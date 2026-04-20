"""Tool system for the agent framework.

Phase 11 legacy (retained during migration):
    - ToolRegistry: YAML-based tool definition loader (retires in Plan 04)
    - ToolResult: Unified result type for tool invocations

Phase 12 SDK tools (added in Plans 02/03):
    - @function_tool decorated async functions using RunContextWrapper[AgentContext]
    - Registered directly with Agent(tools=[...]) — no ToolRegistry needed
"""

from backend.tools.registry import ToolRegistry
from backend.tools.result import ToolResult

__all__ = ["ToolResult", "ToolRegistry"]
