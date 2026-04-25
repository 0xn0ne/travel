"""Unified result type for all tool invocations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result of a tool invocation.

    All tools return this unified type so the agent loop can handle
    success/error consistently and produce SSE-friendly summaries.

    Attributes:
        data: The actual result payload (any type — dict, list, str, etc.).
        error: Error message if the tool failed, None on success.
        summary: Human-readable Chinese summary for SSE display.
    """

    data: Any = None
    error: str | None = None
    summary: str = ""

    @property
    def success(self) -> bool:
        """Return True if the tool call succeeded (no error)."""
        return self.error is None

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for sending to the LLM as tool result content."""
        if self.error is not None:
            return {"error": self.error, "summary": self.summary}
        return {"data": self.data, "summary": self.summary}
