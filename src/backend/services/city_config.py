"""City configuration loader — reads data/cities/*.json files."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

CITIES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cities"


class CityCenter(BaseModel):
    lat: float
    lng: float


class CityBounds(BaseModel):
    northeast: CityCenter
    southwest: CityCenter


class CityConfig(BaseModel):
    name: str
    name_en: str
    center: CityCenter
    bounds: CityBounds
    supported_interests: list[str]
    amap_city_code: str
    adcode: str  # 行政区划代码，用于天气 API (e.g., "330100" for 杭州, "310000" for 上海)
    tier_a_count: int
    poi_data_file: str


@lru_cache
def _load_all_cities() -> dict[str, CityConfig]:
    """Load all city config files from data/cities/*.json."""
    cities: dict[str, CityConfig] = {}
    for path in CITIES_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        config = CityConfig.model_validate(data)
        cities[config.name] = config
    return cities


def get_city_config(city: str) -> CityConfig | None:
    """Get config for a specific city by name (e.g., '上海')."""
    return _load_all_cities().get(city)


def get_supported_cities() -> set[str]:
    """Get set of all supported city names."""
    return set(_load_all_cities().keys())


def is_city_supported(city: str) -> bool:
    """Check if a city is supported."""
    return city in _load_all_cities()


def get_supported_cities_display() -> str:
    """Get display string of supported cities for error messages."""
    return "、".join(sorted(_load_all_cities().keys()))
