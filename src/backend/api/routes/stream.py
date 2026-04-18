"""GET /api/itinerary/stream — SSE reconnection endpoint for resuming in-progress generations."""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.api.routes.generate import active_pipelines
from backend.models.database import ItineraryRow

router = APIRouter()


@router.get("/itinerary/stream", response_class=StreamingResponse)
async def stream_itinerary(
    itinerary_id: str = Query(..., description="Itinerary ID to reconnect to"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ItineraryRow).where(ItineraryRow.id == itinerary_id))
    row = result.scalar_one_or_none()

    if row is not None and row.parsed_itinerary:
        return _completed_stream(row)

    coordinator = active_pipelines.get(itinerary_id)
    if coordinator is None:
        if row is not None:
            return _incomplete_stream(itinerary_id)
        return _not_found_stream(itinerary_id)

    return StreamingResponse(
        _live_stream(coordinator),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


def _completed_stream(row: ItineraryRow):
    itinerary_data = json.loads(row.parsed_itinerary)

    async def stream():
        yield _sse_event(
            "done",
            "complete",
            "行程生成完毕！",
            {"itinerary_id": row.id, "itinerary": itinerary_data},
        )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


async def _live_stream(coordinator):
    queue = coordinator.event_bus.subscribe()
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
        coordinator.event_bus.unsubscribe(queue)


def _incomplete_stream(itinerary_id: str):
    async def stream():
        yield _sse_event(
            "error",
            "error",
            f"行程 {itinerary_id} 生成未完成，请重新生成",
            {"itinerary_id": itinerary_id},
        )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


def _not_found_stream(itinerary_id: str):
    async def stream():
        yield _sse_event(
            "error",
            "error",
            f"未找到行程 {itinerary_id}",
            {"itinerary_id": itinerary_id},
        )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


def _sse_event(event_type: str, status: str, message: str, data: dict | None) -> str:
    payload = json.dumps(
        {
            "event_type": event_type,
            "itinerary_id": data.get("itinerary_id") if data else None,
            "stage": "complete" if event_type == "done" else "error",
            "status": status,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        },
        ensure_ascii=False,
    )
    return f"data: {payload}\n\n"
