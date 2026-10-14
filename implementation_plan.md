# SEO Page Auditor — 90-Minute Implementation Plan

TinyFish × DTU Student Bounty Drop 001 · Track: **SEO Page Auditor**

**One-line pitch:** Show the gap between what a human sees on a page and what an AI tool can actually extract from it, then say how to close it.

---

## 0. Requirements checklist (definition of done)

| # | Submission requirement | Where it's satisfied |
|---|---|---|
| 1 | Takes a URL (+ optional target query) | `app.py` input form, `pipeline.run_audit(url, query=None)` |
| 2 | Uses TinyFish **Search** and **Fetch** | `fetch_module.py`, `search_module.py` |
| 3 | Report: what AI can/can't read, visibility gaps, concrete fixes | `analyze.py` → `app.py` report |
| 4 | Demo on several real pages | Phase 3 (4–5 pages, mix of good/bad) |
| 5 | Short explanation of how TinyFish is used | `docs/tinyfish_usage.md` (Phase 4) |
| 6 | Post on **LinkedIn and X**, tagging TinyFish (both required) | `docs/posts.md` (Phase 4) |

Shared prize ranking across all tracks → polish, a clean demo, and a clear TinyFish story matter as much as features.

---

## 1. Timeline at a glance

| Time (min) | Phase | Where |
|---|---|---|
| 0–10 | **Phase 0 — Shared setup** | `main` |
| 10–45 | **Phase 1A / 1B — Parallel build** | worktree A and worktree B |
| 30 | **Checkpoint** (see §6) | both |
| 45–55 | **Phase 2 — Shared integration** | `main` |
| 55–72 | **Phase 3 — Shared polish + demo** | `main` |
| 72–90 | **Phase 4 — Shared submission** | `main` |

Hard rule: **Phase 1 ends at minute 45 no matter what.** Merge what works.

---

## 2. Worktrees: two-minute primer

A worktree is a second folder checked out from the same repo on its own branch. You can work on two branches at the same time with no stashing or switching.

```bash
# in main folder, after the Phase 0 commit
git worktree add ../seo-A -b feat/evidence      # Worktree A
git worktree add ../seo-B -b feat/report        # Worktree B
git worktree list                               # verify
```

Gotchas:
- **Untracked files are not shared.** Copy `.env` (TinyFish key) into `../seo-A` and `../seo-B`. Install dependencies in each (or point both at one shared venv).
- **One branch per worktree.** You can't check out the same branch in two places.
- **File ownership prevents merge conflicts.** Each worktree edits only its own files (table below). Nobody edits `schemas.py` after Phase 0.
- Commit often inside each worktree. Merging happens from the **main** folder.

Merge (Phase 2):
```bash
cd ../seo-auditor            # main folder
git merge feat/evidence
git merge feat/report
git worktree remove ../seo-A # optional cleanup
git worktree remove ../seo-B
```

---

## 3. Repo layout and file ownership

```
seo-auditor/
├── schemas.py              # SHARED — frozen after Phase 0
├── mocks/                  # SHARED — frozen after Phase 0
│   ├── fetch_js_heavy.json
│   ├── fetch_good.json
│   ├── search_found.json
│   └── search_not_found.json
├── pipeline.py             # SHARED — written in Phase 2
├── requirements.txt        # SHARED
├── .env.example            # SHARED
├── samples/urls.txt        # SHARED — demo pages (Phase 3)
├── docs/
│   ├── tinyfish_usage.md   # SHARED — Phase 4
│   └── posts.md            # SHARED — Phase 4
│
├── tinyfish_client.py      # A
├── fetch_module.py         # A
├── raw_compare.py          # A
├── search_module.py        # A
├── test_evidence.py        # A (quick script, not a full test suite)
│
├── analyze.py              # B
├── fixes.py                # B
├── app.py                  # B (Streamlit)
└── report_render.py        # B (optional: export report to Markdown/HTML)
```

**Split logic:** A collects **evidence** (everything that touches TinyFish and raw HTTP). B turns evidence into **findings and a report** (pure logic + UI). B never calls TinyFish and works entirely against `mocks/` until merge.

---

## 4. Phase 0 — Shared setup (min 0–10) · on `main`

