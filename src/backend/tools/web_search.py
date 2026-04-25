"""Web search tool — DuckDuckGo search as fallback (TOOL-01).

Per D-12, D-13, D-14, D-15, D-38:
- Uses ddgs package (free, no API key) with cn-zh region
- WebSearchProvider protocol for future swap
- Returns top 5 results with title, snippet, URL
- Fallback tool — used when POI DB results are insufficient
"""

import asyncio
import logging
from typing import Protocol

from agents import RunContextWrapper, function_tool
from ddgs import DDGS

from backend.agent.context import AgentContext

logger = logging.getLogger(__name__)


class WebSearchProvider(Protocol):
    """Protocol for web search backends (D-13).

    Allows swapping DuckDuckGo for SerpAPI Baidu or other providers
    without changing tool code.
    """

    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Search the web and return results.

        Returns:
            List of dicts with keys: title, snippet, url
        """
        ...


class DuckDuckGoSearchProvider:
    """DuckDuckGo-based web search provider (D-12, D-14).

    Uses ddgs package — free, no API key required.
    Region set to cn-zh for Chinese-language results.
    """

    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Search DuckDuckGo and return formatted results.

        Args:
            query: Search keywords.
            max_results: Maximum number of results to return.

        Returns:
            List of dicts with title, body (snippet), href (url) keys.
        """
        # DDGS().text() is synchronous — offload to thread
        results = await asyncio.to_thread(
            self._search_sync, query, max_results
        )
        return results

    def _search_sync(self, query: str, max_results: int) -> list[dict]:
        """Synchronous DuckDuckGo search (runs in thread)."""
        with DDGS() as ddgs:
            return list(ddgs.text(query, region="cn-zh", max_results=max_results))


# Module-level default provider instance
_default_provider = DuckDuckGoSearchProvider()


@function_tool
async def web_search(
    ctx: RunContextWrapper[AgentContext],
    query: str,
) -> str:
    """搜索互联网获取信息。当本地POI数据不够时作为补充搜索使用。

    Args:
        query: 搜索关键词，如"上海小众咖啡馆推荐"
    """
    try:
        results = await _default_provider.search(query, max_results=5)

        if not results:
            return "未找到相关结果"

        lines: list[str] = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "无标题")
            snippet = item.get("body", "")
            # Truncate snippet to 200 chars per D-38
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            url = item.get("href", "无链接")
            lines.append(f"{i}. {title}\n   {snippet}\n   链接: {url}")

        return "\n\n".join(lines)

    except Exception as e:
        logger.warning("Web search failed for query=%r: %s", query, e)
        return f"搜索时出错，请稍后再试。（错误: {type(e).__name__}）"
