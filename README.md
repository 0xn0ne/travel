# 拾途 (Shí Tú) — 品味行程生成器

> 面向 18-35 岁中国年轻旅行者的 AI 行程规划工具，用"本地朋友推荐"的温度帮你发现会喜欢但自己找不到的地方。

## 项目简介

拾途是一个基于 AI 的旅行行程生成器，核心特点：
- **品味数据 + LLM 叙事**：不是千篇一律的景点排列，而是有温度、有节奏、有惊喜的个性化行程
- **SSE 流式输出**：实时展示行程生成过程，体验如与朋友聊天的流畅感
- **高德地图集成**：POI 位置可视化，路线规划更直观
- **AI Agent 工具调用**：行程生成过程中 agent 自动调用 POI 搜索、天气查询、网络搜索等工具

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI 0.135.3 | 异步框架，内置 SSE 支持 |
| 前端框架 | Vue 3.5.32 | Composition API + TypeScript |
| 构建工具 | Vite 8.0.8 | 高速 HMR |
| UI 组件库 | Naive UI 2.44.1 | 面向中文市场 |
| 状态管理 | Pinia 3.0.4 | Vue 官方推荐 |
| 数据库 | SQLite (SQLAlchemy 异步) | 单文件，MVP 最佳 |
| LLM | OpenAI 兼容 API (DeepSeek-V3) | Streaming + 函数调用 |
| 地图服务 | 高德开放平台 | POI 搜索 + 路径规划 |
| Agent SDK | openai-agents 0.14+ | SDK Agent 架构 |

## 快速开始

### 前置要求

- **Docker** + **Docker Compose** (推荐)
- 或 **Python 3.12+** + **Node.js 22+** + **npm**

### Docker Compose 部署 (推荐)

```bash
# 1. 克隆项目
git clone <repo-url>
cd travel

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 3. 构建并启动
docker compose up -d --build

# 4. 访问应用
# 前端:      http://localhost
# 后端 API:  http://localhost:8000
# API 文档:  http://localhost:8000/docs
```

### 本地运行

#### 后端

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -e .

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 PROVIDER_API_KEY 和 AMAP_API_KEY

# 4. 启动服务（自动初始化数据库）
uvicorn backend.main:app --reload --port 8000
```

#### 前端

```bash
cd src/frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 环境变量配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `PROVIDER_API_KEY` | ✅ | — | LLM Provider API Key |
| `PROVIDER_BASE_URL` | — | `https://api.deepseek.com` | API Base URL |
| `PROVIDER_MODEL` | — | `deepseek-chat` | 模型名称 |
| `AMAP_API_KEY` | ✅ | — | 高德开放平台 Key (POI + 天气) |
| `JWT_SECRET_KEY` | ✅* | `dev-only-...` | JWT 密钥（生产必须替换） |
| `ENVIRONMENT` | — | `development` | `development` / `production` |
| `DATABASE_URL` | — | `sqlite+aiosqlite:///./data/travel.db` | 数据库连接串 |
| `CORS_ORIGINS` | — | 见 .env.example | 允许的跨域来源列表 |

> `ENVIRONMENT=production` 时必须设置真实的 `JWT_SECRET_KEY`，否则启动拒绝。