**Goal:** both worktrees can start immediately with zero ambiguity about data shapes.

- [ ] `git init seo-auditor`, create the layout above, add `.gitignore` (`.env`, `__pycache__`, `.venv`)
- [ ] Read the TinyFish docs for **Fetch** and **Search** (auth, request/response shape, rate limits)
- [ ] Put the key in `.env`, make **one successful Fetch call and one successful Search call** in a scratch script. Note what Fetch returns (rendered or raw? text, markdown, links?) because that decides what the "gap" story looks like
- [ ] Write `schemas.py` (below)
- [ ] Write the four mock JSON files in `mocks/` matching the schemas (hand-written is fine; two fetch variants, two search variants)
- [ ] `requirements.txt`: `requests`, `beautifulsoup4`, `streamlit`, `python-dotenv`, `anthropic` (optional)
- [ ] Commit: `skeleton + contracts`
- [ ] Create both worktrees (§2), copy `.env` into each

### `schemas.py` (contracts — adjust field names after your smoke test, then freeze)

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FetchResult:
    url: str
    final_url: str
    status: Optional[int]
    # What an AI tool gets via TinyFish Fetch
    extracted_text: str
    extracted_word_count: int
    headings: list[dict]          # [{"level": 1, "text": "..."}]
    links: list[dict]             # [{"text": "...", "href": "..."}]
    # What a plain HTTP GET sees (no JS execution)
    raw_word_count: int
    raw_title: Optional[str]
    meta_description: Optional[str]
    canonical: Optional[str]
    robots_meta: Optional[str]
    json_ld: list[dict]           # parsed JSON-LD blocks
    images_total: int
    images_missing_alt: int
    # The gap
    missing_from_extraction: list[str]   # sentences/headings in raw but not extracted
    only_in_extraction: list[str]        # in extracted but not in raw (JS-rendered)
    error: Optional[str] = None

@dataclass
class SearchHit:
    rank: int
    title: str
    url: str
    snippet: str

@dataclass
class SearchResult:
    query: str
    query_was_derived: bool       # True if user gave no query
    page_rank: Optional[int]      # None = not found in results
    page_snippet: Optional[str]
    top_results: list[SearchHit]  # top ~5-10, for competitor comparison
    error: Optional[str] = None

@dataclass
class Finding:
    id: str                       # e.g. "no_json_ld"
    category: str                 # "readability" | "visibility" | "structure" | "query_fit"
    severity: str                 # "high" | "medium" | "low"
    title: str
    evidence: str                 # concrete numbers/quotes from the page
    fix: str                      # plain-language fix
    fix_snippet: Optional[str] = None   # copy-paste code (e.g. JSON-LD block)

@dataclass
class AuditReport:
    url: str
    query: str
    score: int                    # 0-100
    summary: str                  # 2-3 sentences
    can_read: list[str]           # what AI tools CAN read
    cannot_read: list[str]        # what they can't / miss
    findings: list[Finding]
    fetch: FetchResult
    search: SearchResult
```

---

## 5. Phase 1 — Parallel build (min 10–45)

### Phase 1A — Worktree A (`feat/evidence`) · folder `../seo-A`

**Owner of:** `tinyfish_client.py`, `fetch_module.py`, `raw_compare.py`, `search_module.py`, `test_evidence.py`
**Output contract:** `fetch_module.get_fetch_result(url) -> FetchResult` and `search_module.get_search_result(url, query=None, fetch=None) -> SearchResult`, both matching `schemas.py` exactly.

**A1 · TinyFish client (min 10–15)**
- [ ] `tinyfish_client.py`: thin wrappers `tf_fetch(url)` and `tf_search(query)` with auth, timeout, one retry, and clean error handling (return error info, never crash the pipeline)

**A2 · Fetch + raw comparison (min 15–30)**
- [ ] `fetch_module.py`: call `tf_fetch`, populate `extracted_text`, `extracted_word_count`, `headings`, `links`
- [ ] Plain `requests.get` + BeautifulSoup for the raw side: `raw_word_count`, title, meta description, canonical, robots meta, JSON-LD blocks, image count and missing-alt count
- [ ] `raw_compare.py`: split both texts into sentences/heading lines, normalize (lowercase, collapse whitespace), compute:
  - `missing_from_extraction`: in raw but not in extracted
  - `only_in_extraction`: in extracted but not in raw (signals JS-rendered content that non-rendering crawlers will miss)
  - cap each list (e.g. 15 items) so the report stays readable
- [ ] Handle failures gracefully: 403/timeouts set `error` and still return a valid `FetchResult`

**A3 · Search (min 30–40)**
- [ ] `search_module.py`: if no query, derive one (page title minus brand suffix, or H1)
- [ ] Call `tf_search(query)`, normalize results into `SearchHit`
- [ ] Find the page in results via normalized URL match (strip `www.`, trailing slash, `utm_*`, `#fragment`), set `page_rank` or `None`
- [ ] Keep top ~5–10 competitors for the report

