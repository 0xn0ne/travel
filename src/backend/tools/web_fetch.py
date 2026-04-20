"""Web fetch tool — reads URL content as text (TOOL-02).

Per D-16, D-17, D-18, D-39:
- Uses httpx.AsyncClient to fetch arbitrary URLs
- SSRF protection: resolves hostname, rejects private IPs
- Extracts text from HTML (regex-based, no BeautifulSoup)
- Truncates content to 3000 chars
"""

import asyncio
import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse

import httpx
from agents import RunContextWrapper, function_tool

from backend.agent.context import AgentContext

logger = logging.getLogger(__name__)

# Max content length per D-17
MAX_CONTENT_CHARS = 3000

# HTML tag stripping regex (simple — no BeautifulSoup dependency for MVP)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _is_private_ip(ip_str: str) -> bool:
    """Check if IP is private/reserved (SSRF protection per D-18).

    Blocks:
    - 10.0.0.0/8 (private)
    - 172.16.0.0/12 (private)
    - 192.168.0.0/16 (private)
    - 127.0.0.0/8 (loopback)
    - ::1 (IPv6 loopback)
    - fc00::/7 (IPv6 unique local)
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_reserved
    except ValueError:
        # Invalid IP string — block by default
        return True


async def _validate_url(url: str) -> None:
    """Resolve hostname and reject private IPs (SSRF protection).

    Performs DNS resolution to get actual IPs and checks each one
    against private/reserved ranges.

    Raises:
        ValueError: If URL scheme is invalid or hostname resolves to private IP.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"不支持的协议: {parsed.scheme}，仅支持 http/https")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL中缺少主机名")

    # Resolve DNS asynchronously — socket.getaddrinfo is blocking
    addr_infos = await asyncio.to_thread(socket.getaddrinfo, hostname, None)
    for family, type_, proto, canonname, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        if _is_private_ip(ip_str):
            raise ValueError(f"安全限制: 该地址解析到内网IP {ip_str}")


@function_tool
async def web_fetch(
    ctx: RunContextWrapper[AgentContext],
    url: str,
) -> str:
    """读取网页内容，获取指定URL的文本信息。

    Args:
        url: 要读取的网页URL
    """
    try:
        # SSRF protection — validate before fetching
        await _validate_url(url)

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        # Decode content — try UTF-8 first, fallback to latin-1
        raw_bytes = response.content
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_bytes.decode("latin-1")

        # Strip HTML tags (simple regex-based extraction)
        text = _HTML_TAG_RE.sub(" ", content)

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate to 3000 chars per D-17
        if len(text) > MAX_CONTENT_CHARS:
            text = text[:MAX_CONTENT_CHARS] + "...(内容已截断)"

        return f"来源: {url}\n\n{text}"

    except ValueError as e:
        # SSRF validation error — return user-friendly message
        logger.warning("URL validation blocked: %s for url=%r", e, url)
        return f"无法访问该网址: {e}"
    except httpx.TimeoutException:
        logger.warning("URL fetch timeout: %s", url)
        return "访问超时，请稍后再试。"
    except httpx.HTTPStatusError as e:
        logger.warning("URL fetch HTTP error: %s -> %s", url, e.response.status_code)
        return f"网页返回错误 (HTTP {e.response.status_code})"
    except Exception as e:
        logger.warning("URL fetch failed: %s for url=%r: %s", type(e).__name__, url, e)
        return f"获取网页内容时出错: {type(e).__name__}"
