#!/usr/bin/env python3
"""CLI: Generate blind test data for all scenarios and groups."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from config import get_settings
from db.init_db import AsyncSessionFactory, init_db
from llm.client import ChatGPTClient, DeepSeekClient
from services.test_runner import TestRunnerService


async def main():
    await init_db()
    async with AsyncSessionFactory() as sess:
        settings = get_settings()
        llm = DeepSeekClient(settings.deepseek_api_key)
        chatgpt = ChatGPTClient(settings.openai_api_key)
        runner = TestRunnerService(sess, llm, chatgpt)
        result = await runner.generate_all()
        print(f"Generated {result['generated']} itineraries:")
        for item in result["items"]:
            print(f"  {item['scenario']} / {item['group']} -> {item['id']}")


if __name__ == "__main__":
    asyncio.run(main())
