"""Connect evidence collection to report analysis, with deterministic demo fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from analyze import build_report
from fetch_module import get_fetch_result
from schemas import AuditReport, FetchResult, SearchResult
from search_module import get_search_result

ROOT = Path(__file__).parent


def _load_mock(kind: str, name: str) -> dict:
    return json.loads((ROOT / "mocks" / f"{kind}_{name}.json").read_text(encoding="utf-8"))


def run_audit(
    url: str,
    query: Optional[str] = None,
    use_mocks: bool = False,
    mock_scenario: str = "good",
) -> AuditReport:
    """Run a live audit or one of the bundled good/js-heavy mock scenarios."""
    if use_mocks:
        scenario = "js_heavy" if mock_scenario in {"js_heavy", "problems", "extraction_problems"} else "good"
        fetch = FetchResult.from_dict(_load_mock("fetch", scenario))
        search = SearchResult.from_dict(
            _load_mock("search", "not_found" if scenario == "js_heavy" else "found")
        )
        fetch.url = url.strip() or fetch.url
        if query and query.strip():
            search.query = query.strip()
            search.query_was_derived = False
        return build_report(fetch, search)

    fetch = get_fetch_result(url.strip())
    search = get_search_result(url.strip(), query, fetch)
    return build_report(fetch, search)
