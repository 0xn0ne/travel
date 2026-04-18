# Architecture Research

**Domain:** AI-Powered Travel Itinerary Generation
**Researched:** 2026-04-15
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Vue Frontend (SPA)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Chat UI    │  │ Itinerary UI │  │  Timeline    │             │
│  │  Component   │  │  Component   │  │  Component   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼─────────────────┼─────────────────┼───────────────────────┘
          │                 │                 │
          │ SSE/WebSocket    │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (ASGI)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     SSE Streaming Router                      │  │
│  │  generate / adjust / adjust-confirm / stream / feedback     │  │
│  └──────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  Intent     │  │   Data      │  │ Itinerary   │  │ Validation│  │
│  │ Extraction  │→ │ Pre-filter  │→ │ Generation  │→ │   Layer    │  │
│  │  (LLM)      │  │  (Code)     │  │   (LLM)     │  │ (Map API) │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │
│         │                                                  │        │
│         │ Stage 1         Stage 2      Stage 3        Stage 4       │
│         └──────────────────────────────────────────────────┘        │
│                           4-Stage Pipeline                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Pydantic Validation Layer                 │  │
│  │   IntentOutput | POICandidate | Itinerary | ValidationResult │  │
│  └──────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  SQLite     │  │ DeepSeek-V3 │  │  Amap API   │                  │
│  │  (MVP)      │  │    LLM      │  │  (POI/Routing)│                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Vue Frontend** | User interaction, SSE event handling, itinerary visualization | Vue 3 + Composition API, EventSource API |
| **SSE Router** | Manages streaming responses, stage progress events, connection lifecycle | FastAPI + EventSourceResponse |
| **Intent Extraction (Stage 1)** | Parses natural language → structured travel intent | DeepSeek-V3 API call with ~500 token prompt |
| **Data Pre-filter (Stage 2)** | Queries SQLite POI database, filters by constraints | Pure Python, async SQL query |
| **Itinerary Generation (Stage 3)** | Creates itinerary with SOUL prompt, ~12K tokens | DeepSeek-V3 API call with structured output |
| **Validation Layer (Stage 4)** | Route feasibility check via Amap Walking API | Amap Direction Walking API |
| **POI Database** | Stores Tier A/B/C POIs with taste metadata | SQLite with FTS5 for search |
| **LLM Gateway** | Abstraction over DeepSeek-V3 API, retry/logging | Python async client with httpx |

## Recommended Project Structure

```
src/
├── backend/
│   ├── main.py                 # FastAPI app entry, lifespan events
│   ├── config.py               # Settings (DB path, API keys, LLM config)
│   ├── api/
│   │   ├── routes/
│   │   │   ├── generate.py     # POST /generate → SSE stream
│   │   │   ├── adjust.py       # POST /adjust → SSE stream
│   │   │   ├── confirm.py      # POST /adjust-confirm
│   │   │   ├── stream.py       # GET /stream/{session_id}
│   │   │   └── feedback.py     # POST /feedback
│   │   └── dependencies.py     # Auth, DB session, LLM client
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── stages/
│   │   │   ├── stage1_intent.py      # Intent extraction
│   │   │   ├── stage2_filter.py      # Data pre-filter
│   │   │   ├── stage3_generate.py     # Itinerary generation + SOUL
│   │   │   └── stage4_validate.py     # Route validation
│   │   ├── coordinator.py      # Orchestrates 4-stage pipeline
│   │   └── events.py            # SSE event types, progress tracking
│   ├── llm/
│   │   ├── client.py           # DeepSeek-V3 API client (httpx)
│   │   ├── prompts/
│   │   │   ├── intent_system.txt
│   │   │   ├── intent_user_template.txt
│   │   │   ├── generate_system.txt
│   │   │   ├── generate_user_template.txt
│   │   │   └── examples/        # Few-shot examples per tier
│   │   └── output_parsers.py   # Pydantic model parsers
│   ├── models/
│   │   ├── pydantic.py         # Request/Response models
│   │   └── database.py         # SQLAlchemy/SQLite models
│   ├── services/
│   │   ├── poi_service.py      # POI queries, tier filtering
│   │   ├── taste_service.py    # Taste data lookups
│   │   └── amap_service.py      # Amap API client
│   └── db/
│       ├── init_db.py          # Create tables, seed data
│       └── queries.py           # Reusable SQL queries
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── ItineraryView.vue
│   │   ├── components/
│   │   │   ├── ChatInput.vue
│   │   │   ├── SSEHandler.vue    # EventSource connection management
│   │   │   ├── ItineraryTimeline.vue
│   │   │   ├── POICard.vue
│   │   │   └── AdjustPreview.vue
│   │   ├── stores/
│   │   │   └── itinerary.ts     # Pinia store
│   │   ├── composables/
│   │   │   └── useSSE.ts        # SSE connection + reconnect logic
│   │   └── api/
│   │       └── client.ts        # Axios/fetch wrapper
│   └── package.json
├── data/
│   ├── pois/                    # Cached POI JSON per city
│   └── prompts/                 # SOUL prompt templates
├── tests/
│   ├── unit/
│   │   ├── pipeline/
│   │   │   ├── test_stage1.py
│   │   │   ├── test_stage2.py
│   │   │   ├── test_stage3.py
│   │   │   └── test_coordinator.py
│   │   └── test_parsers.py
│   └── integration/
│       └── test_sse_flow.py
├── scripts/
│   ├── collect_pois.py         # Amap POI collection script
│   ├── annotate_pois.py        # LLM batch annotation
│   └── seed_tier_a.py          # Manual Tier A curation
├── .env.example
├── docker-compose.yml
└── README.md
```

