# Phase 9: UI Redesign & Rich Display - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 09-ui-redesign-rich-display
**Areas discussed:** Color & Warmth, POI Rich Display, Source Badge, Generation Loading, Home Hero, Data Gap

---

## Color & Warmth

| Option | Description | Selected |
|--------|-------------|----------|
| Sand + Coral + Ocean | 沙滩色底，珊瑚强调，海洋蓝辅助 | ✓ |
| Terracotta + Cream + Gold | 深橙+米黄+金色，沙漠暖阳感 | |
| Burgundy + Gold + Cream | 勃艮第红+暗金+奶油，沉稳质感 | |

**User's choice:** Sand + Coral + Ocean
**Notes:** Warm but not overwhelming. Good match for travel/lifestyle app targeting 18-35.

## Card Visual Style

| Option | Description | Selected |
|--------|-------------|----------|
| Soft Shadow + Hover Lift | 圆角16px，柔和阴影，悬停上浮 | ✓ |
| Flat with Accent Border | 渐变边框或底部色条 | |
| Postcard Texture | 明信片质感，轻微纹理 | |

**User's choice:** Soft Shadow + Hover Lift
**Notes:** Airbnb/Monocle card feel.

## POI Detail Display Mode

| Option | Description | Selected |
|--------|-------------|----------|
| Always Visible | 所有信息直接显示 | |
| Expandable | 基本信息可见，点击展开详情 | ✓ |
| Separate Detail Page | 跳转独立页面 | |

**User's choice:** Expandable (current pattern preserved)

## Data Source Attribution

| Option | Description | Selected |
|--------|-------------|----------|
| Inline Tag | 名称旁边小标签：金色/蓝色/紫色 | ✓ |
| Corner Badge | 右上角图标+文字 | |
| Icon Only | ★📍✨ 图标区分 | |

**User's choice:** Inline Tag

## Generation Loading

| Option | Description | Selected |
|--------|-------------|----------|
| Warm Progress Bar + Travel Text | 温暖渐变进度条+旅途场景文字 | ✓ |
| Animated Journey Icon | 飞机/火车/徒步图标移动 | |
| Minimal: Dots + Warm Text | 保持圆点，只换颜色文字 | |

**User's choice:** Warm Progress Bar + Travel Text

## Home Hero

| Option | Description | Selected |
|--------|-------------|----------|
| Gradient Hero + Journey Cards | 全宽渐变背景+可点击旅程卡片 | ✓ |
| Floating Postcard Cards | 半透明明信片卡片 | |
| Minimal Update | 保持简单布局只换配色 | |

**User's choice:** Gradient Hero + Journey Cards

## Data Gap Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Frontend-first with Placeholders | 前端先用占位，后端后续补上 | ✓ |
| Add Backend Data in Phase 9 | 本 phase 内加后端字段 | |

**User's choice:** Frontend-first with Placeholders

## the agent's Discretion

- Exact gradient angles/stops for hero background
- Journey card icons selection
- Exact shadow pixel values
- Progress bar animation timing
- Transition animations between states

## Deferred Ideas

None — discussion stayed within phase scope.
