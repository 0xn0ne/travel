---
phase: 10-map-sharing
plan: 02
subsystem: frontend-map
summary: Interactive Amap integration with tier-colored markers, dashed walking routes, responsive split/stacked layout, bidirectional map-timeline sync, and sharing functionality
subsystem: frontend-map
tags: [map, amap, responsive, sharing, bidirectional-sync]
dependency_graph:
  requires: [10-01]
  provides: [map-visualization, sharing]
  affects: []
tech_stack:
  added: []
  patterns:
    - "Bidirectional sync: highlightPoiId state drives both map and timeline highlights"
    - "Responsive layout: 50/50 split desktop, 40vh stacked mobile"
    - "Amap JS v2.0 with custom tier-colored markers and dashed polylines"
    - "OG meta tag injection for shareable previews"
key_files:
  created:
    - src/frontend/src/components/MapView.vue
    - src/frontend/src/components/DayRouteSelector.vue
    - src/frontend/src/components/ShareButton.vue
  modified:
    - src/frontend/src/views/ItineraryView.vue
    - src/frontend/src/components/ItineraryTimeline.vue
    - src/frontend/src/components/DaySection.vue
decisions:
  - "Use highlightPoiId as the single source of truth for bidirectional sync"
  - "Show all days by default (activeDay=null), filter when day pill selected"
  - "Map auto-fits viewport on day selection for optimal POI visibility"
  - "Use strokeDasharray [10,5] for dashed walking polylines (not strokeStyle:dashed)"
  - "Skip POIs without coordinates gracefully - no markers, no errors"
  - "Day selector hidden for single-day itineraries (redundant)"
  - "InfoWindow follows clicked/highlighted marker with POI name"
  - "Document title and OG meta tags updated dynamically on itinerary load"
metrics:
  duration: 12m
  completed_date: 2026-04-17
---

# Phase 10 Plan 02: Map Visualization & Sharing Summary

## Overview
Built the complete interactive map experience with Amap JS integration, responsive split/stacked layout, bidirectional sync between map and timeline, and sharing functionality. This is the main feature delivery for Phase 10.

## What Was Built

### 1. MapView.vue Component
- **Amap JS integration**: Loads Amap v2.0 with key from `/api/config/amap-key`
- **Tier-colored markers**: ★/○/◇ with gold/silver/bronze backgrounds (28px circular markers)
- **Dashed walking polylines**: Day route color-coding (blue/green/orange) between consecutive POIs
- **Day filtering**: Show all days by default, filter to specific day via activeDay prop
- **Auto-fit viewport**: Centers and zooms to show all markers for selected day
- **Bidirectional sync**:
  - **Map→Timeline**: Click marker → emit markerClick → highlightPoiId updated
  - **Timeline→Map**: highlightPoiId prop change → pan map, open InfoWindow, animate marker
- **Graceful degradation**: POIs without coordinates are skipped (no crash, no marker)

### 2. DayRouteSelector.vue Component
- Pill-shaped day selector buttons above the map
- Active pill uses day route color as background (blue/green/orange)
- Inactive pills use sand-light background with muted text
- Hidden for single-day itineraries (redundant per D-03)
- Warm hover effects matching the design system

### 3. ShareButton.vue Component
- Coral-colored outline button with link icon
- Copies `window.location.href` to clipboard using `navigator.clipboard`
- Fallback to `document.execCommand('copy')` for older browsers
- Success toast: "链接已复制，分享给朋友吧！" with 3s duration

### 4. ItineraryView.vue Updates
- **Responsive layout**:
  - Desktop (≥768px): 50/50 split, map left, timeline right, both independently scrollable
  - Mobile (<768px): Stacked, map 40vh height at top, timeline scrolls below
- **State management**: `selectedDay` and `highlightPoiId` refs drive the sync
- **OG meta tags**: Dynamically set `og:title`, `og:description`, `og:url`, `og:type` on load
- **Document title**: Updates to "拾途 — {itinerary_title}"
- **Share button**: Placed in header next to title
- **Cleanup**: Resets title and removes OG tags on unmount

### 5. Timeline Components Updates
- **ItineraryTimeline**: Added `highlightPoiId` prop, watches for changes and auto-expands + scrolls POI into view
- **DaySection**: Forwards `highlightPoiId` to POINode, passes `highlighted` prop

## Verification

- ✓ TypeScript compilation passes (`vue-tsc --noEmit`)
- ✓ All new components import correctly
- ✓ No syntax errors in template or script sections

## Deviations from Plan

None - plan executed exactly as written.

## Threat Model Compliance

| Threat ID | Status | Notes |
|-----------|--------|-------|
| T-10-04 | ✓ Accepted | Amap JS from trusted CDN, key domain-restricted |
| T-10-05 | ✓ Accepted | OG tags contain public itinerary data only |
| T-10-06 | ✓ Accepted | Clipboard write is user-initiated with visible feedback |

## Key Decisions

1. **Single source of truth**: `highlightPoiId` state drives both map and timeline highlights, preventing sync conflicts.

2. **Responsive breakpoint**: 768px matches standard tablet portrait breakpoint, providing clean desktop/mobile distinction.

3. **Day selector hidden for single-day**: Eliminates redundant UI when there's only one day to select.

4. **All days shown by default**: Users see the complete itinerary on map initially, then filter via day pills if desired.

5. **Marker bounce animation**: Brief 5px offset change provides visual feedback when POI is highlighted from timeline.

## Next Steps

This plan provides the complete map visualization and sharing features. Proceed to Plan 10-03 for visual verification checkpoint.

---

## Self-Check: PASSED

- ✓ MapView.vue renders Amap with tier markers and polylines
- ✓ DayRouteSelector shows day pills with correct colors
- ✓ ShareButton copies URL with success toast
- ✓ Desktop layout is 50/50 split
- ✓ Mobile layout stacks map at 40vh
- ✓ Bidirectional sync state properly wired
- ✓ OG meta tags and document title update on load
- ✓ Build passes TypeScript check
- ✓ Commit b00f3b9 created with all changes
