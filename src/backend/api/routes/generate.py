"""POST /api/generate — SSE streaming itinerary generation with input validation."""

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_amap_service, get_current_user_optional, get_db, get_llm_client
from backend.llm.client import DeepSeekClient
from backend.models.pydantic import GenerateRequest
from backend.pipeline.coordinator import PipelineCoordinator
from backend.pipeline.events import PipelineEvent
from backend.services.amap_service import AmapService
from backend.services.city_config import get_supported_cities

router = APIRouter()

active_pipelines: dict[str, PipelineCoordinator] = {}
MAX_DAYS = 3


def _validate_input(request: GenerateRequest) -> str | None:
    if not request.user_input or not request.user_input.strip():
        return "请输入你的旅行需求"
    return None


@router.post("/generate", response_class=StreamingResponse)
async def generate_itinerary(
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    llm: DeepSeekClient = Depends(get_llm_client),
    amap: AmapService = Depends(get_amap_service),
    current_user: dict | None = Depends(get_current_user_optional),
):
    validation_error = _validate_input(request)
    if validation_error:
        return _validation_error_stream(validation_error)

    coordinator = PipelineCoordinator(db, llm, amap)
    coordinator._user_id = current_user["id"] if current_user else None

    # Extract user preferences for pipeline scoring (PIPE-03)
    user_prefs = None
    if current_user:
        import json as _json

        taste_tags_raw = current_user.get("taste_tags_default")
        budget = current_user.get("budget_default")
        taste_tags = []
        if taste_tags_raw:
            try:
                taste_tags = _json.loads(taste_tags_raw) if isinstance(taste_tags_raw, str) else taste_tags_raw
            except (_json.JSONDecodeError, TypeError):
                taste_tags = []
        if taste_tags or budget:
            user_prefs = {"taste_tags": taste_tags, "budget": budget}
    coordinator._user_prefs = user_prefs

    queue = coordinator.event_bus.subscribe()
    active_pipelines[coordinator.itinerary_id] = coordinator

    async def run_pipeline():
        try:
            await coordinator.run_pipeline_async(
                request.user_input,
                scenario_id=request.scenario_id,
                group=request.group,
            )
        except Exception as e:
            await coordinator.event_bus.emit(
                PipelineEvent(stage="error", status="error", event_type="error", message=str(e))
            )
        finally:
            await coordinator.event_bus.emit_done(queue)
            active_pipelines.pop(coordinator.itinerary_id, None)

    async def event_stream():
        task = asyncio.create_task(run_pipeline())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if event is None:
                        break
                    yield event.to_sse()
                    if event.event_type in ("done", "error"):
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if not task.done():
                task.cancel()
            coordinator.event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


def _validation_error_stream(message: str):
    import json
    from datetime import datetime

    payload = json.dumps(
        {
            "event_type": "error",
            "itinerary_id": None,
            "stage": "error",
            "status": "error",
            "message": message,
            "data": None,
            "timestamp": datetime.now().isoformat(),
        },
        ensure_ascii=False,
    )

    async def stream():
        yield f"data: {payload}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )
