"""POST /api/itinerary/adjust (SSE) + /api/itinerary/adjust/confirm — adjustment endpoints.
PUT /api/itinerary/{itinerary_id} — direct itinerary update (no AI).
"""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_amap_service, get_current_user_optional, get_db, get_llm_client
from backend.llm.client import DeepSeekClient
from backend.models.database import ItineraryRow
from backend.models.pydantic import AdjustmentRequest
from backend.pipeline.coordinator import PipelineCoordinator
from backend.pipeline.events import PipelineEvent
from backend.services.amap_service import AmapService

router = APIRouter()

_pending_previews: dict[str, Any] = {}


@router.post("/itinerary/adjust", response_class=StreamingResponse)
async def adjust_itinerary(
    request: AdjustmentRequest,
    db: AsyncSession = Depends(get_db),
    llm: DeepSeekClient = Depends(get_llm_client),
    amap: AmapService = Depends(get_amap_service),
    current_user: dict | None = Depends(get_current_user_optional),
):
    result = await db.execute(select(ItineraryRow).where(ItineraryRow.id == request.itinerary_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Itinerary not found")

    pending = _pending_previews.get(request.itinerary_id)
    override = None
    if pending and hasattr(pending, "updated_itinerary"):
        override = pending.updated_itinerary

    coordinator = PipelineCoordinator(db, llm, amap)
    coordinator.itinerary_id = request.itinerary_id
    coordinator.event_bus.itinerary_id = request.itinerary_id
    queue = coordinator.event_bus.subscribe()

    async def run_adjust():
        try:
            preview = await coordinator.adjust_pipeline(
                request.itinerary_id,
                request.adjustment_text,
                request.conversation_history or None,
                override_itinerary=override,
            )
            _pending_previews[request.itinerary_id] = preview
        except Exception as e:
            await coordinator.event_bus.emit(
                PipelineEvent(stage="error", status="error", event_type="error", message=str(e))
            )
        finally:
            await coordinator.event_bus.emit_done(queue)

    async def event_stream():
        task = asyncio.create_task(run_adjust())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if event is None:
                        break
                    yield event.to_sse()
                    if event.event_type in ("adjust_done", "adjust_error", "error"):
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


@router.post("/itinerary/adjust/confirm")
async def confirm_adjustment(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    itinerary_id = body.get("itinerary_id")
    confirmed = body.get("confirmed", False)

    if not itinerary_id:
        raise HTTPException(400, "itinerary_id is required")

    if confirmed:
        preview = _pending_previews.get(itinerary_id)
        if not preview:
            raise HTTPException(404, "No pending preview found")

        result = await db.execute(select(ItineraryRow).where(ItineraryRow.id == itinerary_id))
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(404, "Itinerary not found")

        row.parsed_itinerary = preview.updated_itinerary.model_dump_json(ensure_ascii=False)
        await db.commit()

        _pending_previews.pop(itinerary_id, None)
        return {
            "id": row.id,
            "itinerary": preview.updated_itinerary.model_dump(),
        }
    else:
        _pending_previews.pop(itinerary_id, None)
        return {"status": "cancelled"}


class UpdateItineraryBody(BaseModel):
    itinerary: dict


@router.put("/itinerary/{itinerary_id}")
async def update_itinerary(
    itinerary_id: str,
    body: UpdateItineraryBody,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ItineraryRow).where(ItineraryRow.id == itinerary_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Itinerary not found")

    row.parsed_itinerary = json.dumps(body.itinerary, ensure_ascii=False)
    await db.commit()

    return {
        "id": row.id,
        "itinerary": body.itinerary,
    }
