# Feature Research

**Domain:** AI-powered travel itinerary generation (Chinese market focus)
**Researched:** 2026-04-15
**Confidence:** MEDIUM (Chinese competitor data based on training knowledge + partial web verification; Western competitors verified via official sites)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any AI itinerary product. Missing these = product feels broken or incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Natural language input | ChatGPT normalized conversational AI — users won't fill long forms | LOW | Plain text → structured intent extraction (destination, dates, budget, interests) |
| Day-by-day itinerary output | Core value prop of the category — must produce structured day plans | MEDIUM | Time-sequenced nodes with name, type, duration, location, description |
| POI data with basic info | Users expect place names, photos, ratings, hours | MEDIUM | Tier B/C data from Amap API; photos from Amap POI detail |
| Route/time validation | If route is impossible (3h drive in 30min), trust is destroyed | MEDIUM | Amap directions API for travel time between nodes |
| Budget awareness | Users specify budget ranges and expect recommendations to respect them | LOW | LLM prompt constraint + post-generation filter |
| Interest/style preferences | Minimum: foodie/culture/nature/shopping/nightlife tags | LOW | Tag-based pre-filtering of POI candidates |
| Edit/adjust after generation | No first draft is perfect — must allow refinement | MEDIUM | Dialog-based adjustment: swap/add/remove nodes, re-balance days |
| Mobile-responsive web | Target demographic (18-35) primarily uses phones | LOW | CSS responsive design; not a native app |
| Save/load itineraries | Users expect to return to their generated trips | LOW | JWT auth + SQLite storage |
| Chinese language UI | Target market is Chinese users | LOW | All UI copy in Simplified Chinese |

### Differentiators (Competitive Advantage)

Features that set 拾途 apart from competitors. These align with the core value: **curated taste data + LLM narrative personality**.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **SOUL narrative voice** ("本地朋友" tone) | This IS the product — warm, opinionated, personal descriptions vs. encyclopedia-style summaries. The emotional differentiator. | MEDIUM | SOUL prompt engineering + golden examples. Phase 0 blocking prerequisite: ≥60% blind test preference. |
| **Curated taste database** (3-tier POI) | Not "all restaurants" but "restaurants worth your time" — quality over quantity. Tier A (10-15 hand-picked) get rich narrative treatment. | HIGH | Manual curation ~30min/city for Tier A; LLM batch-labeling for Tier B; Amap raw for Tier C. Unique data asset. |
| **Taste-tag scoring** (D1/D3/D7 dimensions) | Quantified taste profile per POI enables matching to user preferences beyond simple category filters. D1 (ambiance), D3 (taste level), D7 (surprise factor). | MEDIUM | Scored during data pipeline; used in Stage 2 pre-filtering. Post-MVP expands to D1-D8. |
| **Emotional pacing** in itineraries | Not just "efficient route" but rhythm — quiet morning → energetic afternoon → cozy evening. Feels human-planned. | MEDIUM | LLM prompt instruction + SOUL. No competitor does this. Hard to replicate without taste data. |
| **SSE streaming progress** (4-stage pipeline visibility) | 30-60s generation feels alive, not frozen. Shows "正在理解你的需求 → 正在挑选好地方 → 正在规划行程 → 正在优化路线". | LOW | FastAPI SSE; 4 explicit progress stages. Trust builder during wait. |
| **A/B comparison-free positioning** | Don't compete on features — compete on feeling. Deliberately minimal UI, warm visual design, no booking clutter. | LOW | Product strategy decision, not code. Sand/seafoam/shell-pink palette, card UI, handwriting accents. |
| **Highlight notes per POI** (recommend理由) | "Why this place?" answered in friend-voice, not Wikipedia voice. "这家店的咖啡是自己烘的，老板以前做摄影" vs. "评分4.5的咖啡馆". | LOW | Stored in taste DB (highlight_note field). SOUL prompt differentiates by tier. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem appealing but would undermine the product's core identity or stretch MVP beyond viability.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Embedded map/navigation** | Users want to see where things are and get directions | Massive dev effort; Amap/Mapbox SDK integration; users already have 地图 app; shifts focus from "discover" to "navigate" | Time-axis visualization only; link out to Amap for navigation |
| **Booking integration** (hotels/flights/tickets) | Revenue opportunity; one-stop-shop appeal | Transforms product into OTA platform (携程 territory); enormous API integration; compliance/licensing; kills the "local friend" vibe with transactional UX | Provide deep links to booking platforms; stay in recommendation layer |
| **Multi-city/cross-city trips** | Real travelers visit multiple cities | Multiplier on route complexity; breaks the "single city depth" positioning; dilutes POI quality across cities | MVP: single city only. Post-MVP: sequential single-city itineraries (not a routing problem) |
| **Social sharing** (朋友圈/小红书) | Growth through virality; users want to share cool trips | Adds social graph complexity; invites comparison/review culture; shifts from "personal friend" to "performative content" brand | Post-MVP: simple image export card, not social platform |
| **UGC/reviews from users** | Community content = scale; everyone loves "real reviews" | Content moderation nightmare; quality dilution; competing with 大众点评; data compliance risk (爬取点评内容) | Expert curation (Tier A) + LLM labeling (Tier B) — quality over quantity |
| **Real-time pricing/comparison** | Users want to know costs | Fragile API dependencies; price data ages fast; shifts value prop from "discovery" to "shopping" | Budget bands in POI data (¥/¥¥/¥¥¥); link out for current prices |
| **Itinerary marketplace/templates** | "Popular itineraries" for inspiration | Undermines personalization; one-size-fits-all is the problem we're solving; template library = maintenance burden | Each itinerary is AI-generated for the individual; no templates |
| **Fine-tuned LLM model** | Better quality = competitive moat, right? | Expensive to train/maintain; brittle; single-model dependency; hard to iterate | SOUL prompts + structured data = controllable quality without model training. Faster iteration loop. |
| **WeChat Mini Program** | Chinese users live in WeChat | WeChat dev tools are separate ecosystem; doubles frontend work; WeChat review process; premature distribution optimization | Web first (mobile-responsive). Post-product-market-fit: migrate to 小程序. |

