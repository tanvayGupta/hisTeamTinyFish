# Current State

## Project

SEO Page Auditor — TinyFish × DTU workshop.

Goal: Audit what AI tools can extract from a webpage, whether it appears in search results, and how to fix visibility gaps.

## Status

Phase 0 — Completed.
Phase 1A (Worktree A / `feat/evidence`) — Completed and verified.
Phase 1B (Worktree B / `feat/report`) — In progress / parallel.

## Architecture & Worktree A Modules

- `schemas.py`: Shared data contracts (`FetchResult`, `SearchHit`, `SearchResult`, `Finding`, `AuditReport`).
- `tinyfish_client.py`: Thin authenticated client wrapper for TinyFish Search & Fetch with retries and timeout handling.
- `raw_compare.py`: Text comparison engine identifying `missing_from_extraction` and `only_in_extraction`.
- `fetch_module.py`: `get_fetch_result(url)` combining raw HTTP GET analysis and TinyFish markdown/link extraction.
- `search_module.py`: `get_search_result(url, query, fetch)` with query derivation, URL normalization, and page rank detection.
- `test_evidence.py`: Contract verification test suite running against real URLs.

## Verified Progress & Test Results

- Implemented `tinyfish_client.py` with `tf_fetch` and `tf_search`, supporting auth headers (`X-API-Key`), timeout, 1-retry fallback, and clean error dictionaries without credential exposure.
- Implemented `raw_compare.py` with text chunking, punctuation/markdown normalization, and capped gap detection.
- Implemented `fetch_module.py` adhering to `FetchResult` schema:
  - Raw HTML metadata: status, title, meta description, canonical, robots meta, JSON-LD blocks, image counts, missing alt counts, raw word count.
  - TinyFish extracted data: markdown text, word count, markdown headings (`[{"level": int, "text": str}]`), structured links (`[{"text": str, "href": str}]`).
  - Graceful degradation on network/DNS errors without crashing.
- Implemented `search_module.py` adhering to `SearchResult` schema:
  - Smart query derivation from title / H1 / URL slug when no query is supplied.
  - Normalized URL matching (stripping protocol, `www.`, trailing slash, fragments, queries).
  - Page rank detection and top competitor hit extraction.
- Tested `test_evidence.py` against live URLs:
  - `https://danluu.com` ("Dan Luu"): Fetch 200, raw 1434 words vs extracted 1428 words, 210 links, 15 missing / 15 only in extraction, Search rank #1.
  - `https://example.com` ("Example Domain"): Fetch 200, raw 25 words vs extracted 25 words, 0 gaps, Search rank #1.
  - `https://docs.github.com/en/get-started`: Fetch 200, raw 801 words vs extracted 354 words, 15 headings, 126 links, 11 missing items, derived query "Get started with GitHub documentation", Search rank #1.
- All schema assertions and `to_dict` / `from_dict` roundtrips validated successfully.

## Blockers & API Connectivity

- Live TinyFish API connectivity verified successfully with active API key.
- No blockers for Worktree A.

## Next Action

1. Await completion of Phase 1B (`feat/report`).
2. Merge `feat/evidence` and `feat/report` into `main` for Phase 2 Shared Integration (`pipeline.py`).
