"""User preferences tool — reads user taste and budget preferences (BIZ-03).

Per D-31, D-32, D-33, D-40:
- Reads taste_tags_default (JSON string) and budget_default from User model
- Reads last 3 itinerary summaries for context
- Read-only — no mutation
- Returns structured data for LLM to incorporate into recommendations
"""

import json

from agents import RunContextWrapper, function_tool
from sqlalchemy import select

from backend.agent.context import AgentContext
from backend.models.database import ItineraryRow, User


@function_tool
async def get_user_preferences(
    ctx: RunContextWrapper[AgentContext],
) -> str:
    """获取当前用户的口味偏好、预算设置和历史行程概要。无需参数。"""
    user_id = ctx.context.user_id
    if not user_id:
        return "用户未登录，无法获取偏好信息"

    db_session = ctx.context.db_session

    # Query user
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return "未找到用户信息"

    # Parse taste tags
    try:
        taste_tags = json.loads(user.taste_tags_default) if user.taste_tags_default else []
    except (json.JSONDecodeError, TypeError):
        taste_tags = []

    budget = user.budget_default or "适中"

    # Query last 3 itineraries
    itin_result = await db_session.execute(
        select(ItineraryRow)
        .where(ItineraryRow.user_id == user_id)
        .order_by(ItineraryRow.created_at.desc())
        .limit(3)
    )
    itineraries = itin_result.scalars().all()

    # Format output
    lines = ["用户偏好："]

    # Taste tags
    if taste_tags:
        tags_str = "、".join(taste_tags)
        lines.append(f"- 口味标签：{tags_str}")
    else:
        lines.append("- 口味标签：暂无设置")

    lines.append(f"- 预算：{budget}")

    # Recent itineraries
    if itineraries:
        lines.append("- 近期行程：")
        for i, itin in enumerate(itineraries, 1):
            date_str = itin.created_at.strftime("%Y-%m-%d") if itin.created_at else "未知日期"
            lines.append(f"  {i}. {itin.city} ({date_str})")
    else:
        lines.append("- 近期行程：暂无")

    return "\n".join(lines)