## Feature Dependencies

```
[Natural Language Input]
    └──requires──> [Intent Extraction LLM (Stage 1)]
                        └──requires──> [POI Database (Tier B/C)]
                                            └──requires──> [Amap Data Pipeline]

[SOUL Narrative Voice]
    └──requires──> [Taste Database (Tier A curation)]
    └──requires──> [SOUL Prompt Engineering (Phase 0 validation)]

[Day-by-Day Itinerary]
    └──requires──> [Intent Extraction LLM (Stage 1)]
    └──requires──> [POI Pre-filtering (Stage 2)]
    └──requires──> [Route Generation LLM+SOUL (Stage 3)]
    └──requires──> [Route Validation (Stage 4)]

[Edit/Adjust Itinerary]
    └──requires──> [Day-by-Day Itinerary] (must exist to edit)
    └──requires──> [SSE Streaming Progress] (for adjustment preview)

[Save/Load Itineraries]
    └──requires──> [JWT Authentication]
    └──requires──> [Day-by-Day Itinerary]

[Emotional Pacing]
    └──enhances──> [SOUL Narrative Voice] (same prompt system)
    └──requires──> [Taste-tag Scoring (D1/D3/D7)]

[SSE Streaming Progress]
    └──requires──> [4-Stage Pipeline Architecture]
    └──enhances──> [User Trust During Long Generation]

[Taste-tag Scoring]
    └──enhances──> [POI Pre-filtering (Stage 2)] (better candidate selection)
    └──conflicts──> [Simple Category Filters] (replaces, not supplements)

[Booking Integration] ──conflicts──> [SOUL Narrative Voice] (transactional kills warmth)
[Embedded Map] ──conflicts──> [Minimal UI Philosophy] (visual clutter)
[UGC Reviews] ──conflicts──> [Curated Quality] (dilutes Tier A exclusivity)
```

### Dependency Notes

- **Intent Extraction requires POI Database:** Can't recommend places without place data. Data pipeline is foundational.
- **SOUL Narrative requires both Taste DB and SOUL Prompts:** The moat is data + prompt coupling, not either alone.
- **Edit/Adjust requires completed itinerary + SSE:** Must have something to edit, and adjustments need the same streaming UX for trust.
- **Emotional Pacing enhances SOUL Narrative:** Same prompt system controls both; they're deeply intertwined.
- **Booking conflicts with SOUL Voice:** Every OTA comparison study shows that adding booking shifts user mode from "exploration" to "optimization" — kills the emotional experience.
- **UGC conflicts with Curated Quality:** The entire point of Tier A is editorial judgment. User reviews make every place a 3.5-star blur.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the core hypothesis: **curated taste + SOUL narrative > standard AI itinerary**.

