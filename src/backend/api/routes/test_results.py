"""POST /api/test-results — submit blind test preference. GET /api/test-results/summary — analysis results."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.models.database import TestResult

router = APIRouter()


class TestResultCreate(BaseModel):
    scenario_id: str
    participant_id: str
    group: str
    preferred_itinerary_id: str
    preference_reason: str | None = None


@router.post("/test-results")
async def submit_test_result(result: TestResultCreate, db: AsyncSession = Depends(get_db)):
    row = TestResult(**result.model_dump())
    db.add(row)
    await db.commit()
    return {"status": "ok"}


@router.get("/test-results/summary")
async def test_results_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TestResult.group, func.count(TestResult.id).label("count")).group_by(TestResult.group)
    )
    rows = result.all()
    return {row[0]: row[1] for row in rows}


@router.get("/test-results/analysis")
async def get_analysis(db: AsyncSession = Depends(get_db)):
    from backend.services.results_analyzer import ResultsAnalyzer

    analyzer = ResultsAnalyzer(db)
    report = await analyzer.analyze()
    return {
        "total_responses": report.total_responses,
        "aggregated_a_rate": report.aggregated_a_rate,
        "verdict": report.verdict,
        "verdict_reason": report.verdict_reason,
        "highlight_note_effect": report.highlight_note_effect,
        "scenarios": [{"scenario_id": s.scenario_id, "a_rate": s.a_rate} for s in report.scenario_results],
    }
