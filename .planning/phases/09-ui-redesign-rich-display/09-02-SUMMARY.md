---
phase: 09-ui-redesign-rich-display
plan: 02
subsystem: frontend
tags: [poi-card, tier-badges, svg-icons, data-source, warm-theme, vue-component]
dependency_graph:
  requires: [warm-palette-css-vars]
  provides: [rich-poi-card-with-tier-badges]
  affects: [POINode.vue]
tech_stack:
  added: [inline-svg-icons, tier-badge-system]
  patterns: [tier-derived-data-source, css-var-only-colors]
key_files:
  created: []
  modified:
    - src/frontend/src/components/POINode.vue
decisions:
  - Tier derived from POIVisitData.tier drives both badge symbol and data source attribution label
  - All icons are inline SVG (not emoji) for consistent rendering across platforms
  - opening_hours always shows placeholder since data is not yet available in the pipeline
  - color-mix() used for semi-transparent backgrounds on change tags and danger button hover
metrics:
  duration: 3m
  completed: 2026-04-17
  tasks: 1
  files: 1
---

# Phase 9 Plan 02: Rich POI Display Summary

Complete POINode redesign with 3-tier badge system (★ gold / ○ silver / ◇ bronze), inline SVG data source attribution icons, enriched expanded detail view, warm-themed card styling — zero hardcoded hex colors.

## Completed Tasks

| Task | Name | Commit | Files Modified |
|------|------|--------|----------------|
| 1 | POINode card structure + tier badge system + warm styling | 69a8520 | src/frontend/src/components/POINode.vue |

## What Was Done

### Task 1: POINode Redesign
Rewrote POINode.vue (183→386 lines) from a flat list item into a rich card component:

**Tier Badge System:**
- `tierConfig` computed maps tier 1/2/3 to distinct symbols (★ ○ ◇) and CSS var colors
- 20x20px circular badge with white symbol on tier background color
- Defaults to tier 2 (silver) when `tier` prop is undefined

**Data Source Attribution:**
- `dataSource` computed derives label/icon from tier: tier 1 = 人工精选 (star), tier 2 = 高德地图 (pin), tier 3 = AI推荐 (sparkle)
- Inline SVG icons (14x14) in pill-shaped tag next to POI name
- Color from `--color-source-curated/amap/ai` CSS vars

**Expanded Detail View:**
- `推荐理由` section with `poi.highlight_note` (label in ocean teal)
- `氛围` section with `poi.vibe_description`
- Walk indicator with walking SVG icon + "步行 N 分钟到下一站"
- Clock icon with "暂无营业时间" placeholder

**Card Styling:**
- 16px border-radius (`--radius-card`), soft shadow (`--shadow-card`)
- Hover lift: translateY(-2px) + stronger shadow (`--shadow-card-hover`)
- Chevron arrow rotates on expand/collapse
- `color-mix()` for semi-transparent backgrounds on tags/buttons

**Preserved Preview/Diff Features:**
- Change tags (新增/替换/删除) restyled with warm palette
- Replaced POI name display with line-through
- Action toolbar (替换/删除/前插/后插) with warm border/surface styling
- Preview mode border-left using ocean/coral colors

## Verification Results

- `npm run build`: ✅ Passed (vue-tsc + vite build, 0 errors, 865ms)
- `tierConfig` present: ✅ (3 occurrences)
- `dataSource` present: ✅ (6 occurrences)
- CSS `var()` references: ✅ (36 occurrences)
- Zero hardcoded hex colors: ✅
- File line count: ✅ (386 lines, min 150 required)

## Deviations from Plan

None — plan executed exactly as written.

## Decisions Made

1. **Tier drives data source**: The `tier` number is the single source of truth for both badge appearance and data source label. No separate data source field needed.
2. **Inline SVG not emoji**: All icons are SVG path elements for pixel-perfect rendering, accessibility, and consistent sizing across browsers/OS.
3. **Opening hours placeholder**: Always shows "暂无营业时间" since the pipeline doesn't yet provide opening_hours data. When backend adds this field, the placeholder condition can be updated.
4. **color-mix() for transparency**: Used CSS `color-mix(in srgb, var 12%, white)` instead of rgba() to stay within the CSS var system without needing separate opacity values.

## Self-Check: PASSED

All files and commits verified:
- src/frontend/src/components/POINode.vue ✅
- Commit 69a8520 ✅