- [x] **Phase 0: SOUL Prompt Validation** — Blind test ≥60% preference. BLOCKING — don't build anything else until this passes.
- [ ] **Natural language input** → structured intent extraction — This is the entry point for all users.
- [ ] **3-tier POI database** (1-2 cities, Amap pipeline) — Without data, there's nothing to recommend.
- [ ] **4-stage generation pipeline** (intent → pre-filter → LLM+SOUL → validation) — Core engine.
- [ ] **Day-by-day itinerary output** (timeline visualization) — The deliverable users see.
- [ ] **SOUL narrative voice** on all POI descriptions — THE differentiator. Must feel different from ChatGPT travel prompts.
- [ ] **SSE streaming progress** (4 stages visible) — 30-60s is too long for a blank screen.
- [ ] **Edit/adjust via dialog** (swap/add/remove nodes) — First drafts are never perfect.
- [ ] **Save/load itineraries** (simple auth) — Users need to come back to their plans.
- [ ] **Minimal feedback mechanism** ("推荐准不准?" 准/一般/不准) — Data flywheel starts here.
- [ ] **Mobile-responsive web** (card-based UI, natural color palette) — Target demographic is mobile-first.

### Add After Validation (v1.x)

Features to add once core loop works and users return.

- [ ] **Taste-tag scoring refinement** (use feedback data to improve D1/D3/D7 accuracy) — Trigger: 500+ feedback signals collected
- [ ] **User taste profile building** (from saved trips and feedback, build per-user preference model) — Trigger: users generating 3+ trips
- [ ] **Additional cities** (expand beyond MVP 1-2) — Trigger: SOUL validation proven in first cities
- [ ] **Itinerary sharing card** (beautiful image export, not social platform) — Trigger: users asking "can I share this?"
- [ ] **Weather awareness** (adjust outdoor plans for rain) — Trigger: user complaints about rain-ruined plans
- [ ] **Time-of-day sensitivity** (morning markets vs. nightlife, seasonal hours) — Trigger: feedback about "it was closed"

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **WeChat Mini Program** — Validate on web first; WeChat is distribution, not product.
- [ ] **Multi-city itinerary chaining** — Requires solving a fundamentally different routing problem.
- [ ] **Group trip planning** — Social complexity; needs user base first.
- [ ] **Community-shared itineraries** (curated, not open UGC) — Needs enough quality content to curate.
- [ ] **Full 8-dimension scoring** (D1-D8) — MVP ships with D1/D3/D7; others require more data.
- [ ] **Real-time POI status** (closed/temporary/popularity spikes) — Needs monitoring infrastructure.
- [ ] **Offline access** — PWA consideration for travelers without reliable data.
- [ ] **WeChat login integration** — Lower friction for Chinese users, but adds platform dependency.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| SOUL prompt validation (Phase 0) | CRITICAL | LOW (prompt engineering only) | P0-BLOCKING |
| Natural language input | HIGH | LOW | P1 |
| 3-tier POI data pipeline | HIGH | MEDIUM | P1 |
| 4-stage generation pipeline | HIGH | HIGH | P1 |
| Day-by-day timeline output | HIGH | MEDIUM | P1 |
| SOUL narrative on POI descriptions | HIGH | LOW (prompt + data) | P1 |
| SSE streaming progress | MEDIUM | LOW | P1 |
| Edit/adjust via dialog | HIGH | MEDIUM | P1 |
| Save/load itineraries | MEDIUM | LOW | P1 |
| Mobile-responsive UI | HIGH | LOW | P1 |
| Minimal feedback ("准不准?") | MEDIUM | LOW | P1 |
| Taste-tag scoring (D1/D3/D7) | MEDIUM | MEDIUM | P2 |
| User taste profile | MEDIUM | MEDIUM | P2 |
| Additional cities | HIGH (growth) | MEDIUM | P2 |
| Sharing card export | LOW | LOW | P2 |
| Weather awareness | LOW | LOW | P2 |
| WeChat Mini Program | MEDIUM (distribution) | HIGH | P3 |
| Multi-city trips | MEDIUM | HIGH | P3 |
| Group planning | LOW | HIGH | P3 |
| Community itineraries | LOW | HIGH | P3 |

