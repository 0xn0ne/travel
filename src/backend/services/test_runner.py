"""TestRunnerService — generates all 3 groups (A/B/C) for all scenarios."""

import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.llm.client import LLMClient
from backend.models.database import ItineraryRow, Scenario


class TestRunnerService:
    """Generates blind test data: 4 scenarios × 3 groups = 12 itineraries."""

    def __init__(self, db_session: AsyncSession, llm: LLMClient):
        self.db = db_session
        self.llm = llm

    async def generate_all(self) -> dict:
        """Generate all 3 groups for all scenarios."""
        result = await self.db.execute(select(Scenario))
        scenarios = list(result.scalars().all())

        results = []
        for scenario in scenarios:
            for group in ("A", "B", "C"):
                itinerary = await self._generate_for_group(scenario, group)
                results.append({"scenario": scenario.name, "group": group, "id": itinerary["id"]})

        await self.db.commit()
        return {"generated": len(results), "items": results}

    async def _generate_for_group(self, scenario: Scenario, group: str) -> dict:
        """Generate one itinerary for one scenario+group."""
        from backend.config import get_settings
        from backend.pipeline.coordinator import PipelineCoordinator
        from backend.services.amap_service import AmapService
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        settings = get_settings()
        engine = create_async_engine(settings.database_url, echo=False)
        async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session_maker() as sess:
            coordinator = PipelineCoordinator(sess, self.llm, AmapService(settings.amap_api_key, db_session=sess))
            raw_response, itinerary = await coordinator.run_pipeline_async(
                scenario.user_input, scenario_id=scenario.id, group=group
            )

            itinerary_id = str(uuid.uuid4())
            row = ItineraryRow(
                id=itinerary_id,
                scenario_id=scenario.id,
                group=group,
                city=scenario.city,
                raw_response=raw_response,
                parsed_itinerary=itinerary.model_dump_json(ensure_ascii=False),
                generation_config=json.dumps({"pipeline": "so+ul", "group": group}),
                created_at=datetime.now(),
            )
            sess.add(row)
            await sess.commit()

            return {"id": itinerary_id, "group": group}
