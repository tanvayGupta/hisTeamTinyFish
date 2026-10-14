"""Search module for checking page ranking and competitor visibility via TinyFish Search API.

Normalizes search results and calculates target page rank.
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urlparse, unquote

from schemas import FetchResult, SearchHit, SearchResult
from tinyfish_client import tf_search

logger = logging.getLogger(__name__)


def normalize_url_for_matching(url: str) -> str:
    """Normalize a URL for robust comparison across search results.

    Strips scheme (http/https), leading 'www.', trailing slashes, fragments, and queries.
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Remove standard default port if present
        if ":" in netloc:
            netloc = netloc.split(":")[0]

        path = unquote(parsed.path or "").rstrip("/")
        if not path:
            path = "/"
        else:
            path = path.lower()

        return f"{netloc}{path}"
    except Exception:
        clean = url.lower().strip()
        clean = re.sub(r"^https?://", "", clean)
        clean = re.sub(r"^www\.", "", clean)
        clean = clean.split("#")[0].split("?")[0].rstrip("/")
        return clean or "/"


def derive_query_from_page(url: str, fetch: Optional[FetchResult] = None) -> str:
    """Derive a sensible search query from page metadata, headings, or URL slug."""
    # 1. Try raw title
    if fetch and fetch.raw_title:
        title = fetch.raw_title.strip()
        # Strip common brand/site separators (e.g. "Page Name | Brand" or "Brand - Page Name")
        parts = re.split(r"[\s\-_|:•~—]+", title)
        # If title has multiple parts, pick the longest descriptive segment
        segments = re.split(r"\s+[|—–\-:•]\s+", title)
        if segments:
            candidate = max(segments, key=lambda s: len(s.strip())).strip()
            # If candidate has enough substance, use it
            if len(candidate) >= 5 and len(candidate.split()) >= 2:
                return candidate
            elif len(candidate) >= 3:
                return candidate
        if title:
            return title

    # 2. Try first H1 heading
    if fetch and fetch.headings:
        for h in fetch.headings:
            if h.get("level") == 1 and h.get("text"):
                text = h["text"].strip()
                if len(text) >= 5:
                    return text

    # 3. Derive from URL path
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path:
            # Take last path segment
            last_segment = path.split("/")[-1]
            # Replace hyphens, underscores with spaces
            slug_words = re.sub(r"[\-_.]+", " ", last_segment).strip()
            if slug_words and len(slug_words) >= 3:
                return slug_words

        # If root domain, return domain name without extension
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        domain_name = domain.split(".")[0]
        if domain_name:
            return domain_name
    except Exception:
        pass

    return url


def get_search_result(
    url: str,
    query: Optional[str] = None,
    fetch: Optional[FetchResult] = None,
) -> SearchResult:
    """Run search via TinyFish Search, normalize hits, and locate page rank."""
    query_was_derived = False
    effective_query = (query or "").strip()

    if not effective_query:
        query_was_derived = True
        effective_query = derive_query_from_page(url, fetch)

    tf_resp = tf_search(effective_query)
    error_msg: Optional[str] = tf_resp.get("error")

    raw_hits = tf_resp.get("results", [])
    top_results: list[SearchHit] = []

    target_norm = normalize_url_for_matching(url)
    final_norm = normalize_url_for_matching(fetch.final_url) if fetch and fetch.final_url else None

    page_rank: Optional[int] = None
    page_snippet: Optional[str] = None

    for idx, r in enumerate(raw_hits):
        rank = r.get("position", idx + 1)
        title = r.get("title", "")
        hit_url = r.get("url", "")
        snippet = r.get("snippet", "")

        hit = SearchHit(
            rank=rank,
            title=title,
            url=hit_url,
            snippet=snippet,
        )
        top_results.append(hit)

        # Check if this hit matches our target page
        hit_norm = normalize_url_for_matching(hit_url)
        if page_rank is None and hit_norm:
            if hit_norm == target_norm or (final_norm and hit_norm == final_norm):
                page_rank = rank
                page_snippet = snippet

    return SearchResult(
        query=effective_query,
        query_was_derived=query_was_derived,
        page_rank=page_rank,
        page_snippet=page_snippet,
        top_results=top_results[:10],
        error=error_msg,
    )
