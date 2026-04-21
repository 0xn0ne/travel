"""SSE event types and event bus for pipeline progress streaming."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PipelineEvent:
    """Pipeline progress event emitted via SSE to connected frontend clients."""

    stage: str
    status: str
    event_type: str = "stage_update"
    message: str = ""
    data: dict | None = None
    itinerary_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_sse(self) -> str:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DEBUG] to_sse: itinerary_id={self.itinerary_id}")
        payload = json.dumps(
            {
                "event_type": self.event_type,
                "itinerary_id": self.itinerary_id,
                "stage": self.stage,
                "status": self.status,
                "message": self.message,
                "data": self.data,
                "timestamp": self.timestamp,
            },
            ensure_ascii=False,
        )
        return f"data: {payload}\n\n"


class EventBus:
    """Fan-out event bus for SSE. Multiple clients can subscribe."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []
        self.itinerary_id: str | None = None

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue[PipelineEvent | None] = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    async def emit(self, event: PipelineEvent):
        if self.itinerary_id and event.itinerary_id is None:
            event.itinerary_id = self.itinerary_id
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def emit_done(self, q: asyncio.Queue):
        await q.put(None)
