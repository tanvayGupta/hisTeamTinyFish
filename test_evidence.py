"""Verification script for Worktree A (Evidence Collection).

Runs fetch_module.get_fetch_result and search_module.get_search_result against URLs,
validates that outputs conform to schemas.py dataclasses, and dumps JSON results.
"""

from __future__ import annotations

import json
import sys
from typing import Optional

from fetch_module import get_fetch_result
from schemas import FetchResult, SearchHit, SearchResult
from search_module import get_search_result

DEFAULT_TEST_URLS = [
    ("https://danluu.com", "Dan Luu"),
    ("https://example.com", "Example Domain"),
    ("https://docs.github.com/en/get-started", None),
]


def validate_fetch_result(res: FetchResult) -> None:
    """Validate that FetchResult conforms to contract."""
    assert isinstance(res, FetchResult), "Output is not an instance of FetchResult"
    assert isinstance(res.url, str), "res.url must be str"
    assert isinstance(res.final_url, str), "res.final_url must be str"
    assert res.status is None or isinstance(res.status, int), "res.status must be int or None"
    assert isinstance(res.extracted_text, str), "res.extracted_text must be str"
    assert isinstance(res.extracted_word_count, int), "res.extracted_word_count must be int"
    assert isinstance(res.headings, list), "res.headings must be list"
    assert isinstance(res.links, list), "res.links must be list"
    for link in res.links:
        assert isinstance(link, dict), "Each link must be a dict"
        assert "text" in link and "href" in link, "Link must contain 'text' and 'href'"
    assert isinstance(res.raw_word_count, int), "res.raw_word_count must be int"
    assert isinstance(res.json_ld, list), "res.json_ld must be list"
    assert isinstance(res.missing_from_extraction, list), "res.missing_from_extraction must be list"
    assert isinstance(res.only_in_extraction, list), "res.only_in_extraction must be list"
    # Ensure serializable to dict and back
    data = res.to_dict()
    rehydrated = FetchResult.from_dict(data)
    assert rehydrated.url == res.url


def validate_search_result(res: SearchResult) -> None:
    """Validate that SearchResult conforms to contract."""
    assert isinstance(res, SearchResult), "Output is not an instance of SearchResult"
    assert isinstance(res.query, str), "res.query must be str"
    assert isinstance(res.query_was_derived, bool), "res.query_was_derived must be bool"
    assert res.page_rank is None or isinstance(res.page_rank, int), "res.page_rank must be int or None"
    assert isinstance(res.top_results, list), "res.top_results must be list"
    for hit in res.top_results:
        assert isinstance(hit, SearchHit), "Each hit must be a SearchHit"
        assert isinstance(hit.rank, int), "hit.rank must be int"
        assert isinstance(hit.title, str), "hit.title must be str"
        assert isinstance(hit.url, str), "hit.url must be str"
        assert isinstance(hit.snippet, str), "hit.snippet must be str"
    # Ensure serializable to dict and back
    data = res.to_dict()
    rehydrated = SearchResult.from_dict(data)
    assert rehydrated.query == res.query


def test_url(url: str, query: Optional[str] = None) -> dict:
    """Run fetch and search for a URL and return combined dictionary."""
    fetch_res = get_fetch_result(url)
    validate_fetch_result(fetch_res)

    search_res = get_search_result(url, query=query, fetch=fetch_res)
    validate_search_result(search_res)

    return {
        "fetch": fetch_res.to_dict(),
        "search": search_res.to_dict(),
    }


def main() -> None:
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        target_query = sys.argv[2] if len(sys.argv) > 2 else None
        results = test_url(target_url, target_query)
        print(json.dumps(results, indent=2))
        return

    print("Running verification against default test URLs...")
    for url, query in DEFAULT_TEST_URLS:
        print(f"\n==================================================")
        print(f"Testing URL: {url} (query: {query})")
        print(f"==================================================")
        results = test_url(url, query)
        f = results["fetch"]
        s = results["search"]
        print(f"Status: {f['status']}")
        print(f"Raw words: {f['raw_word_count']} | Extracted words: {f['extracted_word_count']}")
        print(f"Headings count: {len(f['headings'])} | Links count: {len(f['links'])}")
        print(f"Missing from extraction: {len(f['missing_from_extraction'])} items")
        print(f"Only in extraction: {len(f['only_in_extraction'])} items")
        print(f"Search Query: '{s['query']}' (derived={s['query_was_derived']})")
        print(f"Page Rank: {s['page_rank']} | Top results returned: {len(s['top_results'])}")
        if s["error"]:
            print(f"Search error: {s['error']}")
        if f["error"]:
            print(f"Fetch error: {f['error']}")

    print("\nAll verifications passed!")


if __name__ == "__main__":
    main()
