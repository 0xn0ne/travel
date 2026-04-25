---
phase: 12-business-tools
reviewed: 2026-04-21T12:00:00Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - src/backend/agent/__init__.py
  - src/backend/agent/context.py
  - src/backend/agent/loop.py
  - src/backend/api/dependencies.py
  - src/backend/main.py
  - src/backend/services/amap_service.py
  - src/backend/services/city_config.py
  - src/backend/tools/__init__.py
  - src/backend/tools/command_exec.py
  - src/backend/tools/file_io.py
  - src/backend/tools/itinerary_context.py
  - src/backend/tools/search_pois.py
  - src/backend/tools/user_prefs.py
  - src/backend/tools/weather.py
  - src/backend/tools/web_fetch.py
  - src/backend/tools/web_search.py
  - tests/test_agent_context.py
  - tests/test_tools_integration.py
  - data/cities/hangzhou.json
  - data/cities/shanghai.json
findings:
  critical: 2
  warning: 5
  info: 4
  total: 11
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-04-21T12:00:00Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

Phase 12 implements 10 agent tools (4 business + 4 general + 2 file I/O) using the openai-agents SDK with `@function_tool` decorators and `RunContextWrapper[AgentContext]` dependency injection. The overall architecture is sound — tools follow a consistent pattern, return Chinese text to the LLM, and handle errors gracefully.

Two **critical** SSRF vulnerabilities exist in `web_fetch.py`: DNS resolution is not checked again after HTTP redirects, and the pre-fetch DNS check can be bypassed via DNS rebinding. Five **warnings** cover a session-splitting bug in DI wiring, missing parameter validation, and shared mutable class state.

Tests cover construction and wiring (10 tests pass) but do not test any tool execution logic — only that tools register with the SDK Agent.

## Critical Issues

### CR-01: SSRF via Redirect Bypass in web_fetch

**File:** `src/backend/tools/web_fetch.py:89-94`
**Issue:** `_validate_url()` resolves DNS and blocks private IPs **before** the HTTP request, but `follow_redirects=True` is enabled without re-validating redirect targets. An attacker-controlled URL can return a 302 redirect to an internal IP (e.g., `http://169.254.169.254/latest/meta-data/` for cloud metadata). The initial URL passes DNS validation (points to a public IP), but the redirect goes to a private IP unchecked.

**Fix:**
```python
# Option A: Disable redirects entirely
async with httpx.AsyncClient(
    timeout=15.0,
    follow_redirects=False,
) as client:
    response = await client.get(url)
    if response.status_code in (301, 302, 303, 307, 308):
        redirect_url = response.headers.get("location", "")
        await _validate_url(redirect_url)
        # Follow manually after validation
        response = await client.get(redirect_url)
    response.raise_for_status()

# Option B: Use an event hook to validate each redirect
async def validate_redirect(request: httpx.Request):
    await _validate_url(str(request.url))

async with httpx.AsyncClient(
    timeout=15.0,
    follow_redirects=True,
    max_redirects=5,
    event_hooks={"request": [validate_redirect]},
) as client:
    ...
```

### CR-02: SSRF via DNS Rebinding in web_fetch

**File:** `src/backend/tools/web_fetch.py:67-72`
**Issue:** The SSRF check resolves DNS via `socket.getaddrinfo` and validates IPs, but then `httpx.AsyncClient.get()` resolves DNS **again** independently. An attacker with a short-TTL DNS record can:
1. First resolution: returns a public IP (passes validation)
2. Second resolution (by httpx): returns `127.0.0.1` or `10.0.0.1` (bypasses validation)

This is the classic DNS rebinding / TOCTOU attack on SSRF defenses.

**Fix:**
```python
import httpx._transports.default

# After resolving and validating, connect directly to the approved IP
# using a custom transport or by pinning the resolved IP:
async def _fetch_with_pinned_ip(url: str, validated_ip: str, parsed):
    # Replace hostname with IP, set Host header manually
    pinned_url = url.replace(parsed.hostname, validated_ip, 1)
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            pinned_url,
            headers={"Host": parsed.hostname},
        )
        response.raise_for_status()
        return response
```

Alternatively, use a custom DNS resolver that caches the validated IP.

## Warnings

### WR-01: Multiple DB Sessions in get_agent_context DI Chain

