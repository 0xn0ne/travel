"""LLM clients for DeepSeek (streaming + JSON mode + tool calling) and ChatGPT (Group C competitor)."""

from collections.abc import AsyncIterator

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class LLMClient:
    """LLM client via OpenAI-compatible API with streaming, JSON, and tool-calling support.

    Supports three modes:
    - ``stream_chat``: streaming token-by-token response
    - ``generate_json``: non-streaming with optional JSON mode
    - ``tool_chat``: non-streaming tool-calling completion

    The client is model-agnostic — ``base_url`` and ``model`` are configurable
    (currently defaults to DeepSeek-V3, but any OpenAI-compatible endpoint works).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, APITimeoutError)),
    )
    async def stream_chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        """Stream chat completion, yielding content chunks."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, APITimeoutError)),
    )
    async def generate_json(
        self,
        messages: list[dict],
        response_format: dict | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Non-streaming completion with JSON mode support. Use for structured outputs."""
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response_format:
            kwargs["response_format"] = response_format
        response = await self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            msg = response.choices[0].message
            reasoning = getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
            if reasoning:
                content = reasoning
        if content is None:
            finish_reason = response.choices[0].finish_reason
            raise RuntimeError(
                f"LLM returned empty content (finish_reason={finish_reason}). "
                f"Full response: {response.model_dump_json()}"
            )
        return content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, APITimeoutError)),
    )
    async def tool_chat(
        self,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict:
        """Non-streaming tool-calling completion. Returns dict with 'content' and/or 'tool_calls'."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message = response.choices[0].message
        result: dict = {"content": message.content}
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]
        return result


# Backward-compatible alias — existing code importing DeepSeekClient continues to work
DeepSeekClient = LLMClient


class ChatGPTClient:
    """Client for Group C ChatGPT competitor (per D-11). Uses standard OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, APITimeoutError)),
    )
    async def generate_itinerary(self, user_input: str) -> str:
        """Generate itinerary using ChatGPT with same user_input.
        This is the CONTROL group — no SOUL prompt or taste data."""
        system_prompt = (
            "你是一个旅行规划助手，请根据用户的偏好生成一个合理的旅行行程安排，包含每天的景点、时间安排和简要说明。"
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError(f"ChatGPT returned empty content (finish_reason={response.choices[0].finish_reason})")
        return content
