# Phase 13: Memory & Skills - Context

**Gathered:** 2026-04-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent remembers user preferences across conversations and activates the right skill combinations automatically. Includes: per-user SQLite memory store, skill definition/loading system, skill auto-activation, and 3 pre-built skill packs.

Requirements: MEM-01, MEM-02, MEM-03, SKILL-01, SKILL-02, SKILL-03.

**In scope:**
- `agent_memories` DB table with structured key-value storage
- Memory read/write tools (explicit, LLM-proposed + system-validated)
- Memory profile-scored retrieval and 3-round refresh cycle
- Quarterly memory cleanup with age-exemption
- Skill config loader from `data/skills/` JSON files
- Skill auto-activation via Stage 1 intent keywords
- 3 pre-built skills: 行程规划, 美食探索, 本地人推荐

**Out of scope:**
- Pipeline integration (Phase 14)
- Chat UI (Phase 15)
- Multi-agent orchestration (v1.3)
- User-created custom skills
- Memory summarization / cross-trip learning (v1.3)

</domain>

<decisions>
## Implementation Decisions

### Memory Storage (MEM-01)

- **D-01:** New `agent_memories` SQLAlchemy model with fields: `id` (UUID), `user_id` (FK to users, indexed), `key` (string, indexed), `value` (JSON text), `category` (string: preference/constraint/feedback/trip_context), `access_count` (integer, default 1), `created_at`, `updated_at`, `last_accessed_at`. Composite index on `(user_id, category)`.
- **D-02:** Alembic migration for `agent_memories` table creation.
- **D-03:** 4-category dimension scheme:
  - `preference` — 饮食偏好, 出行节奏, 住宿偏好, 活动偏好
  - `constraint` — 忌口, 预算限制, 时间限制, 人群限制
  - `feedback` — 用户对推荐的评价/反馈
  - `trip_context` — 当前行程相关临时记忆 (city, dates, POIs explored)

### Memory Read (MEM-02)

- **D-04:** `read_memories(ctx, category=None, limit=20)` tool — returns memories scored by user profile relevance (taste_tags + budget alignment). When `category` is provided, filters to that category. Sorts by profile match score descending.
- **D-05:** Profile-scored retrieval: each memory's `value` JSON is compared against user's `taste_tags_default` and `budget_default` — memories with overlapping tags score higher. New users (no profile) get memories sorted by recency.
- **D-06:** 3-round refresh cycle: during ongoing agent conversation, every 3 tool-call rounds the agent should reload memories (call `read_memories()` again). This "deepens" memory context as conversation progresses.
- **D-07:** If `user_id` is None (unauthenticated), `read_memories()` returns empty list — no persistent memory for anonymous users (MEM-03).

### Memory Write (MEM-02)

- **D-08:** `write_memory(ctx, key, value, category)` tool — LLM decides when to write, but system validates the `category` parameter against the 4 allowed dimensions. Rejects writes with invalid categories.
- **D-09:** `value` must be a JSON-serializable dict with at least a `note` field. Example: `{"note": "用户偏好安静的小众咖啡馆", "tags": ["咖啡", "安静", "小众"]}`.
- **D-10:** On write, if a memory with same `user_id` + `key` already exists, update `value` and increment `access_count` instead of creating duplicate.
- **D-11:** Writes increment `access_count` and update `last_accessed_at` and `updated_at`.

### Memory Decay (MEM-01 continued)