**A4 · Verify (min 40–45)**
- [ ] `test_evidence.py`: run both functions on 3 real URLs, dump JSON, confirm shape matches `schemas.py`
- [ ] Commit and push to branch: `evidence: fetch + search working on real URLs`

**A is done when:** `python test_evidence.py <url> "<query>"` prints valid `FetchResult` and `SearchResult` JSON.

---

### Phase 1B — Worktree B (`feat/report`) · folder `../seo-B`

**Owner of:** `analyze.py`, `fixes.py`, `app.py`, `report_render.py`
**Input contract:** `FetchResult` + `SearchResult` (load from `mocks/` during development)
**Output contract:** `analyze.build_report(fetch, search) -> AuditReport`

**B1 · Analyzer checks (min 10–25)** in `analyze.py`. Each check returns zero or one `Finding` with evidence:

| Check id | Logic | Severity |
|---|---|---|
| `extraction_gap` | `missing_from_extraction` non-empty, or extracted words far below raw words | high |
| `js_dependent` | `only_in_extraction` large, or raw words ≪ extracted words (content needs JS) | high |
| `no_title` / `weak_title` | missing, too short (<20) or too long (>65) chars | medium |
| `no_meta_description` | missing or outside ~70–160 chars | medium |
| `h1_issues` | zero or multiple H1s; heading levels skip | medium |
| `no_json_ld` | empty `json_ld` | medium |
| `images_missing_alt` | `images_missing_alt / images_total` above threshold | low–medium |
| `noindex_or_canonical` | `robots_meta` contains noindex; canonical points elsewhere | high |
| `weak_anchor_text` | many links with "click here", "read more" | low |
| `query_fit` | query terms absent from title/H1/first ~100 words | medium–high |
| `not_ranking` | `page_rank is None` for the query | high |
| `outranked` | competitors' titles/snippets show terms the page lacks | medium |

- [ ] Compute `score` (start at 100, subtract by severity: e.g. high −15, medium −8, low −3, floor 0)
- [ ] Build `can_read` / `cannot_read` lists from the evidence, in plain language ("Headings: 14 found", "Product details block was not in the extracted text")

