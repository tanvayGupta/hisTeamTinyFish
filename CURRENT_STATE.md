# Current State

## Project

SEO Page Auditor — TinyFish × DTU workshop.

Goal: Audit what AI tools can extract from a webpage, whether it appears in search results, and how to fix visibility gaps.

## Status

Phase 0 — Completed.
Shared foundation, contracts, and mocks established and verified.
Parallel worktrees — Not yet created (to be created in Phase 1).

## Architecture

- `schemas.py`: Shared data contracts (`FetchResult`, `SearchHit`, `SearchResult`, `Finding`, `AuditReport`).
- `mocks/`: Deterministic test fixtures for fetch and search (`fetch_good.json`, `fetch_js_heavy.json`, `search_found.json`, `search_not_found.json`).
- `requirements.txt`: Minimal dependencies (`requests`, `beautifulsoup4`, `streamlit`, `python-dotenv`).
- `.env.example`: Template for configuration.
- Worktree A (`feat/evidence`): TinyFish Search/Fetch, raw HTML comparison, evidence collection.
- Worktree B (`feat/report`): Analysis, fixes, Streamlit UI.
- `pipeline.py`: Integrates both workstreams after merging (Phase 2).

## Verified Progress & Test Results

- Consulted official TinyFish Search and Fetch API specifications and OpenAPI schemas:
  - Search: `GET https://api.search.tinyfish.ai` returning `{query, total_results, page, results: [{position, site_name, title, snippet, url}]}`.
  - Fetch: `POST https://api.fetch.tinyfish.ai` returning `{results: [{url, final_url, title, description, language, format, text, links}], errors: [...]}`.
- Implemented `schemas.py` matching plan data contracts with `to_dict` and `from_dict` helpers.
- Created all 4 mock datasets in `mocks/` conforming to `FetchResult` and `SearchResult` schemas.
- Created `requirements.txt`, `.env.example`, and updated `.gitignore` for `.env` and `.venv`.
- Created `samples/urls.txt` with representative target URLs for demo scenarios.
- Ran validation test with Python 3.13: verified `schemas.py` imports, mock JSON parsing, dataclass mapping, and `AuditReport` serialization.

## Blockers & API Connectivity

- Real API smoke test was deferred because `TINYFISH_API_KEY` is not yet populated in `.env` (environment file prepared for user to add API key).
- No blockers for Phase 1 parallel development against contracts and mock fixtures.

## Next Action

1. User adds `TINYFISH_API_KEY` into `.env`.
2. Create parallel worktrees (`../seo-A` on `feat/evidence` and `../seo-B` on `feat/report`) and proceed with Phase 1.
