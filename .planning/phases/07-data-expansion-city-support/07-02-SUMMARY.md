---
phase: 07-data-expansion-city-support
plan: 02
subsystem: hangzhou-data
tags: [poi-data, scenarios, auto-seeding, multi-city]
dependency_graph:
  requires: []
  provides: [hangzhou-poi-data, multi-city-auto-seeding]
  affects: [main.py, scenarios]
tech_stack:
  added: []
  patterns: [file-driven-seeding, filename-to-city-mapping]
key_files:
  created:
    - data/pois/hangzhou.json
  modified:
    - data/scenarios/scenarios.json
    - src/backend/main.py
decisions:
  - Hangzhou chosen as second city — proximity to Shanghai, rich cultural scene
  - 21 POIs (12 Tier A, 6 Tier B, 3 Tier C) — curated manually for MVP
  - Placeholder amap_ids (curated_hz_XXX) — real IDs backfilled later via Amap API
  - Auto-discovery seeding via glob("data/pois/*.json") — adding future cities = drop JSON file
  - Filename-to-city mapping dict in main.py — extensible
  - is_chain field added to both shanghai.json and hangzhou.json for Tier C identification
metrics:
  duration: manual
  completed: "2026-04-17"
  tasks: 2
  files: 3
---

# Phase 7 Plan 2: Hangzhou POI Data + Multi-city Auto-seeding Summary

Added Hangzhou as second city with curated POI data and upgraded auto-seeding to discover all city files.

## What Was Done

### Task 1: Create Hangzhou POI data and scenarios
- Created `data/pois/hangzhou.json` with 21 POIs: 12 Tier A (curated landmarks), 6 Tier B (restaurants/cafés), 3 Tier C (chains/budget)
- Added 2 Hangzhou scenarios to `data/scenarios/scenarios.json` (scenario-5: 杭州文艺周末, scenario-6: 杭州美食探索)
- Total scenarios: 6 (4 Shanghai + 2 Hangzhou)
- Added `is_chain` field to both shanghai.json and hangzhou.json POIs

### Task 2: Multi-city auto-seeding in main.py
- Replaced hardcoded `shanghai.json` with `glob("data/pois/*.json")` auto-discovery
- Added `_FILENAME_TO_CITY` mapping dict (shanghai→上海, hangzhou→杭州)
- Each POI file seeds independently with try/except — one failure doesn't block others
- Added logging for observability

## Deviations from Plan

- POI count reduced from 40-45 to 21 — simplified for MVP per user decision
- No acquisition script — manual curation replaced automated acquisition
- Added `is_chain` field post-hoc to address CITY-04 requirement gap
- SUMMARY.md created retroactively during review

## Commits

| Commit | Description |
|--------|-------------|
| 3b9d3b9 | feat(07-02): add Hangzhou POI data, scenarios, and multi-city auto-seeding |

## Self-Check: PASSED

- 21 Hangzhou POIs across 3 tiers, all required fields present
- 6 scenarios (4 Shanghai + 2 Hangzhou)
- No hardcoded shanghai.json in main.py
- glob-based auto-discovery working