**B2 · Fixes (min 25–32)** in `fixes.py`
- [ ] Templated fix text + `fix_snippet` per finding id (JSON-LD `Article`/`WebPage` block pre-filled with the page's title/URL, suggested `<title>` and meta description, `alt` attribute example, server-side rendering / pre-render advice for JS-dependent pages)
- [ ] **Optional (only if ahead of schedule):** one LLM call that takes the findings and writes a 3-sentence summary plus a rewritten title/meta suggestion. Keep behind a flag with the templated fallback

**B3 · UI (min 32–42)** in `app.py` (Streamlit)
- [ ] Inputs: URL, optional query, "Run audit" button, spinner
- [ ] Report layout: score + summary at top → two columns "What AI can read" / "What AI can't read" → **side-by-side gap view** (missing-from-extraction list) → search result panel (rank and competitor table) → findings grouped by severity, each with evidence and an expandable fix + code snippet
- [ ] Toggle "Use mock data" so the UI is demoable before A merges
- [ ] Download button for the report as Markdown (`report_render.py`)

**B4 · Verify (min 42–45)**
- [ ] Run the UI against all four mocks; the JS-heavy mock must show high-severity findings, the good mock a high score
- [ ] Commit: `report: analyzer + UI working against mocks`

**B is done when:** the Streamlit app renders a complete report from mock data.

---

## 6. Checkpoint at minute 30

Each worktree answers: *does my code already run against the contract?*

- **A:** `tf_fetch` and `tf_search` work on at least one real URL. If Search is giving trouble, keep going with Fetch, and cut the competitor comparison to a simple rank check.
- **B:** at least 6 checks and the report skeleton render from mocks.
- If either is behind, cut from the **cut list** (§10) now, not at minute 44.

---

## 7. Phase 2 — Shared integration (min 45–55) · on `main`

- [ ] Merge `feat/evidence`, then `feat/report` (§2). Conflicts should be near zero thanks to file ownership
- [ ] Write `pipeline.py`:
  ```python
  def run_audit(url, query=None, use_mocks=False) -> AuditReport:
      fetch = get_fetch_result(url)
      search = get_search_result(url, query, fetch)
      return build_report(fetch, search)
  ```
- [ ] Wire `app.py` to `run_audit` (remove or keep the mock toggle)
- [ ] Run end to end on **one real URL**; fix shape mismatches (field names, `None` handling, empty lists)
- [ ] Make errors visible, not fatal: if Fetch or Search fails, show a partial report with a clear "couldn't fetch/search" note
- [ ] Commit: `integration: end-to-end audit working`

**Done when:** pasting a real URL in the UI produces a full report.

---

## 8. Phase 3 — Shared polish + demo (min 55–72) · on `main`

- [ ] Fill `samples/urls.txt` with 4–5 pages, chosen so the reports clearly differ:
  1. A JavaScript-heavy page where Fetch misses content (your best demo)
  2. A well-optimized blog/article (high-score baseline)
  3. A thin or poorly structured page
  4. One page with a target query that **doesn't** rank
  5. Your own project/portfolio page (nice real-world fix example)
- [ ] Run all of them, save a Markdown report per page, check the findings are accurate (no false positives that would embarrass the demo)
- [ ] Tune thresholds and wording; make the "what AI can't read" section the visual focus
- [ ] Record the demo (screen capture, 2–3 min): one bad page → show gaps and fixes → one good page for contrast
- [ ] Take 2–3 clean screenshots for the posts
- [ ] Write a README with run instructions (`pip install -r requirements.txt`, `.env`, `streamlit run app.py`)

---

## 9. Phase 4 — Shared submission (min 72–90) · on `main`

- [ ] `docs/tinyfish_usage.md` (short, concrete):
  - **Fetch:** used to get what an AI tool actually extracts (text, headings, links), compared against a plain HTTP fetch to find the gap
  - **Search:** used to check whether and where the page appears for the target query and what the competing results look like
  - One sentence on why this pairing answers "can AI tools read and rank this page?"
- [ ] `docs/posts.md`: draft **both** posts, each tagging TinyFish:
  - **LinkedIn:** problem (AI search changes how pages get found) → what you built → one striking finding from a real page → how TinyFish is used → demo link/screenshots
  - **X:** shorter, one hook finding + screenshot/GIF + tag TinyFish
- [ ] Post on LinkedIn **and** X (both required), then copy the links
- [ ] Final check against §0 checklist, push repo, submit
- [ ] Buffer: leave at least 5 minutes unscheduled for submit-form surprises

---

## 10. Cut list (drop in this order if behind)

1. LLM-written summary/fixes → keep templated fixes
2. Markdown download button
3. `weak_anchor_text`, `h1_issues` checks
4. Competitor snippet comparison → keep just the rank
5. Streamlit styling polish

**Never cut:** raw-vs-extracted gap, search rank, concrete fixes with snippets, the multi-page demo, the TinyFish explanation, both posts.

---

## 11. Risk notes

- **Fetch may already render JS.** Check during the Phase 0 smoke test. If it does, frame the gap as "raw HTML vs. rendered", showing what non-rendering AI crawlers miss. If it doesn't, frame it as "what the page shows vs. what the tool extracted". Either way the report logic is the same.
- **Bot-blocked demo pages.** Test every demo URL in Phase 0 or 1; replace any that 403.
- **Search can't find the page.** That is a valid finding (`not_ranking`), not a bug. Make sure the UI presents it clearly.
- **Demo fallback:** keep saved JSON results for each demo page so the demo still works if the network or API fails.
