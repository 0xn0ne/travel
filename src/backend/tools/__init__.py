"""Tool system for the agent framework.

Phase 11 legacy (retained during migration):
    - ToolRegistry: YAML-based tool definition loader
    - ToolResult: Unified result type for tool invocations

Phase 12 SDK tools (added in Plans 02/03):
    - @function_tool decorated async functions using RunContextWrapper[AgentContext]
    - Registered directly with Agent(tools=[...]) — no ToolRegistry needed

Centralized exports (Plan 04):
    - ALL_TOOLS: list of all 10 @function_tool functions for SDK Agent construction
"""

from backend.tools.registry import ToolRegistry
from backend.tools.result import ToolResult

from backend.tools.search_pois import search_pois
from backend.tools.weather import query_weather
from backend.tools.user_prefs import get_user_preferences
from backend.tools.itinerary_context import get_itinerary_context
from backend.tools.web_search import web_search
from backend.tools.web_fetch import web_fetch
from backend.tools.file_io import list_files, read_file, write_file
from backend.tools.command_exec import execute_command
from backend.tools.memory import read_memories, write_memory

ALL_TOOLS = [
    search_pois,
    query_weather,
    get_user_preferences,
    get_itinerary_context,
    web_search,
    web_fetch,
    list_files,
    read_file,
    write_file,
    execute_command,
    read_memories,
    write_memory,
]

__all__ = ["ToolResult", "ToolRegistry", "ALL_TOOLS"]
