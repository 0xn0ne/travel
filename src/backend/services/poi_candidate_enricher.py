from __future__ import annotations

import hashlib

from backend.models.pydantic import POICandidate


_DISTRICT_KEYWORDS = {
    '上海': [
        ('浦东新区', ['陆家嘴', '世纪', '迪士尼', '浦东', '张江']),
        ('黄浦区', ['外滩', '豫园', '南京路', '人民广场']),
        ('徐汇区', ['徐汇', '武康', '衡山', '龙华']),
        ('静安区', ['静安', '南京西路', '苏河']),
        ('长宁区', ['长宁', '中山公园', '虹桥']),
    ]
}


def _pick_cover(name: str) -> str:
    seed = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16) % 6
    return f'https://images.unsplash.com/photo-150{seed}000000000?auto=format&fit=crop&w=900&q=80'


def _infer_district(city: str, name: str) -> str:
    for district, keywords in _DISTRICT_KEYWORDS.get(city, []):
        if any(keyword in name for keyword in keywords):
            return district
    return f'{city}热门片区'


def _infer_region_key(city: str, district: str, latitude: float | None, longitude: float | None) -> str:
    if city == '上海' and longitude is not None:
        return 'pudong' if longitude >= 121.52 else 'puxi'
    return district


def _infer_free(category: str, tier: int) -> bool:
    if any(keyword in category for keyword in ['公园', '街区', '古镇', '步道']):
        return True
    return tier >= 2


def _build_description(candidate: POICandidate) -> str:
    tags = '、'.join(candidate.taste_tags[:3]) if candidate.taste_tags else '城市气质'
    return f'{candidate.name}适合偏爱{tags}体验的行程安排，首版为演示文案，后续可替换为真实景点介绍。'


def _build_route(candidate: POICandidate) -> str:
    feature = candidate.highlight_note or '先逛主区域，再留一点自由探索时间'
    return f'推荐玩法：围绕{candidate.name}展开半日游，{feature}。'


def enrich_candidate(candidate: POICandidate, city: str) -> POICandidate:
    district = candidate.district or _infer_district(city, candidate.name)
    region_key = candidate.region_key or _infer_region_key(city, district, candidate.latitude, candidate.longitude)
    is_free = candidate.is_free if candidate.is_free is not None else _infer_free(candidate.category, candidate.tier)
    duration = candidate.suggested_duration_minutes or (180 if candidate.tier == 1 else 120)
    ticket_url = candidate.ticket_url or f'https://example.com/tickets/{candidate.id}'

    return candidate.model_copy(update={
        'district': district,
        'region_key': region_key,
        'cover_image_url': candidate.cover_image_url or _pick_cover(candidate.name),
        'is_free': is_free,
        'ticket_url': ticket_url,
        'description': candidate.description or _build_description(candidate),
        'suggested_route': candidate.suggested_route or _build_route(candidate),
        'suggested_duration_minutes': duration,
    })


def enrich_candidates(candidates: list[POICandidate], city: str) -> list[POICandidate]:
    return [enrich_candidate(candidate, city) for candidate in candidates]
