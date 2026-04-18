# 拾途 (Shí Tú) - 品味行程生成器

> 面向 18-35 岁中国年轻旅行者的 AI 行程规划工具，用"本地朋友推荐"的温度帮你发现会喜欢但自己找不到的地方。

## 项目简介

拾途是一个基于 AI 的旅行行程生成器，核心特点：
- **品味数据 + LLM 叙事**：不是千篇一律的景点排列，而是有温度、有节奏、有惊喜的个性化行程
- **SSE 流式输出**：实时展示行程生成过程，体验如与朋友聊天的流畅感
- **高德地图集成**：POI 位置可视化，路线规划更直观

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.135.3 |
| 前端框架 | Vue 3 | 3.5.32 |
| 构建工具 | Vite | 8.0.8 |
| UI 组件库 | Naive UI | 2.44.1 |
| 状态管理 | Pinia | 3.0.4 |
| 数据库 | SQLite (SQLAlchemy 异步) | - |
| LLM | DeepSeek-V3 (deepseek-chat) | - |
| 地图服务 | 高德开放平台 | - |

### 核心依赖

**后端**
- fastapi, uvicorn, pydantic, pydantic-settings
- sqlalchemy[asyncio], aiosqlite, alembic
- openai (DeepSeek API 客户端)
- httpx, tenacity

**前端**
- vue, vue-router, pinia
- naive-ui, axios, @vueuse/core
- tailwindcss, @amap/amap-jsapi-loader

## 快速开始

### 前置要求

- **Docker** (推荐)
- 或者 **Python 3.12+** + **Node.js 22+** + **npm**

### 方式一：Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone <repo-url>
cd silent-river

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 前端: http://localhost
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 方式二：本地运行

#### 后端

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -e .

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY 和 AMAP_API_KEY

# 4. 初始化数据库
python -m backend.db.init_db

# 5. 启动服务
uvicorn backend.main:app --reload --port 8000
```

#### 前端

```bash
cd src/frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev

# 3. 访问 http://localhost:5173
```

## 环境变量配置

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API Key (用于 LLM 生成) |
| `DEEPSEEK_BASE_URL` | - | 默认 `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | - | 默认 `deepseek-chat` |
| `AMAP_API_KEY` | ✅ | 高德开放平台 Key (用于 POI 搜索) |
| `DATABASE_URL` | - | SQLite 数据库路径 |
| `CORS_ORIGINS` | - | 允许的跨域来源 |

获取 API Keys:
- **DeepSeek**: https://platform.deepseek.com/
- **高德开放平台**: https://lbs.amap.com/

## 项目结构

```
silent-river/
├── src/
│   ├── backend/           # FastAPI 后端
│   │   ├── api/          # API 路由和依赖
│   │   │   ├── routes/   # 业务路由 (generate, adjust, itineraries...)
│   │   │   └── auth.py   # 认证逻辑
│   │   ├── db/           # 数据库初始化和种子数据
│   │   ├── llm/          # DeepSeek 客户端和输出解析
│   │   ├── models/       # SQLAlchemy 模型和 Pydantic Schema
│   │   ├── pipeline/     # 行程生成流水线
│   │   │   └── stages/   # 4阶段生成 (意图理解→POI筛选→行程生成→叙事润色)
│   │   ├── services/     # 外部服务 (高德地图)
│   │   ├── config.py     # 配置管理
│   │   └── main.py       # 应用入口
│   │
│   └── frontend/         # Vue 3 前端
│       ├── src/
│       │   ├── api/      # API 客户端
│       │   ├── components/  # 组件 (Timeline, Map, POI, Auth...)
│       │   ├── composables/  # 组合式函数 (useSSE)
│       │   ├── stores/   # Pinia 状态管理
│       │   ├── views/   # 页面视图
│       │   ├── router/  # 路由配置
│       │   └── types/   # TypeScript 类型
│       ├── package.json
│       └── vite.config.ts
│
├── data/                 # SQLite 数据库文件
├── scripts/              # 辅助脚本
├── alembic/             # 数据库迁移
├── docker-compose.yml   # Docker 编排
├── Dockerfile.backend   # 后端镜像
├── Dockerfile.frontend  # 前端镜像
├── nginx.conf           # Nginx 配置
├── pyproject.toml        # Python 依赖
├── .env.example          # 环境变量示例
└── README.md
```

