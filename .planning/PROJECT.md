# 拾途 (Shí Tú)

## What This Is

品味行程生成器——面向 18-35 岁中国年轻旅行者，用人工策展的品味数据 + LLM 叙事能力，生成有温度、有节奏、有惊喜的个性化单城市行程。不是又一个 AI 行程生成器，而是像一个很会玩的本地朋友帮你规划旅行。**v1.0 已交付**——完整四阶段管线、SSE 实时流式生成、对话式行程调整、盲测基础设施、Docker 部署。

## Core Value

"帮你发现你会喜欢但自己找不到的地方，并且用对的方式推荐给你"——品味数据 + SOUL 提示词的组合，让行程有"本地朋友推荐"的温度，而非千篇一律的景点排列。

## Current Milestone: v1.1 Pipeline Quality + UI Redesign

**Goal:** Fix core pipeline to use real Amap POI search (not fixed pool), redesign frontend for excitement and content richness, complete auth flow, add second city, and fix critical technical debt.

**Target features:**
- Wire Amap `search_pois` into Stage 2 for dynamic candidate expansion + enable caching
- Frontend UI overhaul (bright, exciting, "旅途中" feel) using ui-ux-pro-max
- Display highlight_note, vibe_description, data provenance in POI detail
- Fix auth (passlib/bcrypt), add frontend login/register + user settings
- Add second city (杭州 or 成都) with city-config-driven pipeline
- Map visualization (Amap JS API), itinerary sharing
- Auto-seed DB, Alembic migrations, JWT production guard, test runner fixes

## Requirements

### Validated

- ✓ R1: 自然语言输入 → 结构化信息提取 — v1.0
- ✓ R2: 四阶段管线（意图 → 预筛选 → LLM+SOUL → 校验） — v1.0
- ✓ R3: 行程节点含推荐理由，"本地朋友"口吻 — v1.0
- ✓ R4: 实时调整（替换/插入/删除 + 预览确认） — v1.0
- ✓ R7: 品味数据库 taste_tags/recommend/permanent_features/tier/highlight_note — v1.0
- ✓ R9: 数据获取流程（高德采集 + LLM 标注 + 人工精选 Tier A） — v1.0
- ✓ R10: SOUL 提示词按 tier 区分对待 — v1.0
- ✓ R11: 时间轴可视化，节点可点击查看详情 — v1.0
- ✓ R12: 对话式交互输入和调整 — v1.0
- ✓ R13: SSE API 五个端点 — v1.0
- ✓ R14: 变更预览 + 确认后生效 — v1.0
- ✓ R15: 反馈入口"推荐准不准？" — v1.0
- ✓ R16: SOUL 盲测基础设施 — v1.0（工具完成，尚未执行正式测试）

### Active

- [ ] R5: 高德 POI 搜索接入管线（当前仅采集脚本用） — v1.1
- [ ] R6: 全量缓存策略（AmapCache 已建但未启用） — v1.1
- [ ] R8: Tier C 数据缺失（仅 Tier A 12个 + Tier B 85个） — v1.1
- [ ] 第二城市数据（当前仅上海） — v1.1
- [ ] 前端 Auth UI（后端已完成，前端未实现） — v1.1
- [ ] 高德地图可视化（@amap/amap-jsapi-loader 已装未用） — v1.1
- [ ] 用户偏好个性化（taste_tags_default 已存未接入管线） — v1.1
- [ ] Alembic 数据库迁移 — v1.1
- [ ] 前端 UI 重设计（亮色系、旅途中感、POI 详情丰富） — v1.1
- [ ] 行程分享功能 — v1.1
- [ ] 行程列表页 — v1.1
- [ ] 数据来源展示（让用户知道推荐有据可依） — v1.1
- [ ] DB 自动播种 — v1.1
- [ ] Test Runner 修复 — v1.1
- [ ] JWT 生产环境守卫 — v1.1
- [ ] 自动化测试 — v1.2
- [ ] Rate limiting — v1.2

### Out of Scope

- 支付/预订功能 — 非旅行规划核心
- 多语言 — 目标用户为中国用户
- App 端 — Web only，后续可迁移微信小程序
- 多城市/跨城行程 — v1.1 考虑支持第二个城市
- 实时价格比价 — 数据获取困难，非核心
- D2/D4/D5/D6/D8 维度评分 — post-MVP 扩展
- Fine-tuning 模型 — 品味来自数据 + SOUL 提示词
- Offline mode — 需要网络连接