### Structure Rationale

- **`pipeline/stages/`:** Each stage is independently testable. The coordinator chains them but stages have single responsibilities.
- **`llm/prompts/`:** Prompt templates are versioned separately from code. Allows A/B testing of prompts without deployment.
- **`llm/output_parsers.py`:** LLM output parsing is error-prone; centralized parser reduces duplication across stages.
- **`frontend/composables/useSSE.ts`:** SSE connection logic (reconnect, heartbeat, event routing) extracted from view components.
- **`data/pois/`:** Pre-collected POI data lives here, loaded into SQLite at startup.

## Architectural Patterns

### Pattern 1: SSE Streaming with Stage Progress

**What:** Use Server-Sent Events to stream pipeline progress to the frontend, with distinct event types per stage.

**When to use:** Long-running operations (>2s) where users need feedback, particularly LLM calls.

**Trade-offs:** 
- Pros: Simple HTTP-based, works through proxies, automatic reconnection via EventSource
- Cons: Unidirectional only; no client→server messages after initial request

**Example:**
```python
from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent
from collections.abc import AsyncIterable

router = APIRouter()

@router.post("/generate", response_class=EventSourceResponse)
async def generate(request: GenerateRequest) -> AsyncIterable[ServerSentEvent]:
    # Emit stage events as pipeline progresses
    yield ServerSentEvent(data="starting", event="stage", id="1")
    
    # Stage 1: Intent extraction
    intent = await stage1_extract_intent(request.user_input)
    yield ServerSentEvent(data=intent.model_dump_json(), event="intent", id="2")
    yield ServerSentEvent(data="complete", event="stage", id="2")
    
    # Stage 2: Pre-filter
    yield ServerSentEvent(data="running", event="stage", id="3")
    candidates = await stage2_filter_pois(intent, db)
    yield ServerSentEvent(data=f"found {len(candidates)} candidates", event="progress", id="3")
    yield ServerSentEvent(data="complete", event="stage", id="3")
    
    # Stage 3: Generation (longest, stream tokens if possible)
    yield ServerSentEvent(data="running", event="stage", id="4")
    itinerary = await stage3_generate_itinerary(intent, candidates)
    yield ServerSentEvent(data="complete", event="stage", id="4")
    
    # Final result
    yield ServerSentEvent(data=itinerary.model_dump_json(), event="result", id="5")
```

### Pattern 2: Pydantic Output Parsing for LLM Responses

**What:** Define Pydantic models matching expected LLM output structure, use for validation and parsing.

