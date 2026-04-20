# Phase 12: Business & General Tools — Research

**Date:** 2026-04-20
**Status:** Complete

## Standard Stack Additions

| Technology | Version | Purpose |
|------------|---------|---------|
| `openai-agents-python` | >=0.14.2 | Agent SDK — Runner, Agent, @function_tool, RunContextWrapper |
| `ddgs` | latest | DuckDuckGo web search (free, no API key, Chinese region support) |

## Architecture Patterns

### SDK Migration Pattern
- `Agent(name, tools=[...], instructions=..., model=OpenAIChatCompletionsModel(...))` replaces hand-rolled AgentLoop
- `@function_tool` decorator auto-extracts JSON schema from type hints + docstrings
- `Runner.run(starting_agent, input, context=agent_context, max_turns=8, run_config=...)` replaces tool-call loop
- `Runner.run_streamed()` for streaming (SSE bridge deferred to Phase 14)
- `RunContextWrapper[TContext]` provides DI into tools — `ctx.context` holds `AgentContext`

### Tool DI Pattern
```python
from agents import function_tool, RunContextWrapper

@function_tool
async def search_pois(
    ctx: RunContextWrapper[AgentContext],
    city: str,
    keyword: str = "",
) -> str:
    """Search POIs by city and keyword."""
    amap = ctx.context.amap_service
    ...
```

### Context Model
```python
class AgentContext(BaseModel):
    db_session: Any  # AsyncSession (not Pydantic-serializable)
    amap_service: AmapService
    user_id: str | None = None
    settings: Any  # Settings
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

## Don't Hand-Roll

- Tool-call loop → SDK `Runner.run()` handles tool dispatch, retries, max_turns
- Tool JSON schema generation → SDK `@function_tool` auto-extracts from signatures
- Tool registration → SDK `Agent(tools=[...])` replaces ToolRegistry

## Common Pitfalls

1. **ChatCompletions vs Responses API:** DeepSeek only supports ChatCompletions. Must call `set_default_openai_api("chat_completions")` at startup.
2. **Hosted tools don't work:** `WebSearchTool`, `FileSearchTool` etc. require Responses API — build ourselves.
3. **高德 weather city param:** Requires **adcode** (e.g., "310000" for Shanghai), NOT city name. Need city→adcode lookup via district API or config.
4. **SSRF protection:** Web fetch must block private IP ranges (10.x, 172.16-31.x, 192.168.x, localhost).
5. **File I/O sandbox:** Must resolve to absolute path and verify it starts with `data/agent_memory/` root — prevent `../` traversal.
6. **parsed_itinerary is JSON string:** ItineraryRow.parsed_itinerary needs `json.loads()` before accessing.
7. **taste_tags_default is JSON string:** User.taste_tags_default needs `json.loads()` before accessing.

## Validation Architecture

### Tool Behavioral Tests
Each tool should have:
1. Happy path test with mocked dependencies
2. Error handling test (service failure, invalid input)
3. Auth boundary test (user_id=None for user_prefs)

### Integration Validation
- SDK Agent can call each registered tool
- AgentContext DI wires correctly through FastAPI
- Runner respects max_turns=8

## Security Considerations

- **Web fetch SSRF:** Validate resolved IPs against private ranges using `ipaddress` module
- **File I/O path traversal:** `Path.resolve()` + `Path.is_relative_to()` (Python 3.9+)
- **User data isolation:** Tools only access data for authenticated user_id
