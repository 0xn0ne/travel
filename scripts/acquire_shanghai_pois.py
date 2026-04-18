#!/usr/bin/env python3
"""Acquire POI data for Shanghai from Amap API.

Usage:
    python scripts/acquire_shanghai_pois.py [--amap-key YOUR_KEY]

This script:
1. Searches Amap for POIs in various taste categories
2. Auto-tiers POIs (rating>4.0 non-chain = Tier B, rest = Tier C)
3. Generates taste_tags for Tier B POIs using LLM
4. Saves to data/pois/shanghai_new.json

Per D-13: ~30 min setup per new city. This script is reusable pattern.
"""

import argparse
import asyncio
import json

# Add src/backend to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from backend.llm.client import DeepSeekClient
from backend.services.amap_service import AmapService

# Taste category keywords to search for (per taste_tags vocabulary)
SHANGHAI_KEYWORDS = [
    # 文艺品位
    "咖啡馆",
    "独立书店",
    "美术馆",
    "展览馆",
    "文创园",
    "老洋房",
    # 美食
    "本帮菜",
    "咖啡厅",
    "网红餐厅",
    "小众美食",
    "老字号",
    # 漫步探索
    "历史街区",
    "老马路",
    "公园",
    "黄浦江",
    # 购物文艺
    "买手店",
    "古着店",
    "设计品牌",
]


async def generate_taste_tags(llm: DeepSeekClient, poi_name: str, category: str) -> list[str]:
    """Generate taste_tags for a Tier B POI using LLM.

    Uses controlled vocabulary: 文艺, 复古, 拍照, 漫步, 情侣, 咖啡,
    小众艺术, 美食, 历史建筑, 夜景, 购物, 亲子, 自然
    """
    vocabulary = [
        "文艺",
        "复古",
        "拍照",
        "漫步",
        "情侣",
        "咖啡",
        "小众艺术",
        "美食",
        "历史建筑",
        "夜景",
        "购物",
        "亲子",
        "自然",
        "打卡",
    ]

    prompt = f"""为以下上海地点生成品味标签（taste_tags）。

地点名称：{poi_name}
类别：{category}

从以下控制词汇中选择3-5个最合适的标签：
{", ".join(vocabulary)}

只返回JSON数组格式，例如：{{"tags": ["文艺", "咖啡", "拍照"]}}

不要添加解释，只返回JSON对象。"""

    result = await llm.generate_json(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(result)
        if isinstance(data, dict) and "tags" in data:
            return data["tags"]
        elif isinstance(data, list):
            return data
    except Exception:
        pass
    return ["文艺"]  # fallback


def is_chain_store(name: str) -> bool:
    """Check if POI is a chain store (should be Tier C regardless of rating)."""
    chain_keywords = ["肯德基", "麦当劳", "星巴克", "必胜客", "海底捞", "华莱士", "德克士"]
    return any(kw in name for kw in chain_keywords)


async def acquire_shanghai_pois(amap_key: str, llm_key: str, dry_run: bool = True):
    """Acquire Shanghai POIs from Amap API."""
    amap = AmapService(api_key=amap_key)
    llm = DeepSeekClient(api_key=llm_key)

    print(f"Searching for Shanghai POIs ({len(SHANGHAI_KEYWORDS)} keywords)...")
    pois = await amap.batch_search_pois(
        city="上海",
        keyword_list=SHANGHAI_KEYWORDS,
        limit_per_keyword=20,
    )
    print(f"Found {len(pois)} unique POIs")

    # Process and tier
    processed = []
    for poi in pois:
        rating = poi.get("rating")
        chain = is_chain_store(poi.get("name", ""))

        # Auto-tier: rating > 4.0 and non-chain = Tier B
        if rating is not None and rating > 4.0 and not chain:
            tier = 2  # Tier B
        else:
            tier = 3  # Tier C

        # Parse location "lng,lat" → separate fields
        location = poi.get("location", "")
        if location:
            parts = location.split(",")
            if len(parts) == 2:
                lng, lat = float(parts[0]), float(parts[1])
            else:
                lng = lat = 0.0
        else:
            lng = lat = 0.0

        processed_poi = {
            "amap_id": poi.get("amap_id", ""),
            "name": poi.get("name", ""),
            "tier": tier,
            "category": poi.get("category", ""),
            "latitude": lat,
            "longitude": lng,
            "address": poi.get("address", ""),
            "taste_tags": [],  # will be filled by LLM for Tier B
            "opening_hours": poi.get("opening_hours", ""),
            "rating": rating,
        }

        # Generate taste_tags for Tier B
        if tier == 2:
            if dry_run:
                print(f"  [DRY RUN] Would generate taste_tags for: {poi['name']}")
            else:
                print(f"  Generating taste_tags for: {poi['name']}")
                tags = await generate_taste_tags(llm, poi["name"], poi.get("category", ""))
                processed_poi["taste_tags"] = tags
                await asyncio.sleep(0.5)  # avoid rate limit

        processed.append(processed_poi)

    await amap.close()

    # Save to JSON
    output_path = Path("data/pois/shanghai_new.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"pois": processed}, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(processed)} POIs to {output_path}")
    print(f"Tier B: {sum(1 for p in processed if p['tier'] == 2)}")
    print(f"Tier C: {sum(1 for p in processed if p['tier'] == 3)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Acquire Shanghai POIs from Amap API")
    parser.add_argument("--amap-key", default="", help="Amap API key")
    parser.add_argument("--llm-key", default="", help="DeepSeek API key")
    parser.add_argument("--dry-run", action="store_true", help="Don't call LLM, just show what would be done")
    args = parser.parse_args()

    # Load from .env if not provided
    from backend.config import get_settings

    settings = get_settings()

    amap_key = args.amap_key or settings.amap_api_key
    llm_key = args.llm_key or settings.deepseek_api_key

    if not amap_key:
        print("Error: Amap API key required. Set AMAP_API_KEY in .env or pass --amap-key")
        exit(1)

    asyncio.run(acquire_shanghai_pois(amap_key, llm_key, dry_run=args.dry_run))