**When to use:** Any structured LLM generation where you need type-safe access to fields.

**Trade-offs:**
- Pros: Validation at boundaries, clear schema documentation, automatic JSON conversion
- Cons: LLM must be prompted to output in matching format; may need retry logic for parse failures

**Example:**
```python
from pydantic import BaseModel, Field
from typing import Literal

class IntentOutput(BaseModel):
    destination: str = Field(description="Extracted city or region")
    days: int = Field(ge=1, le=7)
    traveler_type: Literal["solo", "couple", "friends", "family"]
    interests: list[str] = Field(min_length=1)
    budget_level: Literal["budget", "mid", "premium"]
    avoid: list[str] = Field(default_factory=list)

class POICandidate(BaseModel):
    id: str
    name: str
    tier: Literal["A", "B", "C"]
    duration_minutes: int
    latitude: float
    longitude: float
    taste_tags: list[str]
    highlight_note: str | None = None

# In stage 3
response = await llm_client.generate(prompt, response_format=IntentOutput)
intent: IntentOutput = response.parsed  # Pydantic v2 parsed attribute
```

### Pattern 3: Pipeline Coordinator with Event Bus

**What:** Central coordinator manages stage execution, emits events, handles failures and retries.

**When to use:** Multi-stage pipelines where stages have dependencies and you need centralized error handling.

**Trade-offs:**
- Pros: Clear data flow, easy to add logging/metrics at coordinator level, testable stages
- Cons: Adds indirection; for simple pipelines, direct chaining may be clearer

**Example:**
```python
class PipelineCoordinator:
    def __init__(
        self,
        llm_client: LLMClient,
        db: Database,
        amap_client: AmapClient,
        event_queue: asyncio.Queue[PipelineEvent],
    ):
        self.llm = llm_client
        self.db = db
        self.amap = amap_client
        self.events = event_queue
    
    async def run(self, user_input: str) -> Itinerary:
        # Emit progress via queue (consumed by SSE)
        await self.events.put(PipelineEvent(stage=1, status="running"))
        
        intent = await stage1_extract_intent(user_input, self.llm)
        await self.events.put(PipelineEvent(stage=1, status="complete", data=intent))
        
        await self.events.put(PipelineEvent(stage=2, status="running"))
        candidates = await stage2_filter_pois(intent, self.db)
        await self.events.put(PipelineEvent(stage=2, status="complete", data=candidates))
        
        # Stage 3 may emit multiple progress events
        await self.events.put(PipelineEvent(stage=3, status="running"))
        itinerary = await stage3_generate_itinerary(intent, candidates, self.llm)
        await self.events.put(PipelineEvent(stage=3, status="complete", data=itinerary))
        
        # Validate and potentially retry
        await self.events.put(PipelineEvent(stage=4, status="running"))
        validated = await stage4_validate(itinerary, self.amap)
        await self.events.put(PipelineEvent(stage=4, status="complete", data=validated))
        
        return validated
```

### Pattern 4: Request-Response with Adjustment Confirmation

**What:** For modifications, show preview first, require explicit confirmation before applying.

**When to use:** Any operation that modifies user-generated content (itinerary changes).

**Trade-offs:**
- Pros: Prevents accidental changes, builds trust, allows cancellation
- Cons: Adds latency (2-round-trip vs 1), more complex state management

## Data Flow

### Request Flow (Generate)

