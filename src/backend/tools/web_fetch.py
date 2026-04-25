"""Web fetch tool — reads URL content as text (TOOL-02).

Per D-16, D-17, D-18, D-39:
- Uses httpx.AsyncClient to fetch arbitrary URLs
- SSRF protection: resolves hostname, rejects private IPs
- DNS rebinding protection: pins resolved IP for actual connection (CR-02)
- Redirect protection: validates each redirect target independently (CR-01)
- Extracts text from HTML (regex-based, no BeautifulSoup)
- Truncates content to 3000 chars
"""

import asyncio
import ipaddress
import logging
import re
import socket
import ssl
from urllib.parse import urlparse, urljoin

import httpx
from agents import RunContextWrapper, function_tool

from backend.agent.context import AgentContext

logger = logging.getLogger(__name__)

# Max content length per D-17
MAX_CONTENT_CHARS = 3000

# Max HTTP redirects to follow
MAX_REDIRECTS = 5

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


async def _resolve_and_validate(url: str) -> tuple[str, str, "tuple"]:
    """Resolve hostname, reject private IPs, return validated IP for pinning.

    Security (CR-02 DNS rebinding protection):
        Resolves DNS and validates ALL returned IPs against private/reserved
        ranges. Returns the first valid public IP so the caller can pin the
        HTTP connection to this exact IP. This eliminates the TOCTOU window
        where an attacker changes DNS between validation and connection.

    Security (CR-01 redirect bypass protection):
        Called for EVERY URL in the redirect chain — not just the initial URL —
        so redirect targets pointing to internal IPs are caught.

    Args:
        url: The URL to validate and resolve.

    Returns:
        Tuple of (validated_ip, hostname, parsed_url).

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

    validated_ip = None
    for family, type_, proto, canonname, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        if _is_private_ip(ip_str):
            raise ValueError(f"安全限制: 该地址解析到内网IP {ip_str}")
        # Pick the first valid public IP for pinning
        if validated_ip is None:
            validated_ip = ip_str

    if validated_ip is None:
        raise ValueError("DNS解析未返回有效地址")

    return validated_ip, hostname, parsed


def _build_pinned_url(parsed, validated_ip: str) -> str:
    """Build URL with hostname replaced by the pre-validated IP.

    Security rationale (CR-02):
        Connecting to the pre-validated IP instead of letting httpx resolve
        DNS independently eliminates the TOCTOU window for DNS rebinding
        attacks. The Host header is set separately to preserve the original
        hostname for the server.
    """
    port = parsed.port
    # IPv6 addresses require brackets in URLs
    if ":" in validated_ip:
        ip_for_url = f"[{validated_ip}]"
    else:
        ip_for_url = validated_ip

    if port:
        netloc = f"{ip_for_url}:{port}"
    else:
        netloc = ip_for_url
    return parsed._replace(netloc=netloc).geturl()


def _make_pinned_ssl_context() -> ssl.SSLContext:
    """SSL context for IP-pinned connections — verifies CA but not hostname.

    Security tradeoff:
        When we pin the connection to a resolved IP, TLS uses the IP as SNI.
        Server certificates are issued for the domain, not the IP, so standard
        hostname verification would fail. We disable hostname checking but keep
        CA chain verification active, meaning:

        - Encryption: present ✓
        - CA verification: required ✓  (attacker needs a trusted-CA cert to MITM)
        - Hostname verification: skipped ✗ (acceptable tradeoff — see below)

        The SSRF risk (reaching internal services via DNS rebinding) is more
        severe than the reduced MITM protection here, because a successful
        MITM still requires a CA-signed certificate AND network-level access.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


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
        # Pre-build SSL context for HTTPS (reused across redirect hops)
        ssl_context = _make_pinned_ssl_context()

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=False,  # CR-01: handle redirects manually with validation
            verify=ssl_context,
        ) as client:
            final_response = None
            current_url = url

            for _ in range(MAX_REDIRECTS + 1):
                # Validate and resolve every URL in the chain (CR-01 + CR-02)
                validated_ip, hostname, parsed = await _resolve_and_validate(
                    current_url
                )

                # Pin connection to pre-validated IP (CR-02 DNS rebinding protection)
                pinned_url = _build_pinned_url(parsed, validated_ip)

                response = await client.get(
                    pinned_url,
                    headers={"Host": hostname},
                )

                # CR-01: manually follow redirects with full validation
                if response.status_code in (301, 302, 303, 307, 308):
                    redirect_location = response.headers.get("location", "")
                    if not redirect_location:
                        # Malformed redirect with no Location — use what we have
                        final_response = response
                        break
                    # Resolve relative redirect URLs against current URL
                    current_url = urljoin(current_url, redirect_location)
                    continue

                final_response = response
                break

            if final_response is None:
                return "重定向次数过多，已停止追踪。"

            final_response.raise_for_status()

            # Decode content — try UTF-8 first, fallback to latin-1
            raw_bytes = final_response.content
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
