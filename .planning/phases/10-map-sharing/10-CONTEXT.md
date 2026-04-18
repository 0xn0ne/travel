# Phase 10: Map & Sharing - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning (revised after codebase audit)

<domain>
## Phase Boundary

Add interactive Amap JS map to ItineraryView (showing POI markers with tier-colored pins and walking route lines), implement map-timeline bidirectional sync with day route color-coding, responsive map layout, and itinerary sharing with copy-link + OG meta tags.

Scope: MAP-01, MAP-02, MAP-03, MAP-04, SHARE-01, SHARE-02. Map display only — no map search or POI discovery.

</domain>

<decisions>
## Implementation Decisions

### Map Layout & Responsiveness (MAP-04)
- **D-01:** Desktop layout: left-right split view (map left, timeline right). No drag resize — fixed 50/50 split.
- **D-02:** Mobile layout: stacked — map on top (40vh), timeline below. Tab-style day selector still on map.
- **D-03:** Day route selector: pill-shaped buttons above the map ("Day 1" / "Day 2" / "Day 3"). Clicking switches the day's route display and auto-zooms to fit that day's POIs. Active day highlighted with its route color.

### Map Markers & Routes (MAP-01, MAP-03)
- **D-04:** POI markers: Custom HTML markers using AMap.Marker `content` property. Each marker renders a div with the POI's tier symbol (★/○/◇) and tier color (gold/silver/bronze from Phase 9 CSS vars). Visual consistency with POINode tier badges.
- **D-05:** Walking routes between consecutive POIs: dashed polylines (虚线连接). No Amap route API call — straight lines between consecutive POIs using AMap.Polyline with `strokeDasharray` property. Lightweight, no additional API cost.
- **D-06:** Day route colors: Day 1 blue (#3B82F6), Day 2 green (#10B981), Day 3 orange (#F59E0B). Add `--color-day-1`, `--color-day-2`, `--color-day-3` CSS custom properties in tailwind.css. **Color conflict resolution:** Change data source attribution colors in tailwind.css to avoid overlap — `--color-source-amap` changes from #3B82F6 to a softer teal like #6BA3D6, keeping warm feel while visually distinct from day-route blue.
- **D-07:** Map auto-zoom: When a day is selected, map fits all that day's POI markers in viewport with padding.

### Map-Timeline Sync (MAP-02)
- **D-08:** Click POI in timeline → map pans to center on corresponding marker + marker shows AMap infoWindow with POI name. Timeline POI gets highlighted state.
- **D-09:** Click map marker → corresponding timeline POI card expands and scrolls into view. Requires adding a `highlightPoiId` prop to ItineraryTimeline → DaySection → POINode so the map can trigger expansion externally. Current ItineraryTimeline uses internal `expandedPoiId` — needs to also accept external input.

### Data Model Changes (Critical Dependency)
- **D-13:** POIVisitData (frontend `src/frontend/src/types/itinerary.ts`) and POIVisit (backend `src/backend/models/pydantic.py`) MUST be extended with optional `latitude?: number` and `longitude?: number` fields. Without coordinates, map markers cannot be placed.
- **D-14:** Coordinate enrichment strategy: Enrich on retrieval, not on storage. Modify the backend GET `/api/itineraries/{id}` endpoint to parse `parsed_itinerary` JSON, then for each POI with a `poi_id`, look up coordinates from the `pois` database table and inject them. This avoids changing the pipeline and works for old itineraries. POIs without a DB match (AI-generated) will lack coordinates — skip them on the map.
- **D-15:** Amap JS API key injection: Add a public `GET /api/config/amap-key` endpoint (no auth required) that returns the JS API key. Frontend fetches this before loading the map. Key is the same `AMAP_API_KEY` from backend config. This is safe — JS API keys are domain-restricted, not secret.

### Sharing (SHARE-01, SHARE-02)
- **D-10:** Share button: positioned next to itinerary title in ItineraryView header. Uses Naive UI NButton with "分享" label + link icon.
- **D-11:** Click behavior: copies `/itinerary/{id}` URL to clipboard using `navigator.clipboard.writeText()`. Shows Naive UI useMessage success toast "链接已复制".
- **D-12:** OG meta tags: Backend adds GET `/api/itineraries/{id}/meta` endpoint returning `{ title, description, city }`. Frontend dynamically sets `document.title` and `<meta og:title>`, `<meta og:description>` tags on page load. Note: WeChat/Weibo crawlers may not execute JS — full SSR is out of scope; this gives best-effort previews for link unfurling.

### the agent's Discretion
- Exact marker HTML/CSS design (size, shadow, animation)
- InfoWindow content and styling
- Polyline dash pattern (gap length, color opacity)
- Mobile breakpoint exact values
- Map initial zoom level and center calculation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 9 Decisions (color reservation)
- `.planning/phases/09-ui-redesign-rich-display/09-CONTEXT.md` — D-01 reserves #3B82F6/#10B981/#F59E0B for Phase 10 map day-route colors; D-05 defines tier badge symbols ★/○/◇

### Requirements
- `.planning/REQUIREMENTS.md` §Map & Visualization — MAP-01 through MAP-04 specs
- `.planning/REQUIREMENTS.md` §Sharing — SHARE-01, SHARE-02 specs

### Existing Code
- `src/frontend/src/views/ItineraryView.vue` — Current itinerary display (363 lines), will integrate map
- `src/frontend/src/stores/itinerary.ts` — Store with itinerary data, SSE streaming (351 lines)
- `src/frontend/src/types/itinerary.ts` — POIVisitData, DayData, ItineraryData interfaces
- `src/frontend/src/tailwind.css` — CSS custom properties including day-route color vars (to be added)
- `src/frontend/src/components/ItineraryTimeline.vue` — Timeline wrapper component
- `src/frontend/src/components/DaySection.vue` — Per-day section rendering
- `src/frontend/src/components/POINode.vue` — Individual POI card (386 lines, has expand/collapse, preview mode)
- `src/frontend/src/App.vue` — Root with NConfigProvider

### Package Dependency
- `src/frontend/package.json` — `@amap/amap-jsapi-loader: 1.0.1` already installed

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `@amap/amap-jsapi-loader`: Already in package.json (version 1.0.1). Loads Amap JS API v2. Use `AMapLoader.load({ key: 'YOUR_KEY', version: '2.0' })`.
- POIVisitData interface: Has `poi_id`, `time_slot`, `name`, `vibe_description`, `highlight_note`, `walk_to_next_minutes`, `tier`. **CRITICAL GAP:** Lacks `latitude`/`longitude` — must be added (D-13). Coordinates come from backend POI table enrichment (D-14).
- DayData interface: Has `day_number`, `theme`, `pois[]` — needed for day-based route display.
- ItineraryData interface: Has `title`, `summary`, `days[]` — title/summary for OG meta.
- CSS custom property system: All colors use `var(--color-*)` in tailwind.css @theme. Day-route colors need to be added as `--color-day-1/2/3`.

### Established Patterns
- Naive UI components: NButton, NMessage (useMessage for toast), NResult — all already used.
- CSS custom properties: All colors defined in `tailwind.css` @theme, referenced via `var(--color-*)`.
- Pinia stores: `useItineraryStore` manages itinerary data, SSE, generation state.
- Vue 3 Composition API with `<script setup lang="ts">`.
- Responsive: 768px breakpoint used in existing components.

### Integration Points
- ItineraryView.vue: Main view where map will be added. Currently shows timeline only (max-width 720px). Map component inserts alongside timeline — requires layout restructuring to flex/grid split view.
- ItineraryTimeline.vue: Emits `@toggle` and `@action` events — map sync needs to listen to expand/collapse state. **Currently lacks external expansion control** — needs new `highlightPoiId` prop for D-09 map→timeline sync.
- DaySection.vue: Knows which POI is expanded (`expandedId`) — must also react to external highlight requests from the map.
- Backend `/api/itineraries/{id}`: Returns itinerary data. Must be modified to enrich POI coordinates (D-14). New `/api/itineraries/{id}/meta` endpoint needed for OG tags (D-12). New `/api/config/amap-key` endpoint for JS API key (D-15).
- POINode.vue: Emits `@toggle` when clicked — map can listen via event chain (POINode → DaySection → ItineraryTimeline → ItineraryView → Map).
- Backend `AMAP_API_KEY`: Already configured in `src/backend/config.py` line 15. Used for POI search. Same key can be exposed for JS API (domain-restricted, not secret).

### Key Technical Notes
- Amap JS API requires an API key. Backend already has `AMAP_API_KEY` in config (used for POI search). Frontend needs its own JS API key (can be the same key with JS API permissions enabled).
- AMap.Marker `content` property accepts HTML string for custom markers.
- AMap.Polyline supports dashed lines via `strokeDasharray` property (array of numbers, e.g., `[10, 5]`). `strokeStyle: 'dashed'` is NOT a valid AMap Polyline property.
- AMap.InfoWindow for popup on marker click.
- Map container needs explicit height — in split view, use CSS flex or grid to allocate space.
- Multiple polylines needed: one per day, each with its day's color.

### Edge Cases
- Day with zero POIs: No route rendered for that day. Day selector still shows it but map shows empty state.
- Itinerary with 1 day: Day selector hidden (only one option, redundant). Show all POIs.
- POIs without coordinates (AI-generated or old itineraries): Skip on map, show timeline only. No marker, no polyline segment.
- Day selector initial state: Defaults to Day 1 on load.

</code_context>

<specifics>
## Specific Ideas

- Map-timeline sync feels like Google Maps list view — click a place in the list, map jumps to it
- Day selector pills above map should match warm UI style (sand background, coral active)
- Share toast should be warm/encouraging tone: "链接已复制，分享给朋友吧！"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-map-sharing*
*Context gathered: 2026-04-17*
