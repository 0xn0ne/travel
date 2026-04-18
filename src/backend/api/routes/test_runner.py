"""POST /test-runner/generate — trigger blind test data generation."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_chatgpt_client, get_db, get_llm_client
from backend.llm.client import ChatGPTClient, DeepSeekClient
from backend.services.test_runner import TestRunnerService

router = APIRouter()


@router.post("/test-runner/generate")
async def trigger_generation(
    db: AsyncSession = Depends(get_db),
    llm: DeepSeekClient = Depends(get_llm_client),
    chatgpt: ChatGPTClient = Depends(get_chatgpt_client),
):
    runner = TestRunnerService(db, llm, chatgpt)
    result = await runner.generate_all()
    return result


@router.get("/test-runner/status")
async def generation_status():
    return {"status": "ready", "note": "Run POST /test-runner/generate to generate test data"}
