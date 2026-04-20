"""Skill auto-activation matcher — matches user intent against skill trigger conditions."""

from backend.services.skill_config import SKILLS_DIR, SkillConfig, get_all_skills


def match_skills(user_message: str, interests: list[str] | None = None) -> list[SkillConfig]:
    """Match skills against user message keywords and intent interests.

    Per D-19: uses keywords from trigger_conditions against user_message text.
    Per D-21: multiple matches use primary + secondary hierarchy.
    """
    if interests is None:
        interests = []

    matched: list[SkillConfig] = []
    for skill in get_all_skills():
        tc = skill.trigger_conditions
        keyword_hits = sum(1 for kw in tc.keywords if kw in user_message)
        interest_hits = len(set(tc.interests) & set(interests))
        total = keyword_hits + interest_hits
        if total >= tc.min_match:
            matched.append(skill)

    matched.sort(key=lambda s: s.priority, reverse=True)
    return matched


def build_skill_prompt(matched_skills: list[SkillConfig]) -> str:
    """Build combined system prompt from matched skills.

    Per D-20: prompt-only injection, no tool filtering.
    Per D-21: primary skill provides main prompt, secondary skills append brief notes.
    Per D-22: memory enriches skill context but does NOT influence skill routing.
    """
    if not matched_skills:
        return ""

    primary = matched_skills[0]
    prompt_path = SKILLS_DIR / "prompts" / primary.prompt_file
    primary_prompt = prompt_path.read_text(encoding="utf-8").strip()

    if len(matched_skills) == 1:
        return primary_prompt

    secondary_notes = []
    for skill in matched_skills[1:]:
        secondary_notes.append(
            f"{skill.name}方面：{skill.description}，请适当兼顾"
        )

    return f"{primary_prompt}\n\nAdditional guidance: {'。'.join(secondary_notes)}。"
