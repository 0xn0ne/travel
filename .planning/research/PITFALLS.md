# Pitfalls Research

**Domain:** AI-powered travel itinerary generation (品味行程生成器)
**Researched:** 2026-04-15
**Confidence:** MEDIUM

*Note: This research synthesizes domain knowledge about LLM-powered travel systems, publicly documented failure cases from comparable products, and API documentation analysis. Web search verification was limited (external search tools unavailable during research), so certain findings carry uncertainty and should be validated during Phase 1 development.*

## Critical Pitfalls

### Pitfall 1: LLM Fabricates Non-Existent Venues

**What goes wrong:**
The LLM generates itineraries referencing restaurants, shops, or attractions that don't exist or are permanently closed. A user arrives at "藏CANG" a trendy杭州咖啡店 at the address the itinerary provides, only to find an empty lot or an entirely different business.

**Why it happens:**
- DeepSeek-V3 (like all LLMs) hallucinates when asked to name specific venues in response to location queries
- The model confuses similar-sounding names, real venues from other cities, or entirely fictional establishments
- The 12K token generation context makes hallucinations more likely as the model "fills in details" for venues it cannot verify
- No ground-truth database is consulted during LLM text generation — the model produces fluent text that sounds authoritative

**How to avoid:**
1. **Never let the LLM generate venue names independently** — Stage 2 (data pre-screening) must supply concrete POI records, and Stage 3 must only select from those records
2. **Enforce strict output schema validation** — itinerary nodes must reference POI IDs from the database, not free-text names
3. **Include venue ID + name + address in the system prompt** as structured constraints, not in the LLM's creative generation space
4. **Implement a "hallucination check"** — after LLM generates, verify every referenced POI ID exists in SQLite with matching name/address

**Warning signs:**
- LLM output contains detailed narrative descriptions of venues without corresponding POI records
- Generated itineraries include specific opening hours, dish names, or price points the LLM "invented"
- Users report "arriving at a place that doesn't exist" — this is a critical failure requiring immediate data investigation

**Phase to address:**
- **Phase 1 (System Integration)** — implement the hallucination check as part of Stage 4 (validation layer)
- **Phase 0 (Prompt Blind Test)** — if the SOUL prompt cannot reliably stick to real POI data, the entire approach needs rethinking

---

### Pitfall 2: POI Data Becomes Stale — Venues Close or Change Character

**What goes wrong:**
Cached POIs in SQLite reference businesses that have closed, changed names, undergone renovation, or had their rating/specialty completely altered. A "hidden gem" coffee shop in Tier B becomes a chain store six months later; the curated recommendation now embarrasses the product.

**Why it happens:**
- Amap POI data reflects a point-in-time snapshot; Chinese business turnover is high, especially for 网红店 (trending shops)
- No scheduled refresh mechanism for cached POI data
- Tier A/B curation work becomes outdated without maintenance pipeline

**How to avoid:**
1. **Add data freshness metadata** — store `poi_fetched_at`, `poi_verified_at` timestamps per POI
2. **Set TTL per tier** — Tier A (30 days), Tier B (14 days), Tier C (7 days) based on volatility of venue type
3. **Build a lightweight re-verification flow** — use Amap's `status` field or LLM spot-check to flag closed venues
4. **Plan for data maintenance sprint** — budget 1-2 hours per city per month for POI refresh

**Warning signs:**
- POI record has no `poi_verified_at` or it's >30 days old
- Amap returns `closed` status or the POI is un retrievable
- User feedback flags "这个店不存在了" (this venue no longer exists)

**Phase to address:**
- **Phase 1 (Data Pipeline)** — implement TTL enforcement and re-verification logic
- **Phase 2 (Operations)** — schedule recurring POI refresh tasks

---

### Pitfall 3: Amap Rate Limits Block Itinerary Generation Mid-Request

**What goes wrong:**
A user requests a 3-day itinerary; the system makes 20+ Amap API calls for POI search + route validation, hitting the 5000/month free quota within days of launch. Requests start returning `1002 RATE_LIMIT_EXCEEDED` errors, breaking the generation pipeline.

**Why it happens:**
- Free tier: 5000 Web API calls/month for search — not 5000/day, 5000/month total
- Each itinerary generation with full route validation (Stage 4) can consume 15-30+ API calls
- A single user requesting multiple itinerary variations can exhaust the quota for all users
- No request batching or caching strategy was designed

