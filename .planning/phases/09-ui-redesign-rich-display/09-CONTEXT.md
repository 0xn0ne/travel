# Phase 9: UI Redesign & Rich Display - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning (revised after 3-agent audit)

<domain>
## Phase Boundary

Visual overhaul of the **entire** frontend — transform the current functional green/white interface into a warm, journey-themed experience. Covers color palette, POI card richness, data source attribution, generation loading animation, and home page hero redesign.

Scope: UI-01 through UI-05 (frontend display layer). Backend data gaps handled with frontend derivations/placeholders — backend enrichment deferred.

**Important:** The warm palette applies to ALL pages, not just HomeView/ItineraryView. Phase 8 pages (AuthModal, Settings, ItineraryList, AppHeader) must also receive warm color treatment.

</domain>

<decisions>
## Implementation Decisions

### Color & Warmth (UI-01)
- **D-01:** Color palette: Sand (#F5E6D3) base, Coral (#FF6B6B) accent, Ocean Teal (#4ECDC4) for links/secondary. Replace all current green (#18a058) branding with warm tones. **Phase 10 color reservation:** Do NOT use pure blue (#3B82F6), green (#10B981), or orange (#F59E0B) as UI accents — these are reserved for map day-route colors in Phase 10.
- **D-02:** Card visual style: Soft shadow (16px border-radius), hover lift effect with deepened shadow. Airbnb/Monocle card feel.
- **D-03:** Color application through THREE channels: (1) NConfigProvider `:theme-overrides` prop for Naive UI component internals (currently bare in App.vue, needs binding), (2) Tailwind `@theme` directive in tailwind.css for CSS custom properties (`--color-sand`, `--color-coral`, etc.), (3) Component scoped CSS for specific effects (shadows, gradients, hover). **All color values MUST use CSS custom properties — no hardcoded hex values.** This enables future dark mode support without component-level changes.
- **D-03b:** Planner MUST invoke `ui-ux-pro-max` skill (`--design-system` with keywords "travel lifestyle warm journey", `--stack vue`) to generate a design system foundation before planning component changes. UI-01 explicitly requires this skill.

### POI Rich Display (UI-02 + UI-03)
- **D-04:** POI detail display mode: Keep current expandable pattern (click to expand). Summary shows name + tier + time slot; expanded view shows highlight_note, vibe_description, walk_to_next_minutes.
- **D-05:** Tier badge redesign: ★ Tier A (gold), ○ Tier B (silver), ◇ Tier C (bronze). Note: Current POINode.vue only handles tier 1 and 2 — tier 3 (· middle dot was considered but rejected as too small/invisible on mobile) needs explicit handling.
- **D-06:** Data source attribution (UI-03): Inline tag with icon next to POI name — ★ "人工精选" (gold tag for Tier A), 📍 "高德地图" (blue tag for Tier B), ✨ "AI推荐" (purple tag for Tier C). Use SVG icons (not emoji) per ui-ux-pro-max guidelines.
- **D-07:** `opening_hours` field: Frontend placeholder "暂无营业时间". The `opening_hours` column already exists in the DB POI model but the pipeline doesn't pass it to frontend `POIVisitData`. Pipeline passthrough is deferred — this phase shows placeholder only.
- **D-08:** Data source derivation: **Priority chain logic** — 1) If `tier === 1` → "人工精选". 2) If `tier === 2` → "高德地图". 3) Otherwise → "AI推荐". This is a simplified tier-only mapping since the frontend `POIVisitData` interface has no `amap_id` field. Documented as simplification until backend outputs explicit `data_source`.

### Generation Loading (UI-04)
- **D-09:** Loading experience: Warm gradient progress bar with travel-themed stage messages. Replace current 5-dot StageProgress with a warm progress bar component.
- **D-10:** Stage messages contextual (include city name when available), journey imagery language. Example progression: "理解你的旅行心愿..." → "在{city}寻找有趣的地方..." → "精心编排你的行程..." → "确保路线顺畅..." → "你的旅程准备好了！"

### Home Page Hero (UI-05)
- **D-11:** Hero section: Full-width gradient background (sand → ocean), title + subtitle, 3-4 clickable "journey cards" below. Each card has icon + short description. Responsive: 4-column desktop, 2-column tablet, stacked mobile (< 640px).
- **D-12:** Journey cards replace current NTag examples. Cards feel like mini travel invitations.
- **D-13:** Input area: Keep textarea but restyle with warm border/background. Generate button uses coral accent color.

### Global Warm Treatment
- **D-15:** ALL existing pages/components receive warm palette color updates via CSS custom properties. No structural changes to auth/settings pages — only color swaps. Applies to: AppHeader.vue, AuthModal.vue, SettingsView.vue, ItineraryListView.vue, FeedbackWidget.vue, ItineraryView.vue.
- **D-16:** Error states: NAlert theme overridden to warm amber (not default Naive UI amber). Error text uses Coral accent.
- **D-17:** Empty states: Centered text with Ocean Teal icon, warm background.
- **D-18:** Loading/skeleton states: Naive UI NSkeleton uses sand-to-warm-gray color. NSpin uses Coral accent.
- **D-19:** BlindTestView.vue is EXCLUDED from redesign — development tool only.

