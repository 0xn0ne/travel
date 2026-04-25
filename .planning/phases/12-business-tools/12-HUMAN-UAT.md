---
status: partial
phase: 12-business-tools
source: [12-VERIFICATION.md]
started: 2026-04-21T00:00:00Z
updated: 2026-04-21T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. POI Search Tool E2E (BIZ-01)

expected: Start server with seeded DB + Amap API key, call `search_pois(city="上海", keyword="咖啡馆")`, verify formatted results with tier/rating/coords/highlight_note. Results should include POI name, rating, coordinates, and city.
result: [pending]

### 2. Weather Tool E2E (BIZ-02)

expected: Call `query_weather(city="上海", days=3)`, verify forecast with current conditions + daily forecast + travel suggestions. Weather data comes from 高德 weather API using city adcode.
result: [pending]

### 3. Web Search Tool E2E (TOOL-01)

expected: Call `web_search(query="上海小众咖啡馆推荐")`, verify DuckDuckGo returns top 5 results with title, snippet, and URL. Uses ddgs package with region=cn-zh.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
