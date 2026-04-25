# Phase 13: Memory & Skills - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in 13-CONTEXT.md — this log preserves the Q&A flow.

**Date:** 2026-04-21
**Phase:** 13-memory-skills
**Mode:** discuss
**Areas discussed:** Memory Strategy, Skill Activation, Skill vs Pipeline, Pre-built Skills

## Discussion Flow

### Memory Read Strategy

**Q: How should the agent read memories?**
- Options: Full dump at session start / Key-pattern search / Both — full + search
- **User response (freeform):** 应该按用户 profile 来搜索记忆信息，不是全盘搜索。没有用户 profile 时自由发挥。记忆应该按维度提取，不是什么都记。助手每 3 轮调用就加载一次记忆（深化记忆）。记忆应该有衰退机制——1 个月或半年后清理低频记忆。
- **Decision:** Profile-scored retrieval + 3-round refresh + quarterly decay

**Q: Memory dimension classification?**
- Options: 4-category / 6-category / LLM自由组织
- **User chose:** 4-category scheme (preference, constraint, feedback, trip_context)

**Q: Memory decay mechanism?**
- Options: 分类 TTL / 统一 30 天 / LRU 排序不清理
- **User response (freeform):** LRU 排序 + 季度全量检查。调用 ≤3 次或尾部 20% 自动清理。季度检查只检查上季度之前创建的记忆，避免刚写入就被清理。
- **Decision:** Quarterly cleanup with age exemption, ≤3 access + bottom 20%

**Q: Profile matching approach?**
- Options: Profile-scored retrieval / Category-filtered / Both
- **User chose:** Profile-scored retrieval

**Q: Memory write control?**
- Options: LLM autonomous / LLM + validation / Event-driven only
- **User chose:** LLM + validation (system validates category dimension)

### Skill Activation Mechanism

**Q: How do skills activate — tool filtering or prompt guidance?**
- Options: LLM decides (all tools on) / Rule-based filtering / Hybrid
- **User chose:** LLM decides (all tools always on) — skills are prompt templates, not tool restrictors

**Q: How does skill matching work?**
- Options: Pipeline intent keywords / Pre-agent keyword matcher / No matching — all in system prompt
- **User chose:** Pipeline intent keywords from Stage 1

**Q: Multi-skill activation handling?**
- Options: Merge all / Single best / Primary + secondary hierarchy
- **User chose:** Primary + secondary hierarchy (primary skill = main prompt, secondaries = brief notes)

### Skill vs Pipeline Overlap

**Q: "行程规划" skill vs existing pipeline relationship?**
- Options: Skill = pipeline enhancement / Skill = chat-only / Skill replaces pipeline stage
- **User chose:** Skill = pipeline enhancement (provides context prompt for Agent Stage, pipeline runs end-to-end)

### Pre-built Skill Definitions

**Q: Are 3 pre-built skills the right set?**
- Options: Yes, 3 skills / Merge to 2 / Add 4th skill
- **User chose:** Yes, 3 skills are right

**Q: Skill config file format?**
- Options: Single JSON per skill / JSON + separate prompt file
- **User chose:** JSON + separate prompt file (metadata in JSON, prompts in markdown)

### Memory + Skill Integration (revisit)

**Q: Does memory influence skill routing or only enriches context?**
- Options: Memory enriches doesn't route / Memory influences routing / Memory is skill-internal only
- **User chose:** Memory enriches, doesn't route — skill activation is keyword-only, memory adds context after activation

---

*Discussion log: 2026-04-21*