获取 API Keys：
- **LLM Provider**: [DeepSeek 平台](https://platform.deepseek.com/) / [OpenAI](https://platform.openai.com/)
- **高德开放平台**: [lbs.amap.com](https://lbs.amap.com/)

## 项目结构

```
travel/
├── src/
│   ├── backend/                    # FastAPI 后端
│   │   ├── api/
│   │   │   ├── routes/            # API 路由 (按功能模块)
│   │   │   │   ├── auth.py         # 认证: register, login, logout, me, profile
│   │   │   │   ├── generate.py     # 行程生成 (SSE 流式)
│   │   │   │   ├── chat.py         # AI 聊天 (SSE 流式)
│   │   │   │   ├── itineraries.py  # 行程列表 / 详情 / meta
│   │   │   │   ├── adjust.py       # 行程调整 (SSE + confirm)
│   │   │   │   ├── scenarios.py    # 测试场景管理
│   │   │   │   ├── feedback.py     # 用户反馈
│   │   │   │   ├── config.py       # 公开配置 (amap-key)
│   │   │   │   ├── stream.py       # SSE 重连恢复
│   │   │   │   ├── test_results.py # 盲测结果提交 / 统计
│   │   │   │   ├── test_runner.py  # 盲测数据批量生成
│   │   │   │   └── __init__.py     # 路由注册汇总
│   │   │   ├── dependencies.py     # FastAPI 依赖注入 (DB session, Agent, LLM)
│   │   │   └── auth.py            # JWT 工具函数
│   │   ├── db/
│   │   │   ├── init_db.py         # 数据库初始化 + Alembic 迁移
│   │   │   └── seed_pois.py       # 从 JSON 文件种子 POI 数据
│   │   ├── agent/
│   │   │   ├── context.py          # AgentContext (请求作用域 DI)
│   │   │   ├── loop.py            # Legacy AgentLoop (保留，Phase 12 过渡)
│   │   │   └── __init__.py        # init_agent_sdk() 入口
│   │   ├── pipeline/
│   │   │   ├── coordinator.py      # 5阶段流水线协调器
│   │   │   ├── events.py          # EventBus + PipelineEvent (SSE 事件)
│   │   │   └── stages/
│   │   │       ├── stage1_intent.py    # 意图提取
│   │   │       ├── stage2_filter.py     # POI 筛选
│   │   │       ├── stage3_generate.py  # 行程生成
│   │   │       ├── stage4_validate.py   # 路线验证
│   │   │       └── stage_agent.py       # Agent 智能补充阶段
│   │   ├── llm/
│   │   │   └── client.py          # LLMClient (流式 / JSON / 工具调用)
│   │   ├── models/
│   │   │   ├── database.py        # SQLAlchemy ORM 模型
│   │   │   └── pydantic.py        # Pydantic 请求/响应/内部 Schema
│   │   ├── services/
│   │   │   ├── amap_service.py    # 高德 API 封装 (POI 搜索 / 天气 / 路径)
│   │   │   ├── city_config.py    # 城市配置加载器
│   │   │   ├── skill_config.py    # Skill 配置加载器
│   │   │   ├── skill_matcher.py   # Skill 激活匹配器
│   │   │   ├── memory_cleanup.py  # 记忆季度清理服务
│   │   │   └── results_analyzer.py # 盲测结果分析器
│   │   ├── tools/                 # SDK @function_tool 工具函数
│   │   │   ├── memory.py         # 记忆读写工具
│   │   │   ├── search_pois.py    # POI 搜索工具
│   │   │   ├── weather.py         # 天气查询工具
│   │   │   ├── user_prefs.py      # 用户偏好读取工具
│   │   │   ├── itinerary_context.py # 行程上下文读取工具
│   │   │   ├── web_search.py      # 网络搜索工具 (DuckDuckGo)
│   │   │   ├── web_fetch.py       # 网页抓取工具 (带 SSRF 防护)
│   │   │   ├── file_io.py         # 文件读写工具 (沙箱限制)
│   │   │   └── command_exec.py    # 命令执行桩 (默认禁用)
│   │   ├── config.py             # pydantic-settings 配置
│   │   └── main.py              # FastAPI 应用入口 + lifespan
│   │
│   └── frontend/                  # Vue 3 前端
│       ├── src/
│       │   ├── api/             # axios API 客户端
│       │   ├── components/       # UI 组件
│       │   │   ├── ChatBubble.vue # 浮动聊天气泡 (AI Chat)
│       │   │   └── ...
│       │   ├── composables/      # 组合式函数 (useSSE, useChat)
│       │   ├── stores/           # Pinia 状态管理
│       │   ├── views/            # 页面视图
│       │   ├── router/            # Vue Router 配置
│       │   └── types/            # TypeScript 类型
│       └── package.json
│
├── data/                         # 运行时数据
│   ├── cities/                   # 城市配置 (adcode 等)
│   │   ├── hangzhou.json
│   │   └── shanghai.json
│   ├── pois/                     # POI 种子数据
│   │   ├── hangzhou.json
│   │   └── shanghai.json
│   ├── prompts/                  # SOUL 提示词模板
│   │   ├── soul_system.md
│   │   ├── soul_user_template.md
│   │   ├── soul_adjust.md
│   │   └── ...
│   ├── skills/                   # Agent Skill 配置
│   │   ├── 行程规划.json
│   │   ├── 美食探索.json
│   │   └── 本地人推荐.json
│   └── agent_memory/              # Agent 文件记忆沙箱 (按 user_id 分隔)
│       └── {user_id}/
│
├── tests/                        # pytest 测试套件
│   ├── test_*.py                  # 单元测试
│   └── test_*_integration.py     # 集成测试
│
├── scripts/                       # 辅助脚本
│   ├── acquire_shanghai_pois.py  # 高德 POI 数据采集
│   └── generate_test_data.py     # 盲测数据生成
│
├── alembic/                       # 数据库迁移
│   ├── versions/                  # 迁移版本文件
│   └── env.py
│
├── docker-compose.yml             # Docker 编排
├── Dockerfile.backend             # 后端镜像
├── Dockerfile.frontend            # 前端镜像 (Node → Nginx)
├── nginx.conf                     # Nginx 配置 (API 代理 + 前端SPA)
├── pyproject.toml                 # Python 依赖
└── README.md
```

---

## API 参考文档

### 认证方式

除 `/api/auth/register` 和 `/api/auth/login` 外，所有需要认证的接口通过 **JWT Bearer Token** 传递：

```
Authorization: Bearer <access_token>
```

注册/登录成功后返回 `access_token`，客户端自行保存（建议存 `localStorage`），在后续请求的 `Authorization` header 中携带。

---

### 认证 (Auth)

#### `POST /api/auth/register` — 用户注册

**认证**: 不需要

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "minlength:6"
}
```

**响应** `200`:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "01751fd9-3e3a-41cf-8a06-3a3c9d4f0fef",
    "email": "user@example.com"
  }
}
```

**错误**: `400` — Email 已注册

---

#### `POST /api/auth/login` — 用户登录

**认证**: 不需要

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "Test123!"
}
```

**响应** `200`: 同 register

**错误**: `401` — 邮箱或密码错误

---

#### `POST /api/auth/logout` — 登出

**认证**: 需要

**请求体**: 无

**响应** `200`:
```json
{"message": "Logged out successfully"}
```

> 客户端需自行删除本地存储的 token。

---

#### `GET /api/auth/me` — 获取当前用户信息

**认证**: 需要

**响应** `200`:
```json
{
  "id": "01751fd9-3e3a-41cf-8a06-3a3c9d4f0fef",
  "email": "user@example.com",
  "taste_tags_default": "[]",
  "budget_default": "适中"
}
```

---

#### `PUT /api/auth/profile` — 更新用户偏好

**认证**: 需要

**请求体**:
```json
{
  "taste_tags_default": "[\"咖啡\", \"小众\", \"历史建筑\"]",
  "budget_default": "适中"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `taste_tags_default` | string (JSON array) | 品味标签，如 `["咖啡", "小众"]` |
| `budget_default` | string | 预算档位：`"经济"` / `"适中"` / `"宽裕"` |

**响应** `200`: 返回更新后的用户信息（同 `/me` 格式）

**错误**: `400` — 无效的 JSON 或 budget 不在允许值中

---

### 行程生成 (Generate)

#### `POST /api/generate` — 生成行程 (SSE 流式)

**认证**: 可选（登录用户获得更好的个性化推荐）

**请求体** `GenerateRequest`:
```json
{
  "user_input": "我想去上海过周末，想喝咖啡和逛老建筑",
  "scenario_id": null,
  "group": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_input` | string | ✅ | 用户的自然语言旅行需求 |
| `scenario_id` | string\|null | — | 关联的测试场景 ID（盲测用） |
| `group` | string\|null | — | 盲测分组：`"A"` / `"B"` / `"C"` |

**响应**: `StreamingResponse` (SSE, `text/event-stream`)

> 返回完整的 SSE 事件流，前端通过 `EventSource` 消费。每个事件是 JSON 格式。

**SSE 事件类型** (`event_type` 字段):

| event_type | stage | status | 说明 |
|------------|-------|--------|------|
| `stage_update` | `intent` | `started` | 正在理解需求 |
| `intent_detected` | `intent` | `complete` | 意图已解析，data 含 IntentOutput |
| `stage_update` | `prefilter` | `started` | 正在筛选 POI |
| `poi_selected` | `prefilter` | `complete` | POI 筛选完成，data 含数量 |
| `pipeline_stage` | `agent` | `started` | Agent 智能补充开始 |
| `agent_thinking` | `agent` | `thinking` | Agent 正在思考 |
| `tool_executing` | `agent` | `executing` | Agent 工具执行中，message 含中文描述 |
| `tool_completed` | `agent` | `completed` | Agent 工具完成 |
| `agent_error` | `agent` | `error` | Agent 执行失败，pipeline 继续降级 |
| `pipeline_stage` | `agent` | `completed` | Agent 阶段完成 |
| `stage_update` | `generation` | `started` | 正在生成行程 |
| `stage_update` | `generation` | `complete` | 行程生成完成 |
| `validation_result` | `validation` | `complete` | 路线验证结果 |
| `done` | `complete` | `complete` | **最终事件**，data 含完整 Itinerary |
| `error` | `error` | `error` | 错误事件 |

**示例 SSE 事件**:
```
data: {"event_type": "intent_detected", "stage": "intent", "status": "complete", "message": "了解！你想要上海2天的行程", "data": {"city": "上海", "days": 2, "budget_level": "适中", "pace": "适中", "rating_level": "较好", "interests": ["咖啡", "历史建筑"]}, "timestamp": "2026-04-21T03:31:29.628665"}

data: {"event_type": "tool_executing", "stage": "agent", "status": "executing", "message": "正在搜索相关地点...", "timestamp": "2026-04-21T03:31:53.924341"}

data: {"event_type": "done", "stage": "complete", "status": "complete", "message": "行程生成完毕！", "data": {"title": "上海2日品味之旅", "summary": "...", "days": [...]}, "timestamp": "..."}
```

**最终 `done` 事件的 `data` 格式** (`Itinerary`):
```json
{
  "title": "上海2日品味之旅",
  "summary": "这条路线带你在梧桐树下发现...",
  "days": [
    {
      "day_number": 1,
      "theme": "老城厢咖啡与建筑之旅",
      "pois": [
        {
          "poi_id": "POI_ID",
          "name": "愚园路",
          "time_slot": "09:00-11:00",
          "highlight_note": "推荐理由：...",
          "vibe_description": "整条路超适合 CityWalk...",
          "walk_to_next_minutes": 10,
          "tier": 2,
          "latitude": 31.2234,
          "longitude": 121.4321
        }
      ]
    }
  ],
  "total_walking_minutes": 180
}
```

---

### AI 聊天 (Chat)

#### `POST /api/chat` — AI 对话 (SSE 流式)

**认证**: 可选（登录用户有记忆和历史）

**请求体** `ChatRequest`:
```json
{
  "message": "上海有哪些小众咖啡馆推荐？",
  "session_id": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | ✅ | 用户消息 |
| `session_id` | string\|null | — | 会话 ID（不传则自动生成），用于关联历史消息 |

**响应**: `StreamingResponse` (SSE)

**SSE 事件类型**:

| event_type | 说明 |
|------------|------|
| `chat_thinking` | AI 正在思考 |
| `tool_executing` / `tool_completed` | Agent 工具调用过程（可见但不暴露技术细节） |
| `chat_text` | **最终文本响应**，data.text 含 AI 回复内容 |
| `error` | 错误 |

**最终 `chat_text` 事件**:
```json
{"event_type": "chat_text", "stage": "chat", "status": "completed", "message": "上海的小众咖啡馆，我推荐...", "data": {"text": "上海的小众咖啡馆...", "session_id": "uuid"}}
```

> 登录用户：消息自动存入 `chat_messages` 表，支持多轮上下文记忆（最近 10 条）。

---

### 行程管理 (Itineraries)

#### `GET /api/itineraries` — 当前用户的行程列表

**认证**: 需要

**响应** `200`:
```json
[
  {
    "id": "uuid",
    "city": "上海",
    "title": "上海2日品味之旅",
    "date": "2026-04-21",
    "poi_count": 12
  }
]
```

---

#### `GET /api/itinerary/{itinerary_id}` — 行程详情

**认证**: 不需要

**响应** `200`:
```json
{
  "id": "uuid",
  "scenario_id": "scenario-1",
  "group": "A",
  "city": "上海",
  "itinerary": { ... Itinerary 对象 ... }
}
```

**错误**: `404` — 行程不存在

---

#### `GET /api/itinerary/{itinerary_id}/meta` — 行程公开元信息

**认证**: 不需要（用于生成 OG 标签/分享卡片）

**响应** `200`:
```json
{
  "title": "上海2日品味之旅",
  "description": "上海2日精选行程，发现独特体验。",
  "city": "上海"
}
```

---

#### `PUT /api/itinerary/{itinerary_id}` — 直接更新行程（无 AI）

**认证**: 需要

**请求体**:
```json
{
  "itinerary": { ... Itinerary 对象 ... }
}
```

**响应** `200`: 返回更新后的 itinerary

---

### 行程调整 (Adjust)

#### `POST /api/itinerary/adjust` — 调整行程 (SSE 流式)

**认证**: 可选

**请求体** `AdjustmentRequest`:
```json
{
  "itinerary_id": "uuid",
  "adjustment_text": "增加更多咖啡馆，减少博物馆",
  "conversation_history": []
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `itinerary_id` | string | ✅ | 要调整的行程 ID |
| `adjustment_text` | string | ✅ | 自然语言调整要求 |
| `conversation_history` | list[dict] | — | 历史对话，用于多轮调整上下文 |

**响应**: `StreamingResponse` (SSE)，事件包括 `adjust_started` → `adjust_progress` → `adjust_done` 或 `error`

**最终事件 `adjust_done`**:
```json
{"event_type": "adjust_done", "data": {"changes": [...], "updated_itinerary": {...}}}
```

---

#### `POST /api/itinerary/adjust/confirm` — 确认调整

**认证**: 需要

**请求体**:
```json
{
  "itinerary_id": "uuid",
  "confirmed": true
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `confirmed` | bool | `true` = 保存调整；`false` = 取消 |

**响应** `200`:
```json
{"id": "uuid", "itinerary": {...updated_itinerary...}}
```

---

### 场景 (Scenarios)

#### `GET /api/scenarios` — 获取所有测试场景

**认证**: 不需要

**响应** `200`:
```json
[
  {
    "id": "scenario-1",
    "name": "文艺独行侠",
    "description": "28岁女生...",
    "user_input": "我一个人来上海过周末末...",
    "city": "上海",
    "tags": "[\"独行\", \"文艺\", \"咖啡\", \"历史建筑\", \"漫歩\"]"
  }
]
```

---

#### `GET /api/scenarios/{scenario_id}/itineraries` — 获取某场景的已生成行程

**认证**: 不需要

**响应** `200`:
```json
{
  "scenario_id": "scenario-1",
  "itineraries": {
    "A": {"id": "uuid", "group": "A", "itinerary": {...}},
    "B": {"id": "uuid", "group": "B", "itinerary": {...}}
  }
}
```

---

### 配置 (Config)

#### `GET /api/config/amap-key` — 获取高德地图 JS API Key

**认证**: 不需要

> 高德 JS API Key 是域名受限的，可以安全地暴露给前端。

**响应** `200`:
```json
{"key": "28e43cdcbb4e67595bff042a7799886d"}
```

---

### 反馈 (Feedback)

#### `POST /api/feedback` — 提交行程反馈

**认证**: 可选

**请求体** `FeedbackRequest`:
```json
{
  "itinerary_id": "uuid",
  "rating": "准",
  "comment": "行程很棒！"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `itinerary_id` | string | ✅ | 被评价的行程 ID |
| `rating` | string | ✅ | `"准"` / `"一般"` / `"不准"` |
| `comment` | string\|null | — | 文字评价 |

**响应** `200`:
```json
{"status": "ok"}
```

---

### 盲测 (Blind Test)

#### `GET /api/test-results/summary` — 盲测统计汇总

**认证**: 不需要

**响应** `200`:
```json
{"A": 4, "B": 3, "C": 2}
```

> 各组被偏好的次数统计。

---

#### `GET /api/test-results/analysis` — 盲测分析报告

**认证**: 不需要

**响应** `200`:
```json
{
  "total_responses": 9,
  "aggregated_a_rate": 0.44,
  "verdict": "A 组显著胜出",
  "verdict_reason": "A 组在所有场景中的胜率...",
  "highlight_note_effect": "使用了高亮理由的 A 组显著优于 C 组...",
  "scenarios": [
    {"scenario_id": "scenario-1", "a_rate": 0.67}
  ]
}
```

---

#### `POST /api/test-results` — 提交盲测选择

**认证**: 不需要

**请求体** `TestResultCreate`:
```json
{
  "scenario_id": "scenario-1",
  "participant_id": "participant-uuid",
  "group": "A",
  "preferred_itinerary_id": "uuid",
  "preference_reason": "行程更有故事感"
}
```

**响应** `200`:
```json
{"status": "ok"}
```

---

#### `POST /api/test-runner/generate` — 触发盲测数据生成

**认证**: 不需要（内部使用）

**请求体**: `{}` (空对象)

**响应** `200`:
```json
{
  "generated": 12,
  "items": [
    {"scenario": "文艺独行侠", "group": "A", "id": "uuid"},
    ...
  ]
}
```

> 为所有场景 × 所有分组 (A/B/C) 批量生成行程数据。耗时较长（约分钟级）。

---

#### `GET /api/test-runner/status` — 测试运行器状态

**认证**: 不需要

**响应** `200`:
```json
{"status": "ready", "note": "Run POST /test-runner/generate to generate test data"}
```

---

### 健康检查

#### `GET /api/health` — 服务健康检查

**认证**: 不需要

**响应** `200`:
```json
{"status": "ok", "db": "connected"}
```

---

## 核心数据模型

### IntentOutput (阶段产出)

```python
class IntentOutput(BaseModel):
    city: str                    # 单一城市（多城市请求将被拒绝）
    days: int                    # 1-3 天
    budget_level: str           # "经济" | "适中" | "宽裕"
    pace: str                    # "悠闲" | "适中" | "紧凑"
    rating_level: str            # "一般" | "较好" | "极好"
    interests: list[str]         # 品味标签列表
    special_requests: str | None  # 特殊要求（回避项等）
    time_constraints: str | None  # 时间约束
```

### POICandidate (POI 候选)

```python
class POICandidate(BaseModel):
    id: str
    name: str
    tier: int                    # 1=A级(顶级), 2=B级(较好), 3=C级(普通)
    category: str                # "餐饮" | "景点" | "购物" | "娱乐" | "住宿"
    taste_tags: list[str]        # 品味标签
    highlight_note: str | None   # AI 生成的高亮推荐理由
    permanent_features: list[str]
    walk_time_minutes: int | None
    rating: float | None
```

### Itinerary (行程)

```python
class Itinerary(BaseModel):
    title: str
    summary: str                 # 行程总述
    days: list[ItineraryDay]
    total_walking_minutes: int

class ItineraryDay(BaseModel):
    day_number: int
    theme: str                  # 今日主题，如"老城厢咖啡与建筑之旅"
    pois: list[POIVisit]

class POIVisit(BaseModel):
    poi_id: str | None          # 对应 pois 表的 ID（无 POI 数据时为 None）
    name: str
    time_slot: str               # "09:00-10:30"
    highlight_note: str | None  # 推荐理由
    vibe_description: str       # 体验描述
    walk_to_next_minutes: int | None
    tier: int | None             # A/B/C
    latitude: float | None       # 纬度（来自数据库）
    longitude: float | None     # 经度（来自数据库）
```

### ValidationResult (路线验证)

```python
class ValidationResult(BaseModel):
    is_valid: bool
    flagged_segments: list[FlaggedSegment]  # 步行时间过长的路段
    total_walking_minutes: int

class FlaggedSegment(BaseModel):
    from_poi: str
    to_poi: str
    walk_minutes: int
    is_acceptable: bool         # ≤15分钟为可接受
```

### 数据库模型 (ORM)

| 模型 | 说明 |
|------|------|
| `User` | 用户账户 (email, password_hash, taste_tags_default, budget_default) |
| `POI` | 景点/餐厅/咖啡馆数据 (name, tier, category, taste_tags, lat/lng, highlight_note) |
| `Scenario` | 测试场景 (id, name, user_input, city, tags) |
| `ItineraryRow` | 已生成的行程 (user_id, scenario_id, group, city, raw_response, parsed_itinerary) |
| `FeedbackLog` | 用户反馈 (itinerary_id, rating, comment) |
| `TestResult` | 盲测结果 (scenario_id, participant_id, group, preferred_itinerary_id) |
| `ChatMessage` | 聊天记录 (user_id, role, content, session_id) |
| `AgentMemory` | Agent 记忆 (user_id, key, value JSON, category, access_count) |

---

## 流水线架构

```
用户输入
    │
    ▼
Stage 1: 意图提取 (extract_intent)
    │ IntentOutput (city, days, interests...)
    ▼
Stage 2: POI 筛选 (filter_pois)
    │ 从数据库 + 高德 API 获取候选 POI
    │ 按品味标签 + tier 过滤
    ▼
[NEW] Agent Stage: 智能补充 (agent_enrich)
    │ Agent 调用工具：
    │   - get_user_preferences (记忆读取)
    │   - query_weather (天气查询)
    │   - search_pois (POI 补充搜索)
    │   - web_search (网络信息)
    │ 输出: enrichment_text (补充说明)
    ▼
Stage 3: 行程生成 (generate_itinerary)
    │ SOUL 提示词 + POI 候选 + enrichment_context
    │ LLM JSON Mode → Itinerary
    ▼
Stage 4: 路线验证 (validate_itinerary)
    │ 高德路径规划 API 验证步行距离
    │ 标记 >15 分钟的过长路段
    ▼
数据库存储 → SSE done 事件 → 前端渲染
```

每个阶段通过 `EventBus` 实时推送 SSE 事件，前端渐进式展示生成过程。

---

## 开发指南

### 代码规范

```bash
# Python lint + format
ruff check src/backend/

# 前端类型检查
cd src/frontend && npm run type-check

# 前端构建
npm run build
```

### 测试

```bash
# 运行全部测试
pytest

# 运行指定测试
pytest tests/test_stage_agent.py -v

# 查看覆盖率
pytest --cov=src/backend --cov-report=html
```

### 数据库迁移

```bash
# 创建新迁移（修改 models 后）
alembic revision --autogenerate -m "add agent_memories table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

> 注意：初始迁移 (`9ccde6d944e6_initial`) 为空，所有表通过 `Base.metadata.create_all()` 在应用启动时创建。后续迁移正常追加 schema 变更。

### Agent 工具列表 (Phase 12)

| 工具函数 | 功能 | 数据来源 |
|---------|------|---------|
| `read_memories` | 读取用户记忆 | agent_memories 表 |
| `write_memory` | 写入/更新记忆 | agent_memories 表 |
| `search_pois` | POI 搜索 | 数据库优先 → 高德 fallback |
| `query_weather` | 天气预报 | 高德天气 API |
| `get_user_preferences` | 读取用户偏好 | User 表 |
| `get_itinerary_context` | 读取最近行程上下文 | ItineraryRow 表 |
| `web_search` | 网络搜索 | DuckDuckGo |
| `web_fetch` | 网页内容抓取 | httpx (SSRF 防护) |
| `list_files` | 列出记忆文件 | data/agent_memory/{user_id}/ |
| `read_file` | 读取记忆文件 | data/agent_memory/{user_id}/ |
| `write_file` | 写入记忆文件 | data/agent_memory/{user_id}/ |
| `execute_command` | 命令执行 | 桩 (默认禁用) |

---

## 部署

### Docker 生产部署

```bash
# 构建（使用 BuildKit 缓存）
DOCKER_BUILDKIT=1 docker compose build

# 启动
docker compose up -d

# 查看日志
docker compose logs -f backend

# 停止
docker compose down
```

### 架构图

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   用户浏览器  │────▶│   Nginx :80  │────▶│   Vue 前端   │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                            │  /api/*
                            ▼
                     ┌──────────────┐
                     │  FastAPI :8000│◀──▶  SQLite (data/)
                     │              │
                     │  ┌────────┐  │
                     │  │ Pipeline │  │     ┌──────────────┐
                     │  │  Agent  │──│────▶│  DeepSeek    │
                     │  └────────┘  │     │  LLM API      │
                     │       │       │     └──────────────┘
                     │       ▼       │
                     │  ┌────────┐  │     ┌──────────────┐
                     │  │  Tools  │──│────▶│  高德地图     │
                     │  └────────┘  │     │  POI + 天气   │
                     └──────────────┘     └──────────────┘
```

---

## 许可证

MIT License