**How to avoid:**
1. **Cache aggressively at the data layer** — POI search results for identical queries should hit SQLite, not Amap
2. **Implement a request budget per user** — cap Amap calls per session (e.g., 50 calls/user/day)
3. **Batch route validation** — instead of validating each segment individually, batch into single polyline requests
4. **Plan for quota upgrade path** — track daily usage; set alert at 80% of monthly quota; budget for paid tier if successful
5. **Use extensions=base for POI search** (returns less data, may count as lighter API usage per their metering)

**Warning signs:**
- API responses include `1002` error code
- Daily usage dashboard shows >200 Amap API calls in a single day
- Multiple users reporting failed itinerary generation simultaneously

**Phase to address:**
- **Phase 1 (Infrastructure)** — implement caching layer and rate limiting before any user-facing launch
- **Phase 0 (Architecture)** — this should have been in the stack decisions; flag for immediate review

---

### Pitfall 4: Route Validation Passes but Produces Unwalkable Routes

**What goes wrong:**
Amap's walking route API returns `status: 1` (success) for a route, but the route includes highway crossings, private property, or assumes a pedestrian bridge that doesn't exist. Users follow the itinerary and end up on a highway on-ramp or locked courtyard.

**Why it happens:**
- Amap's routing algorithm prioritizes shortest distance, not pedestrian accessibility
- Certain areas (industrial zones, university campuses, gated communities) have complex access rules Amap doesn't model
- Time-of-day affects route viability (some pedestrian paths close at night)
- The 100K+ context window of DeepSeek-V3 doesn't help here — the problem is API data quality, not LLM capability

**How to avoid:**
1. **Cross-validate routes with multiple routing flags** — request walking + hiking/trail mode if available; compare paths
2. **Flag routes >2km between consecutive stops** for human review or user warning
3. **Store "route confidence" per segment** — if two routing modes disagree significantly, surface uncertainty to user
4. **Include a "navigation warning"** for segments >15 minutes walking between POIs
5. **Use real user feedback to iterate** — if users consistently report "hard to find" for certain POI pairs, deprioritize that route

**Warning signs:**
- Route includes segments >1.5km in dense urban areas (unusual — most walkable urban POIs are closer)
- User reports of dangerous or impossible pedestrian routes
- Amap returns walking time estimates inconsistent with Google/Apple Maps for same segment

**Phase to address:**
- **Phase 1 (Route Validation)** — implement multi-mode route comparison and confidence scoring

---

### Pitfall 5: "Taste Mode" Produces Generic Results That Sound Personalized

**What goes wrong:**
The SOUL prompt generates text with the right tone (casual, warm, 像本地朋友推荐) but the actual recommendations are the same 标准化景点 anyone would suggest — 30% of itineraries for 北京 include 故宫, even though the user said they want "not touristy" spots.

**Why it happens:**
- The 3-tier POI system (A/B/C) isn't properly stratified — Tier B/C content dominates because Tier A is too small
- LLM falls back to "what's famous" when taste_tags are vague or overlapping
- The SOUL prompt's personality overwhelms the taste data's signal — the model talks nicely but recommends boringly
- No diversity enforcement — the same high-traffic POIs get selected repeatedly because they score well on general appeal metrics

**How to avoid:**
1. **Enforce Tier A minimum inclusion** — every itinerary must include 40%+ Tier A POIs to maintain quality bar
2. **Make taste_tags more specific and binding** — instead of "文艺" (artistic), use granular tags like "独立书店|复古唱片店|小众艺术展"
3. **Add a "surprise me" diversity metric** — track POI repetition rate; if any POI appears in >20% of itineraries for a city, flag for review
4. **Test taste signal explicitly** in Phase 0 blind tests — not just "do you like the writing?" but "did we recommend something you wouldn't have found yourself?"

**Warning signs:**
- Itinerary content sounds warm but recommendations are identical to 大众点评 popular lists
- User feedback: "这些地方我自己也能找到" (I could have found these places myself)
- Tier A POI pool for a city has <50 entries — insufficient for diverse recommendations

**Phase to address:**
- **Phase 0 (Prompt Blind Test)** — validate that SOUL + taste data actually produces differentiated recommendations
- **Phase 1 (Data Stratification)** — ensure proper tier distribution in generation

---

### Pitfall 6: Chinese Character Encoding Breaks SQLite at Scale

**What goes wrong:**
Itineraries display correctly during MVP testing with a single city, but as POI records accumulate (200+ venues per city, 2 cities), SQLite starts returning garbled Chinese characters, or Python's `sqlite3` module throws `UnicodeDecodeError` during bulk operations.

**Why it happens:**
- SQLite's `text_factory` defaults to `str` in Python 3, which assumes UTF-8 but can fail if the database was initialized with different encoding assumptions
- Amap's API returns GB2312/GBK encoding in some error responses; mixing encodings corrupts stored data
- The `pysqlite3` library handles Unicode differently than the built-in `sqlite3`

