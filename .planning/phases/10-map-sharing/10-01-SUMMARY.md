---
phase: 10-map-sharing
plan: 01
subsystem: backend-api
tags: [api, coordinates, amap, og-tags]
dependency_graph:
  requires: []
  provides: [coordinates-enrichment, amap-key-endpoint, meta-endpoint]
  affects: [10-02]
tech_stack:
  added: []
  patterns:
    - "Enrichment-on-retrieval: POI coordinates injected from database at API response time"
    - "UUID validation on path parameters for security"
key_files:
  created:
    - src/backend/api/routes/config.py
  modified:
    - src/backend/api/routes/itineraries.py
    - src/backend/models/pydantic.py
    - src/backend/main.py
    - src/frontend/src/types/itinerary.ts
    - src/frontend/src/tailwind.css
decisions:
  - "Use batch POI lookup with IN clause for efficient coordinate enrichment"
  - "Return null coordinates for POIs not in database (AI-generated) rather than filtering out"
  - "Expose amap JS API key via public endpoint - key is domain-restricted, not secret"
  - "Validate UUID format on path parameters to prevent injection (T-10-02 mitigation)"
  - "Change --color-source-amap from #3B82F6 to #6BA3D6 to avoid clash with Day 1 route color"
metrics:
  duration: 15m
  completed_date: 2026-04-17
---

# Phase 10 Plan 01: Backend API Enrichment Summary

## Overview
Established the data foundation for the map visualization by enriching itinerary API responses with POI coordinates and providing the necessary configuration endpoints for frontend map initialization.

## What Was Built

### 1. POI Coordinate Enrichment
- **Modified** `GET /api/itineraries/{id}` endpoint to inject `latitude` and `longitude` for each POI
- Uses batch lookup from the `pois` database table via `POI.id.in_(poi_ids)` for efficiency
- POIs without database entries (AI-generated) gracefully receive `null` coordinates
- Added UUID validation on path parameters for security (T-10-02 mitigation)

### 2. Amap JS API Key Endpoint
- **Created** `GET /api/config/amap-key` endpoint in new `config.py` router
- Returns the JS API key from `Settings.amap_api_key`
- **No authentication required** - the key is domain-restricted and designed for client-side exposure

### 3. OG Meta Tags Endpoint
- **Created** `GET /api/itineraries/{id}/meta` endpoint
- Returns `{title, description, city}` for OpenGraph meta tag generation
- No authentication required for shareable itinerary pages
- Title extracted from `parsed_itinerary` JSON, falling back to "{city}行程"

### 4. Type Updates
- **Added** `latitude?: number` and `longitude?: number` fields to `POIVisitData` TypeScript interface
- **Added** CSS custom properties for day route colors:
  - `--color-day-1: #3B82F6` (Day 1 blue)
  - `--color-day-2: #10B981` (Day 2 green)  
  - `--color-day-3: #F59E0B` (Day 3 orange)
- **Changed** `--color-source-amap` from `#3B82F6` to `#6BA3D6` to avoid color conflict with Day 1 route color

## Verification

All backend modules pass syntax validation:
- ✓ `config.py` imports successfully
- ✓ `itineraries.py` imports successfully  
- ✓ `pydantic.py` POIVisit model with coordinates instantiates correctly
- ✓ `main.py` router registration successful

## Deviations from Plan

None - plan executed exactly as written.

## Threat Model Compliance

| Threat ID | Status | Notes |
|-----------|--------|-------|
| T-10-01 | ✓ Accepted | JS API key is domain-restricted, public exposure by design |
| T-10-02 | ✓ Mitigated | UUID format validation prevents path parameter injection |
| T-10-03 | ✓ Accepted | Meta endpoint returns public itinerary data only |

## Key Decisions

1. **Enrichment-on-retrieval**: Coordinates injected at API response time rather than stored in itinerary JSON, allowing database-backed POIs to be updated without regenerating itineraries.

2. **Graceful degradation**: POIs without coordinates (AI-generated or not in database) return `null` rather than causing errors - the frontend map skips these.

3. **Domain-restricted key exposure**: The amap JS API key is domain-restricted in the amap console, making public exposure safe by design.

4. **Color conflict resolution**: Changed data source color from blue (#3B82F6) to softer teal (#6BA3D6) to free up blue for Day 1 route color.

## Next Steps

This plan provides the data foundation required by Plan 10-02 (Frontend Map Components). The following are now ready:
- Coordinates available in GET /api/itineraries/{id} response
- Amap JS API key available via GET /api/config/amap-key
- Day route colors defined in CSS
- POIVisitData TypeScript type includes latitude/longitude

Proceed to Plan 10-02 to build the MapView component and responsive layout.

---

## Self-Check: PASSED

- ✓ All created/modified files exist and have correct content
- ✓ All imports validate without syntax errors
- ✓ Commit d2af265 created with plan 10-01 changes
