---
phase: 09-ui-redesign-rich-display
plan: 03
subsystem: ui
tags: [vue, css-custom-properties, gradient, journey-cards, progress-bar, responsive-grid]

# Dependency graph
requires:
  - phase: 09-ui-redesign-rich-display/01
    provides: warm-palette-css-vars, naive-ui-theme-overrides
provides:
  - gradient-hero-section
  - journey-card-examples
  - warm-input-area
  - gradient-progress-bar-with-travel-messages
affects: [09-ui-redesign-rich-display, home-page, stage-progress]

# Tech tracking
tech-stack:
  added: []
  patterns: [css-grid-responsive-journey-cards, gradient-progress-bar, travel-themed-stage-messages]

key-files:
  created: []
  modified:
    - src/frontend/src/views/HomeView.vue
    - src/frontend/src/components/StageProgress.vue

key-decisions:
  - "Journey cards use native HTML divs with CSS Grid instead of Naive UI NTag for richer styling control"
  - "Generate button uses native button element instead of NButton for full CSS var styling (coral accent)"
  - "StageProgress adds optional city prop for personalized travel messages"
  - "Progress percent maps to non-linear stage milestones (10,30,60,85,100) for better perceived progress"

patterns-established:
  - "Journey cards: inline SVG icons + example text in responsive CSS Grid (4→2→1 columns)"
  - "Progress bar: warm gradient (sand→coral→ocean) with shimmer animation during generation"

requirements-completed: [UI-04, UI-05]

# Metrics
duration: 3m
completed: 2026-04-17
---

# Phase 9 Plan 03: Home Page Redesign Summary

**Gradient hero with journey card examples, warm input area, and travel-themed progress bar — transforming the home page into an emotional entry point**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-17T10:59:53Z
- **Completed:** 2026-04-17T11:03:14Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Hero section with full-width sand-to-ocean gradient background, large title, and warm subtitle
- 4 journey cards in responsive CSS Grid (4-col desktop, 2-col tablet, 1-col mobile) with unique travel SVG icons replacing plain NTag examples
- Warm-styled input area with focus border transition to coral, native coral generate button
- StageProgress completely rebuilt — warm gradient progress bar (sand→coral→ocean) replacing 5-dot system
- 5 travel-themed Chinese stage messages with optional city prop for personalized feedback
- Zero hardcoded hex colors in both files — all colors via CSS custom properties

## Task Commits

Each task was committed atomically:

1. **Task 1: Redesign HomeView hero + journey cards + warm input** - `687db30` (feat)
2. **Task 2: Replace StageProgress with warm gradient progress bar + travel messages** - `78d1fc3` (feat)

## Files Created/Modified
- `src/frontend/src/views/HomeView.vue` — Hero gradient, 4 journey cards in responsive grid, warm input area with coral generate button
- `src/frontend/src/components/StageProgress.vue` — Warm gradient progress bar with travel-themed stage messages, city prop, shimmer animation

## Decisions Made
1. **Native HTML for journey cards** — CSS Grid with custom divs instead of Naive UI NTag allows full control over hover transforms, shadows, and SVG icon layout
2. **Native button for generate** — Replaced NButton with native `<button>` element to use CSS var() for coral accent color (NButton doesn't support CSS var for all states)
3. **City prop for StageProgress** — Added optional `city?: string` prop to personalize stage messages (e.g., "在上海寻找有趣的地方...")
4. **Non-linear progress mapping** — Stage percentages (10→30→60→85→100) create better perceived progress than linear 20→40→60→80→100

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Home page redesign complete, ready for any remaining UI plans
- StageProgress city prop available for future integration when city context is passed from store
- Journey cards ready for expansion with more examples or dynamic content

## Self-Check: PASSED

All files and commits verified:
- src/frontend/src/views/HomeView.vue ✅
- src/frontend/src/components/StageProgress.vue ✅
- 09-03-SUMMARY.md ✅
- Commit 687db30 ✅
- Commit 78d1fc3 ✅

---
*Phase: 09-ui-redesign-rich-display*
*Completed: 2026-04-17*
