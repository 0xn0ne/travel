"""4-stage pipeline orchestration with SSE event emission and wired stage implementations."""

import asyncio
from typing import TYPE_CHECKING
from uuid import uuid4

import sqlalchemy
from backend.models.database import POI
from backend.models.pydantic import POICandidate
from backend.pipeline.events import EventBus, PipelineEvent

if TYPE_CHECKING:
    from backend.llm.client import LLMClient
    from backend.models.pydantic import Itinerary
    from backend.services.amap_service import AmapService


class PipelineCoordinator:
    """Orchestrates the 5-stage itinerary generation pipeline."""

    def __init__(self, db_session, llm_client: "LLMClient", amap_service: "AmapService" = None, agent_context=None):
        self.db = db_session
        self.llm = llm_client
        self.amap = amap_service
        self._agent_context = agent_context
        self._poi_candidates: list[POICandidate] | None = None
        self._intent = None
        self._scenario_id: str | None = None
        self._group: str | None = None
        self._user_id: str | None = None
        self._user_prefs: dict | None = None
        self.itinerary_id = str(uuid4())
        self.event_bus = EventBus()
        self.event_bus.itinerary_id = self.itinerary_id

    def run_pipeline(self, user_input: str, scenario_id: str | None = None, group: str | None = None):
        return asyncio.run(self._run_pipeline_async(user_input, scenario_id, group))

    async def run_pipeline_async(self, user_input: str, scenario_id: str | None = None, group: str | None = None):
        return await self._run_pipeline_async(user_input, scenario_id, group)

    async def _run_pipeline_async(self, user_input: str, scenario_id: str | None, group: str | None):
        from backend.pipeline.stages.stage1_intent import extract_intent
        from backend.pipeline.stages.stage2_filter import filter_pois
        from backend.pipeline.stages.stage3_generate import generate_itinerary
        from backend.pipeline.stages.stage4_validate import validate_itinerary

        self._scenario_id = scenario_id
        self._group = group

        await self.event_bus.emit(
            PipelineEvent(
                stage="intent",
                status="started",
                event_type="stage_update",
                message="正在理解你的需求...",
            )
        )
        try:
            intent = await extract_intent(self.llm, user_input, user_prefs=self._user_prefs)
        except ValueError as e:
            await self.event_bus.emit(PipelineEvent(stage="intent", status="error", event_type="error", message=str(e)))
            raise

        self._intent = intent
        city = intent.city
        days = intent.days
        await self.event_bus.emit(
            PipelineEvent(
                stage="intent",
                status="complete",
                event_type="intent_detected",
                message=f"了解！你想要{city}{days}天的行程",
                data=intent.model_dump(),
            )
        )

        await self.event_bus.emit(
            PipelineEvent(
                stage="prefilter",
                status="started",
                event_type="stage_update",
                message="正在筛选适合你的地点...",
            )
        )
        poi_candidates = await filter_pois(
            self.db,
            intent,
            group,
            amap_service=self.amap,
            user_prefs=self._user_prefs,
        )
        self._poi_candidates = poi_candidates
        await self.event_bus.emit(
            PipelineEvent(
                stage="prefilter",
                status="complete",
                event_type="poi_selected",
                message=f"找到了{len(poi_candidates)}个候选地点",
                data={"count": len(poi_candidates)},
            )
        )

        enrichment_text = ""
        if self._agent_context is not None:
            from backend.pipeline.stages.stage_agent import agent_enrich

            await self.event_bus.emit(
                PipelineEvent(
                    stage="agent",
                    status="started",
                    event_type="pipeline_stage",
                    message="开始智能推荐...",
                )
            )
            enrichment_text = await agent_enrich(
                llm_client=self.llm,
                intent=self._intent,
                poi_candidates=poi_candidates,
                user_input=user_input,
                event_bus=self.event_bus,
                agent_context=self._agent_context,
            )
            await self.event_bus.emit(
                PipelineEvent(
                    stage="agent",
                    status="completed",
                    event_type="pipeline_stage",
                    message="智能推荐完成",
                )
            )

        await self.event_bus.emit(
            PipelineEvent(
                stage="generation",
                status="started",
                event_type="stage_update",
                message="正在为你生成个性化行程...",
            )
        )
        raw_response, itinerary = await generate_itinerary(
            self.llm, intent, poi_candidates, user_input, group,
            enrichment_context=enrichment_text,
        )

        # Enrich POI coordinates from database
        await self._enrich_poi_coordinates(itinerary)

        await self.event_bus.emit(
            PipelineEvent(
                stage="generation",
                status="complete",
                event_type="stage_update",
                message="行程初稿完成，正在验证路线...",
            )
        )

        if self.amap is not None:
            await self.event_bus.emit(
                PipelineEvent(
                    stage="validation",
                    status="started",
                    event_type="validation_progress",
                    message="正在验证步行路线...",
                )
            )
            validation = await validate_itinerary(self.amap, self.db, itinerary, poi_candidates)
            await self.event_bus.emit(
                PipelineEvent(
                    stage="validation",
                    status="complete",
                    event_type="validation_result",
                    message="路线验证完成！",
                    data={
                        "is_valid": validation.is_valid,
                        "total_walking_minutes": validation.total_walking_minutes,
                    },
                )
            )
        else:
            await self.event_bus.emit(
                PipelineEvent(
                    stage="validation",
                    status="complete",
                    event_type="validation_result",
                    message="路线验证完成！",
                    data={"is_valid": True, "note": "no amap service"},
                )
            )

        await self._save_to_db(raw_response, itinerary)

        await self.event_bus.emit(
            PipelineEvent(
                stage="complete",
                status="complete",
                event_type="done",
                message="行程生成完毕！",
                data=itinerary.model_dump(),
            )
        )
        return raw_response, itinerary

    async def _enrich_poi_coordinates(self, itinerary: "Itinerary"):
        """Fill in latitude/longitude for each POI from the database."""
        from backend.models.database import POI

        poi_ids = []
        for day in itinerary.days:
            for poi in day.pois:
                if poi.poi_id:
                    poi_ids.append(poi.poi_id)

        if not poi_ids:
            return

        # Query all POI coordinates in one batch
        stmt = sqlalchemy.select(POI.id, POI.latitude, POI.longitude).where(POI.id.in_(poi_ids))
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        rows = result.fetchall()
        coord_map = {row[0]: (row[1], row[2]) for row in rows}

        # Fill in coordinates
        for day in itinerary.days:
            for poi in day.pois:
                if poi.poi_id and poi.poi_id in coord_map:
                    poi.latitude, poi.longitude = coord_map[poi.poi_id]

    async def _save_to_db(self, raw_response: str, itinerary):
        """Save itinerary to DB before emitting done event."""
        import logging

        from backend.models.database import ItineraryRow

        logger = logging.getLogger(__name__)
        city = self._intent.city if self._intent else "未知"
        logger.info(f"[DEBUG] Saving itinerary {self.itinerary_id} to DB, city={city}")
        try:
            row = ItineraryRow(
                id=self.itinerary_id,
                user_id=self._user_id,
                scenario_id=self._scenario_id or None,
                group=self._group or None,
                city=city,
                raw_response=raw_response,
                parsed_itinerary=itinerary.model_dump_json(ensure_ascii=False),
                generation_config="{}",
            )
            self.db.add(row)
            await self.db.commit()
            logger.info(f"[DEBUG] Itinerary {self.itinerary_id} saved to DB successfully")
        except Exception as e:
            logger.error(f"[DEBUG] Failed to save itinerary {self.itinerary_id}: {e}")
            raise

    async def adjust_pipeline(
        self,
        itinerary_id: str,
        adjustment_text: str,
        conversation_history: list[dict] | None = None,
        override_itinerary: "Itinerary | None" = None,
    ):
        import json
        from pathlib import Path

        from sqlalchemy import select

        from backend.llm.output_parsers import _strip_markdown_fences
        from backend.models.database import ItineraryRow
        from backend.models.pydantic import AdjustmentPreview, IntentOutput, Itinerary
        from backend.pipeline.stages.stage2_filter import filter_pois
        from backend.pipeline.stages.stage4_validate import validate_itinerary

        await self.event_bus.emit(
            PipelineEvent(
                stage="adjust",
                status="started",
                event_type="adjust_started",
                message="正在理解你的调整需求...",
            )
        )

        try:
            result = await self.db.execute(select(ItineraryRow).where(ItineraryRow.id == itinerary_id))
            row = result.scalar_one_or_none()
            if not row:
                raise ValueError(f"行程 {itinerary_id} 不存在")

            if override_itinerary is not None:
                existing = override_itinerary
            else:
                existing = Itinerary.model_validate_json(row.parsed_itinerary)

            await self.event_bus.emit(
                PipelineEvent(
                    stage="adjust",
                    status="started",
                    event_type="adjust_progress",
                    message="正在分析调整意图...",
                )
            )

            synthetic_intent = IntentOutput(city=row.city, days=len(existing.days))
            poi_candidates = await filter_pois(
                self.db,
                synthetic_intent,
                amap_service=self.amap,
                user_prefs=self._user_prefs,
            )

            def _fmt_poi(p):
                tier_label = {1: "A", 2: "B", 3: "C"}.get(p.tier, "?")
                tags = " | ".join(p.taste_tags)
                hl = f"\n  推荐理由：{p.highlight_note}" if p.highlight_note else ""
                return f"【{p.name}】\n  ID: {p.id}\n  等级：Tier {tier_label}\n  分类：{p.category} | 标签：{tags}{hl}"

            poi_pool_str = "\n\n".join(_fmt_poi(p) for p in poi_candidates)

            prompt_path = Path(__file__).parent.parent.parent.parent / "data" / "prompts" / "soul_adjust.md"
            soul_adjust = prompt_path.read_text(encoding="utf-8")

            itinerary_json = existing.model_dump_json(ensure_ascii=False, indent=2)

            messages = [{"role": "system", "content": soul_adjust}]
            if conversation_history:
                messages.extend(conversation_history)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"## 当前行程\n{itinerary_json}\n\n"
                        f"## 调整请求\n{adjustment_text}\n\n"
                        f"## 候选POI池\n{poi_pool_str}"
                    ),
                }
            )

            await self.event_bus.emit(
                PipelineEvent(
                    stage="adjust",
                    status="started",
                    event_type="adjust_progress",
                    message="正在生成调整方案...",
                )
            )

            raw = await self.llm.generate_json(
                messages,
                temperature=0.5,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )

            cleaned = _strip_markdown_fences(raw)
            parsed = json.loads(cleaned)
            preview = AdjustmentPreview.model_validate(parsed)

            await self.event_bus.emit(
                PipelineEvent(
                    stage="adjust",
                    status="started",
                    event_type="adjust_progress",
                    message="正在验证调整后的路线...",
                )
            )

            if self.amap is not None:
                validation = await validate_itinerary(self.amap, self.db, preview.updated_itinerary, poi_candidates)
                await self.event_bus.emit(
                    PipelineEvent(
                        stage="adjust",
                        status="complete",
                        event_type="adjust_progress",
                        message="路线验证完成",
                        data={
                            "is_valid": validation.is_valid,
                            "total_walking_minutes": validation.total_walking_minutes,
                        },
                    )
                )

            await self.event_bus.emit(
                PipelineEvent(
                    stage="adjust",
                    status="complete",
                    event_type="adjust_preview",
                    message="调整预览已生成",
                    data=preview.model_dump(),
                )
            )

            await self.event_bus.emit(
                PipelineEvent(
                    stage="adjust",
                    status="complete",
                    event_type="adjust_done",
                    message="行程调整完成",
                )
            )

            return preview

        except Exception as e:
            await self.event_bus.emit(
                PipelineEvent(
                    stage="adjust",
                    status="error",
                    event_type="adjust_error",
                    message=str(e),
                )
            )
            raise
