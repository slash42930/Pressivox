## Plan: Balanced UX Roadmap

Improve the existing static workspace UI in staged steps: first remove friction in the current Search/Research/Extract flows, then add lightweight backend support for transparency and persistence, and finally expose one deeper workflow already present in the backend. This keeps the first iteration small while building toward a more capable research workspace without replacing the current architecture.

**Steps**
1. Phase 1: Improve the existing search and research experience inside the static UI in c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\static\web-search-backend-ui-mod-1.html. Add persistent form state, last-view restoration, clearer loading/error states, richer result metadata, quick copy/share actions, better history affordances, and visible sorting/filter controls. This step is frontend-only and should preserve the current tab structure.
2. Phase 1A: Extend the Search tab to surface backend data it already receives or can receive cheaply: response time, request id in a diagnostics area, rerank score as a confidence indicator, selected-source style badges, and optional ambiguity hints when the result set is ambiguous. This depends on step 1 and reuses existing rendering functions instead of introducing a new UI layer.
3. Phase 1B: Improve the Research tab with export and comparison workflows. Add copy markdown/export markdown using summary_markdown, allow selecting up to 3 results for side-by-side comparison, and make meaning groups easier to scan with counts and stronger headings. This runs in parallel with step 2 once the shared UI utility changes from step 1 are in place.
4. Phase 2: Add minimal backend support for UX-focused features. Extend c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\schemas\search.py and c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\services\search\service.py so SearchResponse can expose ambiguous, meaning_groups, and selected_sources in a stable way instead of only the Research route returning the richer shape. Keep the existing /search contract backward-compatible by adding fields rather than reshaping results.
5. Phase 2A: Add one lightweight diagnostics/refinement endpoint only if needed after the frontend pass. Preferred option: a small query-analysis endpoint or enrich /search so the UI can warn about ambiguous queries before or immediately after rendering. Avoid creating multiple overlapping endpoints unless the UI cannot be implemented cleanly with the existing /search and /research flows.
6. Phase 2B: Improve persistence and revisit workflows. Either extend the existing search history model with small metadata fields needed for UX (saved tab, summary presence, ambiguity flag), or keep the database untouched and persist richer client state in localStorage for the first pass. Prefer client persistence first because history is currently session-scoped by design.
7. Phase 3: Expose one deeper workflow already present in the backend as a new advanced panel, not a whole redesign. Recommended choice: async Tavily research tasks using c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\api\routes\tavily_research.py, because it fits the product direction better than map/crawl for a first advanced UX expansion. Add task submission, polling, status display, and result rendering behind an “Advanced Research” section or tab.
8. Phase 3A: Consider map/crawl as follow-up expansions only after the async research workflow proves useful. Map is better for site exploration and crawl is better for batch extraction, but both add more UI complexity and should stay out of the first balanced roadmap slice.
9. Keep scope boundaries strict. Do not migrate away from the single static HTML file yet, do not redesign the visual language wholesale, do not introduce authentication, and do not build long-running job orchestration beyond the existing Tavily task polling flow.

**Relevant files**
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\static\web-search-backend-ui-mod-1.html — primary UI surface; reuse renderSearchCards, renderResearchResults, renderSelectedSources, renderMeaningGroups, renderHistoryCards, session storage helpers, and API call wiring.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\schemas\search.py — extend SearchResponse carefully for richer UI metadata and keep ResearchResponse export-friendly.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\api\routes\search.py — keep the main search entrypoint stable while exposing any added response fields.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\api\routes\research.py — reuse summary_markdown and selected_sources for export/comparison workflows.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\services\search\service.py — source of selected_sources, ambiguous, meaning_groups, response metadata, and future lightweight search diagnostics.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\services\search\scoring.py — source for rerank score and ranking transparency indicators.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\services\search\ambiguity_detection.py — basis for ambiguity warnings or diagnostics.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\api\routes\tavily_research.py — preferred advanced workflow to expose next.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\api\routes\tavily_map.py — hold for later site-explorer work.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\app\api\routes\tavily_crawl.py — hold for later batch extract/crawl work.
- c:\Users\40730\Desktop\web-search-backend\web-search-backend\tests\test_static_ui.py — keep static UI serving coverage; extend if adding visible sections or asset assumptions.

**Verification**
1. Validate the static UI still serves via the existing test in c:\Users\40730\Desktop\web-search-backend\web-search-backend\tests\test_static_ui.py.
2. Add focused API tests for any new SearchResponse fields so /search and /research remain backward-compatible and serializable.
3. Manually verify the Search, Research, Extract, and Histories tabs on desktop and mobile widths after each UI phase, especially persistent state restoration, comparison flow, export actions, and failure states.
4. Manually verify ambiguous-query behavior with a short general query and confirm meaning groups/selected sources are consistent between /search and /research if step 4 is implemented.
5. If the advanced Tavily research panel is added, verify submit, poll, success, error, and not-found task states against the existing endpoints before considering map/crawl work.

**Decisions**
- Chosen roadmap shape: balanced roadmap, not quick-polish only and not a large new product surface.
- Chosen scope: UI plus backend changes are allowed only when they materially improve UX or expose existing backend value.
- Recommended ordering: current-tab UX polish first, response-shape enrichment second, advanced Tavily workflow third.
- Included now: persistence, comparison, export, diagnostics/transparency, history improvements, ambiguity surfacing, one advanced async workflow.
- Excluded for now: full frontend rewrite, auth, multi-user saved workspaces, PDF server-side generation, map/crawl UI in the same iteration.

**Further Considerations**
1. Prefer localStorage for restored form state and lightweight saved context before extending the database schema; the current backend history is session-scoped and privacy-friendly.
2. If ranking transparency is exposed, keep the UI high-level; show confidence or trust indicators instead of leaking every scoring heuristic detail.
3. If the advanced research workflow lands well, the next strongest follow-up is batch extraction powered either by crawl or an internal extract batch endpoint, not a broader redesign.