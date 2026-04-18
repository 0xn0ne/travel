"""Stage 1: Extract structured user intent from natural language input."""

from pathlib import Path
from typing import TYPE_CHECKING

from backend.llm.output_parsers import parse_intent_output
from backend.models.pydantic import IntentOutput
from backend.services.city_config import get_supported_cities_display, is_city_supported

if TYPE_CHECKING:
    from backend.llm.client import DeepSeekClient


def _load_prompt(filename: str) -> str:
    path = Path(__file__).parent.parent.parent.parent.parent / "data" / "prompts" / filename
    return path.read_text(encoding="utf-8")


async def extract_intent(
    llm_client: "DeepSeekClient",
    user_input: str,
    user_prefs: dict | None = None,
) -> IntentOutput:
    """Extract structured preferences from user text via DeepSeek JSON mode.

    Args:
        user_prefs: Optional user profile preferences with "taste_tags" and "budget".
    """
    system_prompt = _load_prompt("intent_extraction.md")

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if user_prefs:
        hints = []
        if user_prefs.get("taste_tags"):
            tags = "、".join(user_prefs["taste_tags"])
            hints.append(f"该用户的历史偏好标签：{tags}，请在提取interests时优先考虑这些标签。")
        if user_prefs.get("budget"):
            hints.append(f"该用户的预算偏好：{user_prefs['budget']}。")
        if hints:
            messages.append({"role": "system", "content": "\n".join(hints)})

    messages.append({"role": "user", "content": user_input})

    raw = await llm_client.generate_json(
        messages,
        temperature=0.3,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    intent = await parse_intent_output(raw)

    if not is_city_supported(intent.city):
        supported = get_supported_cities_display()
        raise ValueError(f"暂不支持{intent.city}的行程规划，目前支持：{supported}")

    # Per requirements: max 3 days
    if intent.days > 3:
        raise ValueError("行程天数不能超过3天，建议缩减为3天以获得最佳体验")

    return intent