**File:** `src/backend/api/dependencies.py:111-123`
**Issue:** `get_agent_context` depends on `get_db`, `get_amap_service` (which also depends on `get_db`), and `get_current_user_optional` (which also depends on `get_db`). FastAPI does not deduplicate `Depends()` calls — each creates a new `AsyncSession`. This means:
- `ctx.context.db_session` (from direct `get_db`) ≠ `amap_service._db_session` (from `get_amap_service`'s `get_db`)
- Cache writes by `AmapService` via its session won't be visible to queries made via the tool's session
- Potential for transactional inconsistency

**Fix:**
```python
def get_agent_context(
    db: AsyncSession = Depends(get_db),
    user: dict | None = Depends(get_current_user_optional),
) -> AgentContext:
    """Create request-scoped AgentContext with shared DB session."""
    settings = get_settings()
    # Reuse the same db session for AmapService
    amap = AmapService(api_key=settings.amap_api_key, db_session=db)
    return AgentContext(
        db_session=db,
        amap_service=amap,
        user_id=user["id"] if user else None,
        settings=settings,
    )
```

### WR-02: Missing `days` Parameter Validation in query_weather

**File:** `src/backend/tools/weather.py:32-33`
**Issue:** The docstring says `days: 查询天数，1-7天，默认3天` but the value is never validated. A value of `days=0`, `days=-1`, or `days=100` would pass through silently. `days=0` produces an empty forecast list; `days=100` just returns all available casts (高德 returns up to 4 days typically), so it won't crash but violates the documented contract.

**Fix:**
```python
@function_tool
async def query_weather(
    ctx: RunContextWrapper[AgentContext],
    city: str,
    days: int = 3,
) -> str:
    days = max(1, min(7, days))  # Clamp to valid range
    ...
```

### WR-03: Shared Mutable Class Variable `_call_count` in AmapService

**File:** `src/backend/services/amap_service.py:35`
**Issue:** `_call_count` is a class variable (`int` is immutable, but the assignment `_call_count += 1` creates a new binding on the class). This means all `AmapService` instances share the same counter. In a web server with multiple requests creating new `AmapService` instances, the counter accumulates across all requests, never resetting. The quota warning threshold becomes meaningless after a few hundred requests.

**Fix:** Use instance-level counter or reset per-request:
```python
class AmapService:
    _call_count: int = 0  # This is fine for MVP — tracks total API usage

    # If per-request tracking is needed:
    def __init__(self, ...):
        self._instance_call_count = 0
```

For MVP this is acceptable as a monitoring metric, but document that it's a global counter.

### WR-04: web_search Module-level Singleton Prevents Testing/Swapping

**File:** `src/backend/tools/web_search.py:68`
**Issue:** `_default_provider = DuckDuckGoSearchProvider()` is a module-level singleton. The `WebSearchProvider` protocol exists for future swapping, but `web_search()` hardcodes `_default_provider`. This means:
- Tests that invoke `web_search` will hit the real DuckDuckGo API
- The DI pattern (via `AgentContext`) is not used for the search provider
- No way to inject a mock provider for testing

**Fix:** Pass the provider through `AgentContext` or allow module-level override:
```python
# In AgentContext:
class AgentContext(BaseModel):
    ...
    web_search_provider: Any = None  # Optional override

# In web_search tool:
@function_tool
async def web_search(ctx: RunContextWrapper[AgentContext], query: str) -> str:
    provider = getattr(ctx.context, 'web_search_provider', None) or _default_provider
    results = await provider.search(query, max_results=5)
```

### WR-05: itinerary_id Not Validated as UUID in get_itinerary_context

**File:** `src/backend/tools/itinerary_context.py:21-22`
**Issue:** The `itinerary_id` parameter is typed as `str` but the database model uses `String(36)` UUID. Any arbitrary string (including SQL-like patterns) is passed directly to the SQLAlchemy query. While SQLAlchemy parameterizes queries (no SQL injection risk), passing invalid UUIDs will silently return "未找到该行程" — not a bug per se, but the error message is misleading. More importantly, if `itinerary_id` contains special characters, it could be used to probe for existence of records.

**Fix:** Add basic UUID format validation:
```python
import uuid

@function_tool
async def get_itinerary_context(
    ctx: RunContextWrapper[AgentContext],
    itinerary_id: str,
) -> str:
    try:
        uuid.UUID(itinerary_id)
    except ValueError:
        return "无效的行程ID格式"
    ...
```

## Info

### IN-01: WebSearchProvider Protocol Defined But Never Used as Type

**File:** `src/backend/tools/web_search.py:22-35`
**Issue:** The `WebSearchProvider` Protocol is defined with a `search()` method signature, but no function parameter or variable is typed as `WebSearchProvider`. The `DuckDuckGoSearchProvider` doesn't explicitly implement it. This is fine as documentation but adds dead code.

**Fix:** Either use it as a type annotation somewhere or add a comment clarifying it's an architectural marker:
```python
# In DuckDuckGoSearchProvider docstring:
class DuckDuckGoSearchProvider:
    """Implements WebSearchProvider protocol for DuckDuckGo."""
```

### IN-02: Test Coverage Gaps — No Tool Execution Tests

**File:** `tests/test_tools_integration.py`
**Issue:** All 10 tests verify construction, registration, and naming — none test actual tool execution (calling a tool with a mock `RunContextWrapper`). This means error handling, output formatting, and edge cases are untested.

**Fix:** Add tests like:
```python
@pytest.mark.asyncio
async def test_query_weather_validates_days():
    ctx = _make_mock_ctx()
    result = await query_weather(ctx, city="上海", days=0)
    # Verify it handles edge case
```

### IN-03: Docstring Says "10 tools" but Plan Says "8 tools"

**File:** `src/backend/tools/__init__.py:12`
**Issue:** The module docstring and `ALL_TOOLS` list contain 10 tools (search_pois, query_weather, get_user_preferences, get_itinerary_context, web_search, web_fetch, list_files, read_file, write_file, execute_command). The plan mentioned 8 tools (BIZ-01~04 + TOOL-01~04). File I/O was split into 3 functions (list/read/write) and command_exec is a stub, giving 10 total. This is fine but worth noting the discrepancy.

**Fix:** Update the docstring comment to reflect 10 tools:
```python
# Line 12: Change from "all 10" — already correct
```

Actually the docstring already says 10 — the plan says 8. No code change needed, just noting the scope expansion is acceptable.

### IN-04: `create_deepseek_model` Returns `Any` Type

**File:** `src/backend/agent/context.py:30-34`
**Issue:** The return type is `Any` instead of the actual `OpenAIChatCompletionsModel` type. This loses type safety for callers. The import is deferred inside the function, so the top-level type hint can't reference it directly.

**Fix:** Use `TYPE_CHECKING` or a type alias:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

def create_deepseek_model(...) -> OpenAIChatCompletionsModel:
    ...
```

---

_Reviewed: 2026-04-21T12:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