**Priority key:**
- P0-BLOCKING: Must validate before building anything
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Layla.ai (Western) | Wanderlog (Western) | 携程AI Trip Planner (Chinese) | 穷游 行程助手 (Chinese) | 拾途 Our Approach |
|---------|---------------------|---------------------|-------------------------------|--------------------------|-------------------|
| **Input method** | Form + chat | Form + map pins | Chat (自然语言) | Manual drag-and-drop | Chat (自然语言, conversational) |
| **AI generation** | Full AI itineraries | AI suggestions (Pro only) | Full AI itineraries | None (manual tool) | Full AI + SOUL narrative |
| **Narrative personality** | Neutral/factual | Neutral/factual | Neutral/factual | N/A | "本地朋友" warm voice ★ |
| **Taste curation** | None (algorithmic) | None (user-driven) | None (popularity-based) | None (user-driven) | 3-tier curated taste DB ★ |
| **POI depth** | Standard descriptions | Auto-populated from Google | Standard POI data | User-generated guides | Tier A: curated stories; Tier B: LLM-labeled; Tier C: raw |
| **Emotional pacing** | None (efficient routing) | None | None | None | Rhythm-aware day planning ★ |
| **Booking integration** | Full (Skyscanner/Booking.com) | Hotel search (Pro) | Full OTA stack | Hotel/insurance/visa | None — link out only |
| **Map view** | Yes | Yes (killer feature) | Yes | Yes | No — timeline only (MVP) |
| **Route optimization** | AI-powered | Pro feature | Yes | Manual | Amap validation (Stage 4) |
| **Collaboration** | Group planning | Group collaboration | Limited | None | None (MVP) |
| **Community/shared trips** | Trip library | Shared guides | User reviews | UGC community | None (anti-feature) |
| **Chinese market focus** | No | No | Yes (primary) | Yes (primary) | Yes (exclusive) ★ |
| **Pricing** | Free + $49/yr | Free + ~$50/yr | Free (OTA monetized) | Free (OTA monetized) | TBD (data/experience moat) |

★ = 拾途 unique differentiator

### Competitor Insights (Training Knowledge + Partial Verification)

**携程 (Ctrip/Trip.com) AI Planner** — MEDIUM confidence:
- Integrated into main 携程 app as a chat feature
- Uses LLM to generate itineraries but output is functional/transactional
- Monetizes through booking commissions, not itinerary quality
- Massive POI database but popularity-based, not taste-based
- Advantage: scale, data, booking ecosystem. Weakness: no personality, no "hidden gems" curation

**飞猪 (Fliggy/Alibaba) AI** — LOW confidence (training knowledge only):
- Alibaba's travel platform with AI planning features
- Integrated with Alibaba ecosystem (支付宝, 芝麻信用)
- Similar to 携程 in approach: functional AI, booking-driven monetization
- Likely uses Tongyi/Qwen models internally

**马蜂窝 (Mafengwo)** — MEDIUM confidence:
- UGC travel content platform with strong community
- Travel guides (攻略) are the core product, not AI generation
- Has been exploring AI features but core value is still user-written content
- Direct competitor to 穷游 in the UGC travel content space
- Weakness: content quality varies wildly, no taste curation

**Key competitive insight:** Chinese market AI travel tools (携程, 飞猪) compete on booking comprehensiveness and data scale. No one is competing on **taste curation and narrative personality**. This is 拾途's gap.

## Sources

- **Wanderlog** — Official site features page (HIGH confidence, directly fetched)
- **Layla.ai** — Official site + tripplanner.ai redirect verification (HIGH confidence, directly fetched)
- **TripIt** — Official site features page (HIGH confidence, directly fetched)
- **穷游 (Qyer)** — Official site (MEDIUM confidence, directly fetched)
- **携程AI, 飞猪AI, 马蜂窝** — Training knowledge only (LOW-MEDIUM confidence, could not verify via web due to Chinese site access restrictions)
- **Project documents** — PROJECT.md, detailed requirements doc (HIGH confidence, primary source)
- **Sygic Travel** — Official site (MEDIUM confidence, directly fetched)

---
*Feature research for: AI-powered travel itinerary generation (Chinese market focus)*
*Researched: 2026-04-15*