**How to avoid:**
1. **Explicitly set `text_factory = str`** and open connections with `check_same_thread=False`
2. **Normalize all Amap API responses to UTF-8** before storing — Amap returns `info` messages in Chinese; ensure encoding consistency
3. **Use `PRAGMA encoding = UTF-8`** when creating the database
4. **Test with realistic Chinese data volume** before considering the MVP complete — insert 1000 Chinese-named POIs and verify retrieval

**Warning signs:**
- `UnicodeEncodeError` or `UnicodeDecodeError` in server logs during POI import
- Chinese place names appear as `\u5e7f\uf97f` or `???` in API responses
- Works with ASCII data but fails with full Chinese POI dataset

**Phase to address:**
- **Phase 1 (Database Setup)** — proper encoding configuration before any POI import

---

### Pitfall 7: SSE Stream Drops Mid-Generation, Leaving UI in Limbo

**What goes wrong:**
The frontend shows a spinning "generating itinerary..." indicator, but the SSE connection drops silently. The user waits 60+ seconds, sees nothing, and refreshes — potentially triggering a duplicate generation request that doubles API costs.

**Why it happens:**
- DeepSeek-V3 generation takes 30-60s for a full 12K context; SSE timeout defaults are often too short (e.g., 30s)
- Nginx/reverse proxy has default SSE timeout of 60s, killing long connections
- LLM token generation stalls without any keepalive ping
- Frontend doesn't have reconnection logic or status polling fallback

**How to avoid:**
1. **Set SSE timeout to 120s minimum** for the generation endpoint (DeepSeek-V3 is fast but not 30s fast for full itineraries)
2. **Send ping/pong events every 15s** during generation to keep connection alive
3. **Implement client-side reconnection** with exponential backoff
4. **Always emit a terminal event** (`[DONE]` or `generation_complete`) so the frontend can distinguish "still going" from "failed silently"
5. **Add generation_id tracking** to allow polling for status if SSE drops

**Warning signs:**
- Frontend logs show `EventSource connection closed` without a terminal message
- Users report "loading spinner that never ends"
- Backend logs show SSE write failures after 45-60s of generation

**Phase to address:**
- **Phase 1 (API Contract)** — implement ping events and timeout configuration
- **Phase 1 (Frontend)** — implement reconnection logic and terminal state handling

---

### Pitfall 8: Feedback Loop Captures Signal But Produces No Actionable Iterations

**What goes wrong:**
Users tap "不准" (inaccurate) on recommended venues, but the data is never fed back into the taste system. After 6 months, the product has 500 feedback records and no improvement in recommendation quality — the feedback button is cosmetic.

**Why it happens:**
- No pipeline exists to ingest user feedback and update POI taste_tags or tier classifications
- "不准" is too vague — doesn't capture *why* (wrong type? closed? not representative of the area?)
- No analytics dashboard to review feedback trends
- Product team never schedules a data review sprint

**How to avoid:**
1. **Design the feedback data model before launch** — capture not just vote but which dimension failed (location accuracy, taste match, open hours, etc.)
2. **Build a weekly digest** — automated report of low-rated POIs for human review
3. **Define an update threshold** — e.g., if >30% "不准" votes for a Tier B POI, demote to Tier C or flag for re-verification
4. **Close the loop** — tell users when feedback leads to changes ("We've removed X from recommendations based on your feedback")

**Warning signs:**
- Feedback database table grows but nobody reviews it
- Same POIs appear in low-rating reports month after month
- No mechanism to translate user votes into POI tier adjustments

**Phase to address:**
- **Phase 1 (Feedback System)** — design the feedback capture model as part of R15
- **Phase 2 (Iteration Pipeline)** — build the review and update workflow

---

### Pitfall 9: Phase 0 Blind Test Validates Writing Quality, Not Recommendation Quality

**What goes wrong:**
SOUL prompt gets 75% preference rate in blind tests, but the test only evaluated whether the *writing style* felt like a friend recommending. Nobody tested whether the *specific venues* were actually good — a charming friend can still recommend boring tourist traps.

**Why it happens:**
- It's easier to evaluate "does this sound like a local friend?" than "would I actually want to visit these places?"
- The test asks the right question for the wrong attribute — style over substance
- High writing quality masks mediocre recommendation quality

