"""POST /api/chat — SSE streaming chat with agent integration (CHAT-01, CHAT-03)."""

import asyncio
import json
import logging
from uuid import uuid4

from agents import Runner
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.context import AgentContext
from backend.api.dependencies import (
    build_agent_instructions,
    get_amap_service,
    get_current_user_optional,
    get_db,
    get_sdk_agent,
)
from backend.config import get_settings
from backend.models.database import ChatMessage
from backend.models.pydantic import ChatRequest
from backend.pipeline.events import EventBus, PipelineEvent
from backend.pipeline.stages.stage_agent import PipelineSSEHooks
from backend.services.amap_service import AmapService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_class=StreamingResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    amap: AmapService = Depends(get_amap_service),
    current_user: dict | None = Depends(get_current_user_optional),
):
    if not request.message or not request.message.strip():
        return _error_stream("请输入你的问题")

    session_id = request.session_id or str(uuid4())
    event_bus = EventBus()
    queue = event_bus.subscribe()

    async def run_chat():
        try:
            messages: list[dict] = []

            if current_user:
                history_result = await db.execute(
                    select(ChatMessage)
                    .where(
                        ChatMessage.user_id == current_user["id"],
                        ChatMessage.session_id == session_id,
                    )
                    .order_by(ChatMessage.created_at.desc())
                    .limit(10)
                )
                history = list(reversed(history_result.scalars().all()))
                messages = [{"role": m.role, "content": m.content} for m in history]

                user_msg = ChatMessage(
                    user_id=current_user["id"],
                    role="user",
                    content=request.message,
                    session_id=session_id,
                )
                db.add(user_msg)
                await db.commit()

            messages.append({"role": "user", "content": request.message})

            instructions = build_agent_instructions(request.message)
            base_agent = get_sdk_agent()
            agent = base_agent.clone(instructions=instructions)

            agent_context = None
            if current_user:
                agent_context = AgentContext(
                    db_session=db,
                    amap_service=amap,
                    user_id=current_user["id"],
                    settings=get_settings(),
                    active_skills=[],
                )

            hooks = PipelineSSEHooks(event_bus)

            await event_bus.emit(
                PipelineEvent(
                    stage="chat",
                    status="thinking",
                    event_type="chat_thinking",
                    message="正在思考...",
                )
            )

            try:
                result = await asyncio.wait_for(
                    Runner.run(
                        starting_agent=agent,
                        input=messages,
                        context=agent_context,
                        max_turns=8,
                        hooks=hooks,
                    ),
                    timeout=30.0,
                )
                final_text = result.final_output or ""

                await event_bus.emit(
                    PipelineEvent(
                        stage="chat",
                        status="completed",
                        event_type="chat_text",
                        message=final_text,
                        data={"text": final_text, "session_id": session_id},
                    )
                )

                if current_user:
                    assistant_msg = ChatMessage(
                        user_id=current_user["id"],
                        role="assistant",
                        content=final_text,
                        session_id=session_id,
                    )
                    db.add(assistant_msg)
                    await db.commit()

            except asyncio.TimeoutError:
                logger.warning("chat agent timed out after 30s")
                await event_bus.emit(
                    PipelineEvent(
                        stage="chat",
                        status="error",
                        event_type="error",
                        message="回复超时，请稍后再试",
                    )
                )
            except Exception as e:
                logger.warning("chat agent failed: %s", e)
                await event_bus.emit(
                    PipelineEvent(
                        stage="chat",
                        status="error",
                        event_type="error",
                        message="暂时无法回复，请稍后再试",
                    )
                )

        except Exception as e:
            logger.exception("chat pipeline error: %s", e)
            await event_bus.emit(
                PipelineEvent(
                    stage="chat",
                    status="error",
                    event_type="error",
                    message="服务暂时不可用",
                )
            )
        finally:
            await event_bus.emit_done(queue)

    async def event_stream():
        task = asyncio.create_task(run_chat())
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
            event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


def _error_stream(message: str):
    async def stream():
        payload = json.dumps(
            {
                "event_type": "error",
                "stage": "chat",
                "status": "error",
                "message": message,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            ensure_ascii=False,
        )
        yield f"data: {payload}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )
