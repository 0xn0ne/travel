"""ResultsAnalyzer — analyze blind test results and determine go/no-go verdict."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import TestResult


@dataclass
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    a_count: int
    b_count: int
    c_count: int
    a_rate: float


@dataclass
class BlindTestReport:
    total_responses: int
    aggregated_a_rate: float
    verdict: str  # "PASS" | "RETRY" | "PLAN_B"
    verdict_reason: str
    scenario_results: list[ScenarioResult]
    highlight_note_effect: str  # "SIGNIFICANT" | "MARGINAL" | "NONE"


class ResultsAnalyzer:
    """Analyze blind test results from TestResult table."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    def _determine_verdict(self, a_rate: float) -> tuple[str, str]:
        if a_rate >= 0.60:
            return "PASS", f"SOUL+taste preference rate {a_rate:.1%} ≥ 60% threshold"
        elif a_rate >= 0.40:
            return "RETRY", f"Preference rate {a_rate:.1%} in 40-59% range — retry with improved prompts"
        else:
            return "PLAN_B", f"Preference rate {a_rate:.1%} < 40% — activate Plan B"

    async def analyze(self) -> BlindTestReport:
        """Compute preference rates per scenario and overall, return verdict."""
        result = await self.db.execute(
            select(
                TestResult.scenario_id,
                TestResult.group,
                func.count(TestResult.id).label("count"),
            ).group_by(TestResult.scenario_id, TestResult.group)
        )
        rows = list(result.all())

        scenario_totals: dict[str, dict] = {}
        for scen_id, group, count in rows:
            scenario_totals.setdefault(scen_id, {})[group] = count

        scenario_results = []
        total_a = total_all = 0
        for scen_id, counts in scenario_totals.items():
            a = counts.get("A", 0)
            b = counts.get("B", 0)
            c = counts.get("C", 0)
            total = a + b + c
            if total > 0:
                a_rate = a / total
                scenario_results.append(
                    ScenarioResult(
                        scenario_id=scen_id,
                        scenario_name=scen_id,
                        a_count=a,
                        b_count=b,
                        c_count=c,
                        a_rate=a_rate,
                    )
                )
                total_a += a
                total_all += total

        aggregated_a_rate = total_a / total_all if total_all > 0 else 0.0
        verdict, reason = self._determine_verdict(aggregated_a_rate)

        a_total = sum(s.a_count for s in scenario_results)
        b_total = sum(s.b_count for s in scenario_results)
        if b_total > 0 and a_total > 0:
            ratio = a_total / (a_total + b_total)
            if ratio > 0.7:
                hn_effect = "SIGNIFICANT"
            elif ratio > 0.55:
                hn_effect = "MARGINAL"
            else:
                hn_effect = "NONE"
        else:
            hn_effect = "INSUFFICIENT_DATA"

        return BlindTestReport(
            total_responses=total_all,
            aggregated_a_rate=aggregated_a_rate,
            verdict=verdict,
            verdict_reason=reason,
            scenario_results=scenario_results,
            highlight_note_effect=hn_effect,
        )

    async def compare_ab(self) -> dict:
        """Compare Group A vs Group B to isolate highlight_note effect."""
        result = await self.db.execute(
            select(TestResult.group, func.count(TestResult.id).label("count")).group_by(TestResult.group)
        )
        counts = {row[0]: row[1] for row in result.all()}
        a = counts.get("A", 0)
        b = counts.get("B", 0)
        total = a + b
        a_rate = a / total if total > 0 else 0.0
        return {
            "a_count": a,
            "b_count": b,
            "a_rate": a_rate,
            "highlight_note_effect": ("SIGNIFICANT" if a_rate > 0.7 else "MARGINAL" if a_rate > 0.55 else "NONE"),
        }