## 核心功能

### 行程生成流程 (4 阶段 SSE 流式)

1. **意图理解** - 解析用户需求，提取关键词、偏好、旅行风格
2. **POI 筛选** - 从高德 API 获取候选 POI，按品味标签筛选
3. **行程设计** - 规划日程、计算时间、优化路线
4. **叙事润色** - 用"本地朋友"的语气撰写推荐理由

### API 端点

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| **认证 (Auth)** ||||
| POST | `/api/auth/register` | 否 | 用户注册，返回 JWT |
| POST | `/api/auth/login` | 否 | 用户登录，返回 JWT |
| POST | `/api/auth/logout` | 是 | 登出 |
| GET | `/api/auth/me` | 是 | 获取当前用户信息 |
| PUT | `/api/auth/profile` | 是 | 更新用户偏好设置 |
| **行程生成 (Generate)** ||||
| POST | `/api/generate` | 可选 | SSE 流式生成行程 |
| GET | `/api/itinerary/stream` | 否 | SSE 重连获取进度 |
| **行程调整 (Adjust)** ||||
| POST | `/api/itinerary/adjust` | 可选 | SSE 流式调整行程 |
| POST | `/api/itinerary/adjust/confirm` | 是 | 确认调整并保存 |
| PUT | `/api/itinerary/{id}` | 是 | 直接更新行程（无 AI） |
| **行程管理 (Itineraries)** ||||
| GET | `/api/itineraries` | 是 | 获取用户行程列表 |
| GET | `/api/itinerary/{id}` | 否 | 获取行程详情 |
| GET | `/api/itinerary/{id}/meta` | 否 | 获取行程 OG 信息（公开分享用） |
| **场景 (Scenarios)** ||||
| GET | `/api/scenarios` | 否 | 获取所有测试场景 |
| GET | `/api/scenarios/{id}/itineraries` | 否 | 获取场景对应的行程 |
| **配置 (Config)** ||||
| GET | `/api/config/amap-key` | 否 | 获取高德地图 JS API Key |
| **反馈 (Feedback)** ||||
| POST | `/api/feedback` | 可选 | 提交行程反馈 |
| **盲测 (Test)** ||||
| POST | `/api/test-results` | 否 | 提交盲测选择结果 |
| GET | `/api/test-results/summary` | 否 | 获取盲测统计汇总 |
| GET | `/api/test-results/analysis` | 否 | 获取盲测分析报告 |
| POST | `/api/test-runner/generate` | - | 触发盲测数据生成（内部） |
| GET | `/api/test-runner/status` | - | 获取测试运行器状态 |
| **健康检查** ||||
| GET | `/api/health` | 否 | 服务健康检查 |

> 注意：标记"可选"的端点支持匿名使用，但登录用户可获得更好的个性化推荐。

完整 API 文档: 启动后访问 `http://localhost:8000/docs`

## 开发指南

### 代码规范

- Python: 使用 `ruff` 进行 lint 和 format
- 前端: 使用 TypeScript + Vue 3 `<script setup>`

```bash
# Python lint
ruff check src/backend/

# 前端类型检查
npm run type-check
```

### 测试

```bash
# 运行后端测试
pytest
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 部署

### 生产环境 (Docker)

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 架构图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   用户      │────▶│   Nginx     │────▶│   Vue 前端  │
│  (浏览器)   │     │   (80)      │     │             │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  FastAPI    │◀───▶│  SQLite     │
                    │  后端:8000  │     │  (POI数据)  │
                    └──────┬──────┘     └─────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
     ┌──────────┐   ┌──────────┐   ┌──────────┐
     │ DeepSeek │   │  高德    │   │  LLM     │
     │   API    │   │  POI API │   │ 流式输出 │
     └──────────┘   └──────────┘   └──────────┘
```

## 许可证

MIT License