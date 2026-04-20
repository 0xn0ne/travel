---
phase: 14
plan: 02
status: complete
self_check: PASSED
key_files:
  created:
    - tests/test_pipeline_integration.py
  modified:
    - src/backend/pipeline/coordinator.py
    - src/backend/pipeline/stages/stage3_generate.py
    - src/backend/api/routes/generate.py
---

# Plan 14-02: Pipeline Wiring

## What Was Built

Wiring agent enrichment stage into the existing 4-stage pipeline, making it a 5-stage pipeline.

### Core Changes

1. **`PipelineCoordinator`** (`coordinator.py`)
   - Constructor gains optional `agent_context: AgentContext | None = None`
   - `_run_pipeline_async()` calls `agent_enrich()` between `filter_pois()` and `generate_itinerary()`
   - Only runs agent stage when `self._agent_context is not None`
   - Emits `pipeline_stage` events before/after agent enrichment with Chinese messages
   - Passes `enrichment_text` to `generate_itinerary()` via `enrichment_context` kwarg
   - Agent failure is non-blocking — pipeline continues with empty enrichment

2. **`generate_itinerary()`** (`stage3_generate.py`)
   - New parameter: `enrichment_context: str = ""`
   - When non-empty, appends `## 智能推荐补充信息\n{enrichment_context}` to user message
   - This enriches the SOUL prompt with agent-gathered supplementary information

3. **Generate Route** (`api/routes/generate.py`)
   - Imports `AgentContext` and `get_settings`
   - Creates `AgentContext` inline for authenticated users with DB session, AmapService, user_id, settings
   - Passes to coordinator: `coordinator._agent_context = agent_context`
   - Unauthenticated users get no agent enrichment (graceful degradation)

### Tests

8 integration tests in `tests/test_pipeline_integration.py`:
- `test_coordinator_with_agent_context`: Agent stage runs, returns enriched text
- `test_coordinator_without_agent_context`: No agent stage, pipeline runs normally
- `test_coordinator_agent_failure`: Agent failure doesn't break pipeline
- `test_stage3_with_enrichment`: Enrichment text appended to prompt
- `test_stage3_without_enrichment`: No enrichment text, normal prompt
- `test_generate_route_creates_agent_context`: Route creates context for auth user
- `test_pipeline_full_flow`: Full 5-stage pipeline with agent enrichment
- `test_pipeline_sse_events`: Correct SSE events emitted throughout

## Commits

- `89c2c99`: feat(14-02): wire agent enrichment into pipeline

## Deviations

None. Implementation follows plan exactly.
