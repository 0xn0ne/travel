---
phase: 09-ui-redesign-rich-display
plan: 01
subsystem: frontend
tags: [css, design-system, theme, tailwind, naive-ui]
dependency_graph:
  requires: []
  provides: [warm-palette-css-vars, naive-ui-theme-overrides]
  affects: [tailwind.css, App.vue]
tech_stack:
  added: [tailwind-css-@theme, naive-ui-theme-overrides]
  patterns: [css-custom-properties-source-of-truth]
key_files:
  created: []
  modified:
    - src/frontend/src/tailwind.css
    - src/frontend/src/App.vue
decisions:
  - All palette colors defined as CSS custom properties in @theme block — single source of truth
  - Naive UI component overrides use hardcoded hex (not CSS vars) due to NConfigProvider API limitations
  - Data source colors (amap, curated, ai) are attribution-only, not UI accents
metrics:
  duration: 2m
  completed: 2026-04-17
  tasks: 2
  files: 2
---

# Phase 9 Plan 01: Warm Design System Foundation Summary

Warm palette CSS custom properties (25+) via Tailwind @theme + NConfigProvider theme-overrides binding for all Naive UI components — establishing the color source of truth for every subsequent UI plan.

## Completed Tasks

| Task | Name | Commit | Files Modified |
|------|------|--------|----------------|
| 1 | Create warm palette CSS custom properties in tailwind.css | f917e18 | src/frontend/src/tailwind.css |
| 2 | Wire NConfigProvider theme-overrides in App.vue | 2d59145 | src/frontend/src/App.vue |

## What Was Done

### Task 1: Warm Palette CSS Custom Properties
Replaced bare `tailwind.css` (1 line) with full `@theme` block containing 25+ CSS custom properties:
- **Warm palette**: sand (#F5E6D3), coral (#FF6B6B), ocean (#4ECDC4) with light/dark variants (9 vars)
- **Semantic colors**: warm-bg, warm-surface, warm-text, warm-text-muted, warm-border, warm-gray, warm-amber, warm-amber-light (8 vars)
- **Tier colors**: gold, silver, bronze for POI tier indicators (3 vars)
- **Data source colors**: curated (gold), amap (blue), ai (purple) for attribution badges (3 vars)
- **Card design tokens**: 16px border-radius, soft shadow, hover shadow (3 vars)
- **Transition tokens**: smooth 0.2s ease (1 var)

### Task 2: NConfigProvider Theme Overrides
Added `themeOverrides` constant in App.vue `<script setup>` and bound to `<n-config-provider :theme-overrides>`:
- **common**: Coral primary, ocean success, warm amber warning, warm text colors, cream backgrounds, sand borders
- **Card**: 16px radius, white bg, sand border, soft shadow
- **Button**: 12px/8px rounded corners
- **Tag**: 8px rounded
- **Input**: Warm focus/hover borders, cream background
- **Alert**: Warm amber warnings, coral errors, teal info backgrounds
- **Empty**: Ocean teal icon color, muted warm text
- **Spin**: Coral accent
- **Skeleton**: Sand-to-warm-gray gradient

## Verification Results

- `npm run build`: ✅ Passed (vue-tsc + vite build, 0 errors, 781ms)
- `@theme` block present: ✅
- 25+ CSS custom properties: ✅
- NConfigProvider `:theme-overrides` binding: ✅
- All component overrides present (common, Card, Button, Tag, Input, Alert, Empty, Spin, Skeleton): ✅

## Deviations from Plan

None — plan executed exactly as written.

## Decisions Made

1. **CSS vars as source of truth**: All color values live in `@theme` block. Other files reference via `var(--color-sand)` etc.
2. **NConfigProvider uses hex strings**: Naive UI's theme-overrides API requires literal hex strings, not CSS `var()` references. The values match the CSS custom properties exactly but are duplicated as string literals — this is a Naive UI API constraint, not a design choice.
3. **Data source colors are attribution-only**: Comment preserved in tailwind.css clarifying that `--color-source-amap` and `--color-warm-amber` are for data-source attribution badges, not general UI accents. Map route colors come in Phase 10.

## Self-Check: PASSED

All files and commits verified:
- src/frontend/src/tailwind.css ✅
- src/frontend/src/App.vue ✅
- 09-01-SUMMARY.md ✅
- Commit f917e18 ✅
- Commit 2d59145 ✅
