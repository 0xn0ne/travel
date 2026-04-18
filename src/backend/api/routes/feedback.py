"""POST /api/feedback — submit feedback for an itinerary."""

from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.models.database import FeedbackLog
from backend.models.pydantic import FeedbackRequest

router = APIRouter()


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    log = FeedbackLog(
        id=str(uuid4()),
        itinerary_id=request.itinerary_id,
        rating=request.rating,
        comment=request.comment,
    )
    db.add(log)
    await db.commit()
    return {"status": "ok"}