- **D-12:** Quarterly cleanup job (not real-time TTL). Runs as a background task or management command.
- **D-13:** Cleanup rules:
  - Only examines memories created **before the current quarter** (new memories are exempt — e.g., a memory created on March 10 won't be touched during the March quarterly check)
  - Removes memories with `access_count <= 3` in their lifetime
  - Additionally removes bottom 20% lowest-access-count memories (after the ≤3 rule)
  - `trip_context` category memories expire after 7 days regardless (temporary by nature)
- **D-14:** Cleanup does NOT require a separate tool — it's an administrative function (could be a CLI command or scheduled task, not an agent tool).

### Skill Definition (SKILL-01)

- **D-15:** Each skill is defined by a JSON config file in `data/skills/` (e.g., `data/skills/trip_planning.json`) + a separate prompt markdown file in `data/skills/prompts/` (e.g., `data/skills/prompts/trip_planning.md`).
- **D-16:** Skill JSON schema:
  ```json
  {
    "name": "行程规划",
    "slug": "trip_planning",
    "description": "规划城市行程，包括景点选择、路线安排、时间分配",
    "priority": 10,
    "trigger_conditions": {
      "keywords": ["规划", "行程", "安排", "天", "日", "路线"],
      "interests": ["景点", "规划"],
      "min_match": 1
    },
    "prompt_file": "trip_planning.md",
    "related_tools": ["search_pois", "query_weather", "get_user_preferences", "write_memory"]
  }
  ```
- **D-17:** Skill loader follows `city_config.py` pattern: Pydantic `SkillConfig` model, `@lru_cache` loader, glob `data/skills/*.json`.
- **D-18:** `related_tools` field is informational only — it guides prompt content, not tool filtering. All tools remain available to the agent at all times.

### Skill Activation (SKILL-02)

- **D-19:** Skill activation uses Stage 1 intent keywords — the `intent_extraction` stage already outputs `interests` and other structured fields. These are matched against skill `trigger_conditions`.
- **D-20:** Activation is **prompt-only** — no tool filtering. The matched skill's prompt template is injected into the agent's system message to guide behavior. All `ALL_TOOLS` remain available.
- **D-21:** Multi-skill activation: when multiple skills match, use **primary + secondary hierarchy**. Primary skill (highest `priority` score) provides the main system prompt. Secondary skills append brief behavioral notes (1-2 sentences each).
- **D-22:** Memory enriches skill context but does NOT influence skill routing. Skill matching is strictly based on intent keywords. After activation, relevant user memories are loaded into the skill's prompt context.

### Pre-built Skills (SKILL-03)

- **D-23:** Three pre-built skills:

  **行程规划 (trip_planning)**
  - Priority: 10 (highest)
  - Trigger: keywords ["规划", "行程", "安排", "路线"], interests ["景点", "规划"]
  - Guides agent to: search POIs, check weather, read preferences, plan day-by-day itinerary, write trip_context memory
  - Role: Pipeline enhancement (Phase 14 Agent Stage context prompt)

  **美食探索 (food_exploration)**
  - Priority: 5
  - Trigger: keywords ["吃", "美食", "餐厅", "小吃", "咖啡", "茶"], interests ["美食", "品尝"]
  - Guides agent to: search food POIs, web search for blog reviews, read preference memories
  - Role: Chat + pipeline enrichment

  **本地人推荐 (local_insider)**
  - Priority: 3
  - Trigger: keywords ["小众", "本地人", "隐藏", "推荐", "地道"], interests ["探索", "文化"]
  - Guides agent to: search off-tier POIs, web search + web fetch for local blog content, read preference memories
  - Role: Chat + pipeline enrichment

### Skill vs Pipeline Boundary

- **D-24:** Skills are pipeline **enhancements**, not replacements. The existing 4-stage pipeline runs end-to-end. Skills provide context prompts for the Agent Stage (Phase 14) that enriches data between Stage 2 (pre-filter) and Stage 3 (LLM+SOUL).
- **D-25:** Skills also function in free-form chat (Phase 15) — the same skill config + prompt injection works for both pipeline and chat contexts.

### Agent's Discretion

- Exact profile scoring algorithm (how taste_tags match memory values)
- Memory value JSON schema details beyond `note` field
- Quarterly cleanup implementation (CLI command vs background task)
- Prompt file content for each skill (tone, instructions, examples)
- How "3-round refresh" is tracked (counter in AgentContext? tool-call tracking?)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Memory Architecture
- `.planning/REQUIREMENTS.md` §MEM-01, MEM-02, MEM-03 — Memory requirements
- `src/backend/models/database.py` — Existing table patterns (UUID PKs, JSON text, timestamps)
- `src/backend/agent/context.py` — AgentContext model (extend with memory service if needed)
- `src/backend/tools/file_io.py` — Existing file-based memory sandbox (separate from DB memory)
- `src/backend/api/dependencies.py` — `get_agent_context()`, `get_sdk_agent()` DI wiring

### Skill System
- `.planning/REQUIREMENTS.md` §SKILL-01, SKILL-02, SKILL-03 — Skill requirements
- `src/backend/services/city_config.py` — Pattern to replicate for skill loading (Pydantic + lru_cache + glob)
- `data/cities/hangzhou.json` — Example JSON config structure
- `src/backend/tools/__init__.py` — ALL_TOOLS list (skills don't filter this)
- `src/backend/api/dependencies.py` — `get_sdk_agent()` where skill prompt injection happens

### Pipeline Context (Phase 14 boundary)
- `.planning/ROADMAP.md` §Phase 14 — Pipeline integration description
- `src/backend/pipeline/coordinator.py` — 4-stage pipeline, where Agent Stage inserts
- `src/backend/pipeline/stages/stage1_intent.py` — Intent extraction output format (used for skill matching)

### Prior Phase Decisions
- `.planning/phases/12-business-tools/12-CONTEXT.md` — SDK migration, AgentContext, ALL_TOOLS, DI patterns
- `.planning/phases/11-agent-framework-core/11-CONTEXT.md` — AgentLoop, SSE events, max_turns=8

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **city_config.py pattern**: Pydantic model + `@lru_cache` + glob loading — perfect template for `skill_config.py`
- **AgentContext** (context.py): Already has `db_session`, `user_id` — memory tools access DB directly via `ctx.context.db_session`
- **ALL_TOOLS** (tools/__init__.py): 10 `@function_tool` functions — skills reference these but don't filter them
- **file_io.py sandbox**: Separate file-based storage under `data/agent_memory/` — DB memory is a different system, no conflict
- **AmapService**: Tools already wrap it (search_pois, query_weather) — skills guide usage, not implementation

### Established Patterns
- **Tool pattern**: `@function_tool` + `RunContextWrapper[AgentContext]` first param, returns `str`
- **DI pattern**: `@lru_cache` singletons for registries, request-scoped for DB-dependent services
- **Config loading**: JSON files in `data/`, Pydantic validation, `@lru_cache`
- **Prompt loading**: `Path(__file__).parent... / "data" / "prompts" / filename` with `.read_text(encoding="utf-8")`

### Integration Points
- **`get_sdk_agent()`** in `dependencies.py` — where skill prompt gets injected into Agent's `instructions` parameter
- **Stage 1 output** in pipeline — `intent.interests` feeds skill matching (Phase 14 integration)
- **`agent_memories` table** — new model in `database.py`, new Alembic migration
- **`data/skills/`** directory — new, follows `data/cities/` pattern

</code_context>

<specifics>
## Specific Ideas

- Memory should feel natural — agent remembers what a "很会玩的本地朋友" would remember about you
- "行程规划" skill's prompt should guide the agent to think about pacing, variety, surprises — not just list POIs
- "本地人推荐" should prioritize off-the-beaten-path places, not tourist traps
- Skills are personality templates — same tools, different behavior and focus
- Memory categories help keep things organized but shouldn't be visible to users — they just experience a smarter agent

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-memory-skills*
*Context gathered: 2026-04-21*