## Context

### 当前系统状态
- **代码量**: 34,789 行 (Python + TypeScript + Vue)
- **技术栈**: FastAPI 0.135 + Vue 3.5 + SQLite + DeepSeek-V3 + 高德地图 API
- **部署**: Docker Compose (backend 319MB + frontend 94.5MB + nginx)
- **POI 数据**: 上海 97 个 (Tier A: 12, Tier B: 85)
- **API 端点**: 16 个（14 测试通过 + 2 auth 修复后通过）
- **前端页面**: 3 个 (Home, Itinerary, BlindTest)

### 已知技术债
- AmapCache 缓存未启用（缺少 db_session）
- Test Runner 有 import 路径 bug
- seed_pois.py 有 lat/lng 参数名 bug
- 内存中 _pending_previews / active_pipelines 无 TTL
- 无结构化日志、无监控、无 HTTPS
- JWT Secret 未配置时使用硬编码回退值

### 目标用户
18-35 岁中国年轻旅行者，期望"像本地朋友推荐一样"的旅行体验，而非标准化的景点百科。期望随性、从容、有意外的旅行节奏。

### 品牌定位
产品名：拾途（shí tú，"拾起旅途"）。核心隐喻：海滩拾贝——自由漫步但挑选美好的贝壳。
品牌人格：不是导游，是懂你的旅行伙伴。
5 个情感关键词：随性、从容、意外、品位、主动。
视觉方向：自然色（沙色/海沫蓝/贝壳粉），温暖色调，手写感，卡片式 UI。

### 关键文档
- 详尽需求文档：`docs/brainstorms/2026-04-15-travel-planning-system-requirements.md`
- 命名推演：`docs/ideation/2026-04-15-travel-planning-naming-ideation.md`
- 语义场：`docs/ideation/2026-04-15-拾途-semantic-field.md`

## Constraints

- **Tech Stack**: Python (FastAPI) + Vue + SQLite — 用户选定，团队熟悉
- **LLM**: DeepSeek-V3 — 成本极低（~¥1/M token），100K+ 上下文窗口
- **Map API**: 高德开放平台为主 — 免费额度 5000 搜索/月，15 万 LBS/月
- **MVP 范围**: 1-2 城市，单城行程，≤3 天，Web only，中文 only
- **数据源合规**: 不爬取大众点评/小红书/B站（合规风险高），以高德 POI + 人工整理为主
- **部署**: 单 VPS + Docker Compose

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + Vue 技术栈 | 团队熟悉，FastAPI 异步适合 SSE，Vue 组件化适合交互密集前端 | ✓ Good — SSE 流式管线稳定运行 |
| SQLite 存储 | MVP 数据量 <1MB（1-2 城市），全量内存加载，无需复杂数据库 | ✓ Good — 需启用 WAL 模式 |
| 品味来自数据而非模型 | 不做 fine-tuning，用 SOUL 提示词 + 结构化品味数据控制输出 | ✓ Good — 生成质量可接受 |
| 3 层 POI 自动化 | 高德 API 自动采集 + LLM 批量标注 + 人工精选 Tier A（~30 分钟/城市） | ✓ Good — Tier C 尚未填充 |
| DeepSeek-V3 | 成本极低（月均 ¥4.3），100K+ 上下文窗口满足需求 | ✓ Good |
| 高德为主数据源 | 免费 5000 次/月搜索额度足够 MVP，覆盖 POI/路线/天气 | ⚠ Revisit — 搜索未接入管线 |
| SSE 进度反馈 | 四阶段管线耗时长（30-60s），需分阶段推送进度管理等待预期 | ✓ Good |
| Phase 0 前置验证 | 产品假设（品味行程 > 标准推荐）必须在开发前验证 | ⚠ Pending — 工具就绪，未执行正式测试 |
| 前端不嵌入地图 | MVP 时间轴展示为主，不含地图组件，减少开发量和 API 调用 | ⚠ Revisit — v1.1 应加地图 |
| SOUL 提示词 + 黄金示例 | 隐性知识难以复制，数据和提示词耦合构成初步壁垒 | ✓ Good |
| bcrypt 直接替代 passlib | passlib 1.7.4 与 bcrypt 4.x 不兼容 | ✓ Good |
| nginx 延迟 DNS 解析 | Docker compose 启动时 backend 未就绪导致 nginx 崩溃 | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-04-16 — v1.1 milestone started*
