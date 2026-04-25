from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_amap_service, get_current_user_optional, get_db, get_llm_client
from backend.llm.client import DeepSeekClient
from backend.models.pydantic import CandidatePoiRequest, CandidatePoiResponse, GenerateFromPoisRequest, IntentOutput
from backend.pipeline.coordinator import PipelineCoordinator
from backend.pipeline.events import PipelineEvent
from backend.pipeline.stages.stage1_intent import extract_intent
from backend.pipeline.stages.stage2_filter import filter_pois
from backend.pipeline.stages.stage3_generate import generate_itinerary
from backend.pipeline.stages.stage4_validate import validate_itinerary
from backend.services.amap_service import AmapService
from backend.services.poi_candidate_enricher import enrich_candidates

router = APIRouter()


def _compose_user_input(request: CandidatePoiRequest) -> str:
    parts = [f"目的地：{'、'.join(request.destinations)}"]
    if request.trip_days:
        parts.append(f'行程天数：{request.trip_days}天')
    if request.styles:
        parts.append(f"喜好：{'、'.join(request.styles)}")
    if request.crowd_preference:
        parts.append(f'人流偏好：{request.crowd_preference}')
    if request.budget:
        parts.append(f'预算：{request.budget}')
    if request.extra_info:
        parts.append(f'补充：{request.extra_info}')
    return '；'.join(parts)


@router.post('/poi-candidates', response_model=CandidatePoiResponse)
async def load_poi_candidates(
    request: CandidatePoiRequest,
    db: AsyncSession = Depends(get_db),
    llm: DeepSeekClient = Depends(get_llm_client),
    amap: AmapService = Depends(get_amap_service),
    current_user: dict | None = Depends(get_current_user_optional),
):
    user_input = _compose_user_input(request)
    intent = await extract_intent(llm, user_input, user_prefs=current_user)
    if request.trip_days:
        intent = intent.model_copy(update={'days': min(request.trip_days, 3)})
    candidates = await filter_pois(db, intent, request.group, amap_service=amap, user_prefs=current_user)
    enriched = enrich_candidates(candidates, intent.city)
    return CandidatePoiResponse(city=intent.city, trip_days=intent.days, user_input=user_input, candidates=enriched)


@router.post('/generate-from-pois', response_class=StreamingResponse)
async def generate_from_selected_pois(
    request: GenerateFromPoisRequest,
    db: AsyncSession = Depends(get_db),
    llm: DeepSeekClient = Depends(get_llm_client),
    amap: AmapService = Depends(get_amap_service),
    current_user: dict | None = Depends(get_current_user_optional),
):
    intent = IntentOutput(city=request.city, days=min(request.trip_days, 3))
    coordinator = PipelineCoordinator(db, llm, amap)
    coordinator._user_id = current_user['id'] if current_user else None
    coordinator._user_prefs = current_user
    queue = coordinator.event_bus.subscribe()

    async def run_pipeline():
        try:
            coordinator._intent = intent
            coordinator._scenario_id = request.scenario_id
            coordinator._group = request.group
            selected_candidates = enrich_candidates(request.selected_pois, request.city)
            coordinator._poi_candidates = selected_candidates

            await coordinator.event_bus.emit(PipelineEvent(stage='intent', status='complete', event_type='intent_detected', message=f'已根据所选景点准备{request.city}{intent.days}天行程', data=intent.model_dump()))
            await coordinator.event_bus.emit(PipelineEvent(stage='prefilter', status='complete', event_type='poi_selected', message=f'已锁定{len(selected_candidates)}个已选景点', data={'count': len(selected_candidates)}))
            await coordinator.event_bus.emit(PipelineEvent(stage='generation', status='started', event_type='stage_update', message='正在根据已选景点生成行程...'))

            raw_response, itinerary = await generate_itinerary(llm, intent, selected_candidates, request.user_input, request.group)
            await coordinator._enrich_poi_coordinates(itinerary)

            await coordinator.event_bus.emit(PipelineEvent(stage='generation', status='complete', event_type='stage_update', message='行程初稿完成，正在验证路线...'))
            if amap is not None:
                validation = await validate_itinerary(amap, db, itinerary, selected_candidates)
                await coordinator.event_bus.emit(PipelineEvent(stage='validation', status='complete', event_type='validation_result', message='路线验证完成！', data={'is_valid': validation.is_valid, 'total_walking_minutes': validation.total_walking_minutes}))
            else:
                await coordinator.event_bus.emit(PipelineEvent(stage='validation', status='complete', event_type='validation_result', message='路线验证完成！', data={'is_valid': True, 'note': 'no amap service'}))

            await coordinator._save_to_db(raw_response, itinerary)
            await coordinator.event_bus.emit(PipelineEvent(stage='complete', status='complete', event_type='done', message='行程生成完毕！', data=itinerary.model_dump()))
        except Exception as e:
            await coordinator.event_bus.emit(PipelineEvent(stage='error', status='error', event_type='error', message=str(e)))
        finally:
            await coordinator.event_bus.emit_done(queue)

    async def event_stream():
        task = asyncio.create_task(run_pipeline())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if event is None:
                        break
                    yield event.to_sse()
                    if event.event_type in ('done', 'error'):
                        break
                except asyncio.TimeoutError:
                    yield ': ping\n\n'
        finally:
            if not task.done():
                task.cancel()
            coordinator.event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={'X-Accel-Buffering': 'no', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive'},
    )
