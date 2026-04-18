"""Pydantic-based LLM output parsers with markdown fence stripping."""

import json
import re

from backend.models.pydantic import IntentOutput, Itinerary, ValidationResult


class ParseError(Exception):
    """Raised when LLM output cannot be parsed into expected Pydantic model."""

    def __init__(self, expected_type: str, raw_output: str, detail: str):
        self.expected_type = expected_type
        self.raw_output = raw_output
        self.detail = detail
        super().__init__(f"Failed to parse {expected_type}: {detail}")


def _strip_markdown_fences(raw: str) -> str:
    """Remove ```json ... ``` wrapping if present."""
    if not raw:
        raise ParseError("unknown", "", "LLM returned empty or None content")
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw.strip()


async def parse_intent_output(raw: str) -> IntentOutput:
    """Parse Stage 1 intent extraction output.

    Handles JSON wrapped in markdown code blocks.
    Raises ValueError if multiple cities detected (per INTENT-03).
    """
    cleaned = _strip_markdown_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ParseError("IntentOutput", raw, f"JSON decode error: {e}")

    # Detect multi-city (INTENT-03) — reject with user-friendly message
    city_value = data.get("city", "")
    cities_list = data.get("cities", [])

    if isinstance(city_value, str) and "," in city_value:
        # "上海, 杭州" format
        raise ValueError("暂不支持多城市行程，请选择一个城市")
    elif cities_list and len(cities_list) > 1:
        # ["上海", "杭州"] format
        raise ValueError("暂不支持多城市行程，请选择一个城市")
    elif isinstance(city_value, list) and len(city_value) > 1:
        raise ValueError("暂不支持多城市行程，请选择一个城市")

    try:
        return IntentOutput.model_validate(data)
    except Exception as e:
        raise ParseError("IntentOutput", raw, f"Validation error: {e}")


async def parse_itinerary_output(raw: str) -> Itinerary:
    """Parse Stage 3 itinerary generation output. Handles JSON wrapped in markdown."""
    cleaned = _strip_markdown_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ParseError("Itinerary", raw, f"JSON decode error: {e}")
    try:
        itinerary = Itinerary.model_validate(data)
    except Exception as e:
        raise ParseError("Itinerary", raw, f"Validation error: {e}")

    day_numbers = [d.day_number for d in itinerary.days]
    if day_numbers != list(range(1, len(day_numbers) + 1)):
        raise ParseError("Itinerary", raw, "day_numbers must be sequential starting from 1")
    for day in itinerary.days:
        if len(day.pois) == 0:
            raise ParseError("Itinerary", raw, f"Day {day.day_number} has empty POI list")

    return itinerary


async def parse_validation_output(raw: str) -> ValidationResult:
    """Parse Stage 4 route validation output."""
    cleaned = _strip_markdown_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ParseError("ValidationResult", raw, f"JSON decode error: {e}")
    try:
        return ValidationResult.model_validate(data)
    except Exception as e:
        raise ParseError("ValidationResult", raw, f"Validation error: {e}")
