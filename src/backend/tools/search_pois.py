"""POI search tool — searches curated DB data and Amap API (BIZ-01).

Per D-25, D-26, D-27, D-36:
- Queries DB first (curated data), falls back to Amap API
- Returns top 10 results with name, rating, tier, coords, highlight_note
- Includes truncation note when results exceed 10
"""

import json

from agents import RunContextWrapper, function_tool
from sqlalchemy import select

from backend.agent.context import AgentContext
from backend.models.database import POI


@function_tool
async def search_pois(
    ctx: RunContextWrapper[AgentContext],
    city: str,
    keyword: str = "",
) -> str:
    """搜索城市中的兴趣点（餐厅、景点、咖啡馆等）。

    Args:
        city: 城市名称，如"上海"、"杭州"
        keyword: 搜索关键词，如"咖啡馆"、"日料"、"博物馆"，可为空
    """
    db_session = ctx.context.db_session
    amap_service = ctx.context.amap_service

    # Build DB query
    stmt = select(POI).where(POI.city == city)
    if keyword:
        stmt = stmt.where(
            (POI.name.contains(keyword)) | (POI.category.contains(keyword))
        )

    result = await db_session.execute(stmt)
    db_pois = result.scalars().all()

    # If keyword provided, also try matching taste_tags in Python (JSON array field)
    if keyword and len(db_pois) < 10:
        # Broader query without keyword filter, then post-filter by taste_tags
        broad_stmt = select(POI).where(POI.city == city)
        broad_result = await db_session.execute(broad_stmt)
        all_pois = broad_result.scalars().all()

        taste_matched = []
        seen_ids = {p.id for p in db_pois}
        for poi in all_pois:
            if poi.id in seen_ids:
                continue
            try:
                tags = json.loads(poi.taste_tags) if poi.taste_tags else []
                if keyword in tags:
                    taste_matched.append(poi)
                    seen_ids.add(poi.id)
            except (json.JSONDecodeError, TypeError):
                pass

        db_pois = list(db_pois) + taste_matched

    # Collect DB results as dict keyed by amap_id
    results_by_id: dict[str, dict] = {}
    for poi in db_pois:
        tier_str = "★" * poi.tier if poi.tier else "★"
        results_by_id[poi.amap_id] = {
            "name": poi.name,
            "tier": tier_str,
            "rating": f"{poi.rating:.1f}" if poi.rating else "暂无",
            "coords": f"{poi.latitude},{poi.longitude}",
            "highlight_note": poi.highlight_note or "",
            "category": poi.category,
            "source": "db",
        }

    # If DB results < 3, expand from Amap API
    if len(results_by_id) < 3:
        try:
            amap_result = await amap_service.search_pois(
                keywords=keyword or city,
                city=city,
            )
            for poi in amap_result.get("pois", []):
                aid = poi.get("amap_id", "")
                if aid and aid not in results_by_id:
                    results_by_id[aid] = {
                        "name": poi.get("name", ""),
                        "tier": "★",
                        "rating": poi.get("rating") or "暂无",
                        "coords": poi.get("location", ""),
                        "highlight_note": "",
                        "category": poi.get("category", ""),
                        "source": "amap",
                    }
        except Exception:
            pass  # Amap API failure is non-fatal for this tool

    # Format results as Chinese text (top 10)
    all_results = list(results_by_id.values())
    total = len(all_results)
    shown = all_results[:10]

    if not shown:
        return f"在 {city} 未找到{('包含「' + keyword + '」的') if keyword else ''}兴趣点。"

    lines = [f"在 {city} 找到以下兴趣点：", ""]
    for i, r in enumerate(shown, 1):
        line = f"{i}. {r['name']} [{r['tier']}]"
        if r["rating"] != "暂无":
            line += f" 评分:{r['rating']}"
        if r["highlight_note"]:
            line += f"\n   ✨ {r['highlight_note']}"
        line += f"\n   坐标: {r['coords']}"
        lines.append(line)

    if total > 10:
        lines.append(f"\n共 {total} 个结果，显示前 10 个")

    return "\n".join(lines)