```
[User Input: "我想去上海玩3天，喜欢美食和艺术"]
    │
    ▼
[Vue: SSE POST /generate]
    │
    ▼
[SSE Router: Validate request, create session_id]
    │
    ├──────────────────────────────────────────────────────────────┐
    │                    4-Stage Pipeline                           │
    │                                                               │
    ▼                                                               │
[Stage 1: Intent Extraction LLM]                                   │
  Input:  user_input + intent_system_prompt                        │
  Output: IntentOutput { destination, days, interests, ... }        │
  Token: ~500                                                      │
    │                                                               │
    ▼                                                               │
[Stage 2: Data Pre-filter]                                         │
  Input:  IntentOutput + SQLite POI DB                             │
  Output: List[POICandidate] (20-30 items)                        │
  Logic:  Filter by destination, tier balance, user constraints    │
    │                                                               │
    ▼                                                               │
[Stage 3: Itinerary Generation LLM + SOUL]                        │
  Input:  IntentOutput + POICandidates + SOUL_prompt               │
  Output: Itinerary { days[], nodes[], metadata{} }               │
  Token: ~12K                                                      │
    │                                                               │
    ▼                                                               │
[Stage 4: Validation Layer]                                         │
  Input:  Itinerary                                                 │
  Output: ValidatedItinerary | ItineraryWithIssues                 │
  Logic:  Amap Walking API O(N) check between consecutive nodes    │
    │                                                               │
    └──────────────────────────────────────────────────────────────┘
    │
    ▼
[SSE: Emit result event]
    │
    ▼
[Vue: Update itinerary store, render timeline]
```

### Adjustment Flow

```
[User Input: "第二天上午换成博物馆行程"]
    │
    ▼
[SSE POST /adjust with adjustment_instruction]
    │
    ▼
[LLM: Parse adjustment → targeted change spec]
    │
    ▼
[Database: Query alternative POIs matching change]
    │
    ▼
[SSE: Emit preview with original vs changed nodes highlighted]
    │
    ▼
[User clicks "确认" (confirm)]
    │
    ▼
[POST /adjust-confirm with session_id + change_spec]
    │
    ▼
[Backend: Apply change, persist, re-validate]
    │
    ▼
[SSE: Emit updated itinerary]
```

### State Management

```
┌─────────────────────────────────────────────────────┐
│                   Vue Pinia Store                    │
│  itinerary: {                                        │
│    session_id: string,                                │
│    status: 'idle'|'generating'|'complete'|'error',  │
│    intent: IntentOutput | null,                      │
│    days: Day[],                                      │
│    pendingChange: ChangePreview | null,               │
│    feedback: 'positive'|'neutral'|'negative' | null  │
│  }                                                    │
└─────────────────────────────────────────────────────┘
                         │ subscribe
                         ▼
┌─────────────────────────────────────────────────────┐
│              SSE Event Handler (useSSE)              │
│  - Parses incoming ServerSentEvent                  │
│  - Dispatches to appropriate store action           │
│  - Handles reconnection with last-event-id          │
└─────────────────────────────────────────────────────┘
```

### Key Data Flows

1. **Pipeline Progress Flow:** Pipeline stage events → SSE queue → Frontend store → UI progress indicator
2. **Itinerary Result Flow:** Generated itinerary → SSE data event → Store set → Timeline render
3. **Adjustment Preview Flow:** Adjustment request → Preview event → Store pendingChange → Diff UI render
4. **Feedback Flow:** User clicks feedback → POST /feedback → Store update → Future training signal

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 users | Monolith FastAPI + SQLite fine. Single VPS. |
| 100-1K users | Add Redis for SSE pub/sub if multiple workers. Consider connection pooling. |
| 1K-10K users | Move to PostgreSQL, add LLM response caching. Read replicas for POI queries. |
| 10K+ users | Horizontal scaling of FastAPI workers, dedicated LLM inference service, CDN for static assets. |

### Scaling Priorities

1. **First bottleneck: SSE connections.** If using multiple workers, SSE must use Redis pub/sub or similar. Solution: Add Redis before adding many workers.

2. **Second bottleneck: LLM latency.** DeepSeek-V3 is fast but ~30-60s for full pipeline. Solution: Stream partial results, add response caching for identical intents.

3. **Third bottleneck: POI queries.** SQLite fine for <10K POIs, but blocking I/O matters. Solution: Use aiosqlite for async queries.

## Anti-Patterns

### Anti-Pattern 1: Synchronous LLM Calls Blocking Event Loop

**What people do:** Use `requests` or synchronous httpx calls inside async FastAPI route handlers.

**Why it's wrong:** Blocks the event loop, prevents other requests from being processed during LLM wait time (30-60s).

