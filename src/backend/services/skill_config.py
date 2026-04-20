"""Skill configuration loader — reads data/skills/*.json files."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "skills"


class TriggerConditions(BaseModel):
    keywords: list[str]
    interests: list[str]
    min_match: int = 1


class SkillConfig(BaseModel):
    name: str
    slug: str
    description: str
    priority: int
    trigger_conditions: TriggerConditions
    prompt_file: str
    related_tools: list[str]


@lru_cache
def _load_all_skills() -> dict[str, SkillConfig]:
    """Load all skill config files from data/skills/*.json."""
    skills: dict[str, SkillConfig] = {}
    for path in SKILLS_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        config = SkillConfig.model_validate(data)
        skills[config.slug] = config
    return skills


def get_all_skills() -> list[SkillConfig]:
    """Get all skills sorted by priority descending (highest first)."""
    return sorted(_load_all_skills().values(), key=lambda s: s.priority, reverse=True)


def get_skill_by_slug(slug: str) -> SkillConfig | None:
    """Get skill config by slug (e.g., 'trip_planning')."""
    return _load_all_skills().get(slug)
