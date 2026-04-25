"""Itinerary context tool — reads current itinerary state (BIZ-04).

Per D-34, D-35, D-41:
- Reads ItineraryRow by ID, parses parsed_itinerary JSON
- Returns day-by-day breakdown with POI details
- Used during itinerary generation/adjustment for agent context
"""

import json

from agents import RunContextWrapper, function_tool
from sqlalchemy import select

from backend.agent.context import AgentContext
from backend.models.database import ItineraryRow


@function_tool
async def get_itinerary_context(
    ctx: RunContextWrapper[AgentContext],
    itinerary_id: str,
) -> str:
    """获取指定行程的详细信息，包括每天的景点安排。

    Args:
        itinerary_id: 行程ID
    """
    db_session = ctx.context.db_session

    # Query itinerary
    result = await db_session.execute(
        select(ItineraryRow).where(ItineraryRow.id == itinerary_id)
    )
    itinerary = result.scalar_one_or_none()

    if not itinerary:
        return "未找到该行程"

    # Parse itinerary JSON
    try:
        parsed = json.loads(itinerary.parsed_itinerary) if itinerary.parsed_itinerary else {}
    except (json.JSONDecodeError, TypeError):
        return f"行程数据解析失败 (ID: {itinerary_id})"

    # Format output
    title = parsed.get("title", "未命名行程")
    lines = [f"📋 行程: {title}", f"📍 城市: {itinerary.city}", ""]

    days = parsed.get("days", [])
    if not days:
        return "\n".join(lines + ["行程暂无具体安排"])

    for day_data in days:
        day_num = day_data.get("day", "?")
        lines.append(f"--- 第 {day_num} 天 ---")

        pois = day_data.get("pois", [])
        if not pois:
            lines.append("  暂无安排")
            continue

        for poi in pois:
            name = poi.get("name", "未知地点")
            time_slot = poi.get("time_slot", "")
            note = poi.get("note", "") or poi.get("brief_note", "")

            entry = f"  • {name}"
            if time_slot:
                entry += f" ({time_slot})"
            if note:
                entry += f"\n    {note}"
            lines.append(entry)

        lines.append("")

    return "\n".join(lines)