**Do this instead:**
```python
# Bad
def call_llm(prompt):
    response = requests.post(LLM_URL, json={"prompt": prompt})  # Blocks!

# Good
async def call_llm(prompt):
    async with httpx.AsyncClient() as client:
        response = await client.post(LLM_URL, json={"prompt": prompt})  # Yields
```

### Anti-Pattern 2: LLM Output Parsed with `eval()` or String Manipulation

**What people do:** Parse LLM JSON output with `json.loads()` and manual validation.

**Why it's wrong:** No schema enforcement, silent failures on missing fields, security risk if any code execution is involved.

**Do this instead:** Use Pydantic models with `model_validate_json()` or OpenAI-compatible `response_format` parameter that returns parsed objects directly.

### Anti-Pattern 3: Tight Coupling Between Pipeline Stages

**What people do:** Pass internal dicts between stages, access fields like `data["destination"]`.

**Why it's wrong:** Refactoring any stage breaks downstream code, no IDE autocomplete, no type checking.

**Do this instead:**
```python
# Bad
def stage2(data: dict):
    city = data["intent"]["destination"]  # No type safety
    
# Good  
def stage2(intent: IntentOutput, db: Database):
    city = intent.destination  # Type-safe, IDE autocomplete
```

### Anti-Pattern 4: No Retry Logic for External APIs

**What people do:** Single API call to Amap or LLM with no error handling.

**Why it's wrong:** Amap API rate limits or LLM overloaded errors will fail entire request.

**Do this instead:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_llm_with_retry(prompt: str) -> LLMResponse:
    return await llm_client.generate(prompt)
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **DeepSeek-V3** | REST API via httpx | ~500 tokens Stage 1, ~12K tokens Stage 3. Use `response_format` for Pydantic parsing. |
| **Amap POI API** | REST API, async httpx | Free tier 5000 searches/month. Batch requests where possible. |
| **Amap Walking API** | REST API, async httpx | Used in Stage 4 for route validation between nodes. O(N) calls per itinerary. |
| **Vue Frontend** | SSE + REST | SSE for streaming responses, REST for confirmation actions. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **API Route → Pipeline** | Direct async call | Route handler creates pipeline instance, awaits result |
| **Pipeline → LLM Client** | Interface/protocol | Allows swapping DeepSeek with other providers |
| **Pipeline → Database** | SQLAlchemy async session | SQLite via aiosqlite for non-blocking I/O |
| **Pipeline → Amap** | HTTP client | Abstract behind service class for testability |
| **Frontend → Backend** | SSE events + REST | SSE for progress streaming, REST for state-modifying actions |

## Build Order Implications

For roadmap phasing, the architecture suggests this dependency order:

```
Phase 1: Foundation
├── Project structure + config
├── SQLite schema + seed data (minimal)
└── LLM client wrapper (DeepSeek-V3)

Phase 2: Single-Stage Execution
├── Stage 1: Intent extraction (prompt + parser)
├── Stage 2: POI filtering (SQLite query)
└── Stage 3: Itinerary generation (SOUL prompt + parser)

Phase 3: SSE Integration
├── Backend SSE streaming
├── Event types and progress reporting
└── Frontend SSE handler composable

Phase 4: Validation + Adjustments  
├── Stage 4: Amap validation
├── Adjustment flow (preview + confirm)
└── Feedback collection

Phase 5: Polish + Edge Cases
├── Error handling + retry logic
├── Response caching
└── Performance optimization
```

**Critical path:** Stage 3 (generation) is the most complex and likely to need iteration on prompt engineering. Consider Phase 0 (mentioned in constraints) to validate SOUL prompt effectiveness before building full system.

## Sources

- [FastAPI SSE Documentation](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — Official docs on EventSourceResponse
- [Pydantic v2 Documentation](https://docs.pydantic.dev/) — BaseModel, validation, parsing
- [DeepSeek-V3 GitHub](https://github.com/deepseek-ai/DeepSeek-V3) — Model capabilities, API format
- [Amap API Docs](https://lbs.amap.com/api/webservice/summary/) — POI search, direction API
- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html) — Frontend state management

---
*Architecture research for: AI-Powered Travel Itinerary Generation*
*Researched: 2026-04-15*