### the agent's Discretion
- Exact gradient angles/stops for hero background
- Journey card icon SVG selection (subject to ui-ux-pro-max guidelines)
- Exact shadow pixel values for card depth
- Progress bar animation timing/easing
- Transition animations between states

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` § UI Redesign (UI-01 through UI-05) — acceptance criteria for each UI requirement
- `.planning/ROADMAP.md` § Phase 9 — success criteria and phase boundary

### Skill (MUST invoke)
- `.opencode/skills/ui-ux-pro-max/SKILL.md` — UI-01 explicitly requires ui-ux-pro-max skill. Use `--design-system` with "travel lifestyle warm journey" and `--stack vue` for design foundation.

### Existing Frontend to Modify (Primary — structural changes)
- `src/frontend/src/components/POINode.vue` — POI card visual overhaul + expandable detail enrichment
- `src/frontend/src/components/StageProgress.vue` — replace 5-dot progress with warm progress bar
- `src/frontend/src/views/HomeView.vue` — redesign hero + journey cards
- `src/frontend/src/components/DaySection.vue` — day header warm styling
- `src/frontend/src/components/ItineraryTimeline.vue` — timeline container warm styling
- `src/frontend/src/App.vue` — add NConfigProvider `:theme-overrides` binding
- `src/frontend/src/tailwind.css` — add `@theme` with warm palette CSS custom properties

### Existing Frontend to Update (Color-only — no structural changes)
- `src/frontend/src/components/AppHeader.vue` — replace hardcoded colors with CSS vars
- `src/frontend/src/components/AuthModal.vue` — inherits Naive UI theme overrides
- `src/frontend/src/components/FeedbackWidget.vue` — replace hardcoded colors with CSS vars
- `src/frontend/src/views/ItineraryView.vue` — replace hardcoded colors with CSS vars
- `src/frontend/src/views/SettingsView.vue` — inherits Naive UI theme overrides
- `src/frontend/src/views/ItineraryListView.vue` — replace hardcoded colors with CSS vars

### Data Models
- `src/frontend/src/types/itinerary.ts` — POIVisitData, DayData, ItineraryData interfaces (no type changes this phase)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Naive UI components**: Already used throughout — NCard, NTag, NButton, NInput, NSpace, NAlert, NModal, NRadio, NGrid, etc. Redesign continues using these with theme overrides.
- **NConfigProvider**: Already in App.vue but BARE (no `:theme-overrides` prop). Needs binding from scratch.
- **Tailwind CSS 4**: CSS-first config — add custom colors via `@theme` directive in tailwind.css.
- **Pinia stores**: useItineraryStore (generation state, SSE), useAuthStore (auth state) — no changes needed.

### Established Patterns
- **POI expandable card**: POINode.vue has expand/collapse with `<Transition>` — keep, enrich expanded view.
- **Scoped CSS**: All components use `<style scoped>`. Maintain this pattern.
- **Color usage**: Currently hardcoded hex values (#18a058, #ed8936, etc.) — ALL must be replaced with CSS custom properties.

### Integration Points
- **NConfigProvider theme overrides**: Primary for Naive UI component internals. Must create override object and bind via `:theme-overrides`.
- **tailwind.css @theme**: Defines `--color-sand`, `--color-coral`, `--color-ocean` etc. for all custom CSS to reference.
- **POIVisitData interface**: No changes. `opening_hours` = placeholder, `data_source` = derived from tier.
- **StageProgress**: Same 5 stage keys (intent/prefilter/generation/validation/complete), same props (currentStage, message). Only template/styles change.

### Key Technical Notes
- Current codebase has NO Tier C badge handling (POINode.vue only checks tier 1 and 2) — tier 3 support is additive.
- `opening_hours` column exists in DB POI model but pipeline doesn't pass it through — this phase uses placeholder only.
- NConfigProvider `theme-overrides` structure: `common.primaryColor`, `common.primaryColorHover`, etc. See Naive UI docs.

</code_context>

<specifics>
## Specific Ideas

- Journey card examples: "文艺漫步" (Shanghai 2-day artsy), "浪漫之旅" (romantic 3-day), "美食探店" (food walk), "独行探险" (solo exploration)
- Warm progress bar messages: "理解你的旅行心愿..." → "在{city}寻找有趣的地方..." → "精心编排你的行程..." → "确保路线顺畅..." → "你的旅程准备好了！"
- Card hover: translateY(-4px) + box-shadow deepened, 0.2s transition
- CSS custom property names: `--color-sand`, `--color-coral`, `--color-ocean`, `--color-sand-light`, `--color-coral-light`, `--color-ocean-light`, `--color-text-primary`, `--color-text-secondary`, `--color-bg`, `--color-card`, `--color-card-shadow`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-ui-redesign-rich-display*
*Context gathered: 2026-04-17*
*Revised: 2026-04-17 — 3-agent audit (4 CRITICAL, 5 WARNING fixed)*