**How to avoid:**
1. **Design two separate blind tests** — one for SOUL writing quality (Phase 0 prerequisite), one for recommendation quality (separate validation)
2. **For recommendation test**: Show users two itineraries (our AI + a competitor's) without branding; ask which itinerary they'd actually follow
3. **Include "surprise me" as a metric** — "Did this itinerary recommend something you wouldn't have found on your own?"
4. **Test with ground truth**: If a user has visited 上海 before, exclude well-known venues and measure whether AI recommends genuinely niche spots

**Warning signs:**
- Phase 0 test results only mention "writing quality" or "tone" — no mention of venue quality
- Blind test participants are friends/team members who know the product's taste goals (unbiased but also unvalidated against real user needs)

**Phase to address:**
- **Phase 0 (Prompt Blind Test)** — ensure the test captures both writing AND recommendation quality

---

### Pitfall 10: Fine-Tuning Ambition Triggers Data Compliance Issues

**What goes wrong:**
The team collects user feedback and interaction data to fine-tune a model for better taste matching. This triggers compliance concerns: user-generated travel preferences could be considered 个人信息 (personal information) under PIPL, and using it for model training requires explicit consent and data minimization.

**Why it happens:**
- Chinese data privacy law (PIPL) is strict about how personal data can be used for AI training
- "Taste profile" data — where a user likes to travel, their preferences — is sensitive personal information
- Using this data for model training without proper consent mechanism is a legal risk

**How to avoid:**
1. **Design data architecture for compliance from day one** — separate taste profile data from LLM training pipelines
2. **Include explicit data usage consent** in onboarding if any user data will feed into model improvement
3. **Anonymize before any analytics** — strip user identifiers before aggregating feedback
4. **Use SOUL prompt + taste data approach (no fine-tuning)** — this was a deliberate decision in PROJECT.md; do not deviate without legal review
5. **Document the compliance boundary** — what data goes where, who can access it

**Warning signs:**
- Team discusses "could we use this interaction data to improve the model?" without legal review
- User feedback data is stored in the same database as POI data without access controls
- No data retention policy exists

**Phase to address:**
- **Phase 1 (Data Architecture)** — implement data separation and consent handling
- **Phase 0 (Legal/Compliance)** — if any user data will be used, consult legal before Phase 1 begins

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode Tier A POIs for 1 city | Fast MVP delivery | Rewriting import pipeline later | MVP only; never acceptable for scale |
| Skip rate limiting during development | Easier testing | API quota exhaustion on launch day | Never acceptable |
| Use single API key for all users | Simpler auth | Can't track per-user usage or revoke compromised keys | Never acceptable |
| Cache POI data indefinitely | No refresh overhead | Stale data, user trust erosion | Only if TTL is enforced |
| Store user preferences in plain JSON | Faster development | No structured query capability | MVP only, with migration plan |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **Amap Search API** | Calling `POST /v3/place/text` with full Chinese address — returns 0 results if any character has a space or punctuation mismatch | Use Amap's `keywords` parameter instead of `address`; test with spaces and special chars |
| **Amap Route API** | Requesting `strategy=10` (most economic) for pedestrian routes — returns routes inappropriate for walking | Use `strategy=0` (recommended) or `strategy=30` (avoid highways) for pedestrian routes |
| **Amap POI Type** | Filtering by POI type without also checking `typecode` — some POIs return without expected type field | Always use both `keywords` and `typecode` filters together; validate expected fields in response |
| **DeepSeek-V3** | Sending entire conversation history for each generation request — rapidly accumulates token cost | Use conversation summarization or start fresh per generation with only static context |
| **SQLite** | Using `SELECT *` on large POI tables during route scoring — blocks the event loop | Use indexed queries with specific columns; never SELECT * on >1000 rows |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| **Unbounded POI cache growth** | SQLite file grows to 50MB+; query times slow to 500ms+ | Set max POI cache size; evict oldest Tier C POIs when limit reached | At 10+ cities with full POI coverage |
| **Sequential API calls in route validation** | 20 POI route takes 20+ seconds (20 sequential Amap calls) | Batch route segments or parallelize with asyncio | Routes with >10 nodes |
| **No query indexing on POI table** | `WHERE taste_tags LIKE '%文艺%'` causes full table scan | Create FTS5 index on taste_tags; add composite indexes on (city, tier) | >500 POIs in database |
| **SSE memory accumulation** | Each streaming request holds full context in memory; 100 concurrent users = OOM | Stream tokens immediately; don't buffer full response | >50 concurrent generation requests |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| **Embedding Amap API key in frontend code** | Key stolen, quota exhausted by attacker | Keep all Amap calls server-side; key never leaves backend |
| **No input sanitization on user text queries** | Prompt injection via crafted travel requests | Strip/markdown-escape user input before including in LLM prompt |
| **Storing JWT secret in code** | Token forgery if code is leaked | Use environment variables; rotate secrets regularly |
| **No rate limiting on `/generate` endpoint** | Cost explosion from adversarial or buggy client | Implement per-user rate limits; reject excessive concurrent requests |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| **No estimated total time shown until generation completes** | Users don't know if they're waiting 30s or 5 minutes | Show estimated time range (e.g., "~45 seconds") before generation starts |
| **Route shows walking time but not physical difficulty** | User plans a "30 minute walk" that's actually a 2km highway trek | Add "mostly flat urban" or "requires stamina" descriptors for long walks |
| **"调整" (adjust) flow is unclear** | Users don't know if "我想换个地方" will regenerate the whole itinerary or just one stop | Explicitly confirm: "Replace [venue name] with something similar in this area?" |
| **No offline fallback** | User loses signal mid-generation, loses their in-progress request | Save draft itinerary to localStorage; offer "continue" on next visit |

---

## "Looks Done But Isn't" Checklist

- [ ] **POI Import:** Looks complete when it returns data — verify all expected fields (name, address, typecode, location) are non-null
- [ ] **Route Validation:** Looks passing when API returns `status: 1` — verify the returned `distance` and `time` fields are non-zero and reasonable
- [ ] **SSE Streaming:** Looks working when spinner appears — verify terminal `[DONE]` event actually terminates the connection
- [ ] **Taste Tags:** Looks populated when search returns results — verify tags are specific (not just "餐厅" but "胡同里的私房菜")
- [ ] **Tier Classification:** Looks correct when Tier A/B labels appear — verify Tier A has `highlight_note` and `recommend_reason` populated (not just name/address)
- [ ] **Feedback Button:** Looks functional when user taps it — verify the response is stored and queryable, not just logged to stdout
- [ ] **Phase 0 Prerequisite:** Looks validated when blind test passes — verify test measured recommendation quality, not just writing quality

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| LLM fabricates venues | HIGH | Immediately disable affected itinerary; remove hallucinated POIs from database; add hallucination check; notify affected users |
| Stale POI data | MEDIUM | Delete affected POI records; trigger re-import from Amap; demote POI source to Tier C; accept temporary recommendation gap |
| Amap rate limit hit | MEDIUM | Implement emergency caching; throttle new requests; contact Amap for quota review; implement paid tier migration |
| SSE drop mid-generation | LOW | Client reconnects automatically with reconnection logic; generation resumes from checkpoint if implemented, otherwise restart |
| Feedback loop unused | LOW (but opportunity cost HIGH) | Backfill feedback into analytics; schedule weekly review; build automated POI demotion logic |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| LLM fabricates venues | Phase 1 (Stage 4 Validation) | Manual test: generate 20 itineraries, verify all POI IDs exist in DB |
| POI data becomes stale | Phase 1 (Data Pipeline) | Check `poi_verified_at` is within TTL for all active POIs |
| Amap rate limits | Phase 1 (Infrastructure) | Load test: simulate 100 concurrent users, verify no 1002 errors |
| Route validation quality | Phase 1 (Route Validation) | Sample 10 routes, walk each segment physically, compare to Amap |
| Generic taste recommendations | Phase 0 (Blind Test) | Separate recommendation quality test from writing quality test |
| Chinese encoding issues | Phase 1 (Database Setup) | Insert 1000 Chinese-named POIs, retrieve via API, verify display correct |
| SSE drops | Phase 1 (API Contract) | Test: generate 10 itineraries, verify all receive `[DONE]` terminal event |
| Feedback loop unused | Phase 1 (Feedback System) | After 2 weeks of production: verify feedback data is queryable and reviewed |
| Phase 0 validates wrong thing | Phase 0 (Test Design) | Test instrument captures both writing quality AND recommendation quality |
| Data compliance | Phase 1 (Data Architecture) | Legal review of data flow before any user data is collected |

---

## Sources

- **Amap Web Service API Documentation** — verified POI field structure, rate limit explanations, geocoding behavior (2026-02-02 update)
- **PROJECT.md** — confirmed technology stack (Python/FastAPI, Vue, SQLite, DeepSeek-V3, Amap), 3-tier POI architecture, 4-stage generation pipeline, compliance constraints
- **Domain knowledge** — general patterns from LLM application development, travel recommendation system failure cases, Chinese internet product development
- **LOW confidence** — certain pitfalls (Chinese market specifics, user behavior patterns) are based on general knowledge rather than specific documented post-mortems; validation recommended during Phase 1 user research

---

*Pitfalls research for: 品味行程生成器 (Taste-based Itinerary Generator)*
*Researched: 2026-04-15*
