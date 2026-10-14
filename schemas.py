from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FetchResult:
        return cls(
            url=data.get("url", ""),
            final_url=data.get("final_url", ""),
            status=data.get("status"),
            extracted_text=data.get("extracted_text", ""),
            extracted_word_count=data.get("extracted_word_count", 0),
            headings=data.get("headings", []),
            links=data.get("links", []),
            raw_word_count=data.get("raw_word_count", 0),
            raw_title=data.get("raw_title"),
            meta_description=data.get("meta_description"),
            canonical=data.get("canonical"),
            robots_meta=data.get("robots_meta"),
            json_ld=data.get("json_ld", []),
            images_total=data.get("images_total", 0),
            images_missing_alt=data.get("images_missing_alt", 0),
            missing_from_extraction=data.get("missing_from_extraction", []),
            only_in_extraction=data.get("only_in_extraction", []),
            error=data.get("error"),
        )


@dataclass
class SearchHit:
    rank: int
    title: str
    url: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchHit:
        return cls(
            rank=data.get("rank", 0),
            title=data.get("title", ""),
            url=data.get("url", ""),
            snippet=data.get("snippet", ""),
        )


@dataclass
class SearchResult:
    query: str
    query_was_derived: bool       # True if user gave no query
    page_rank: Optional[int]      # None = not found in results
    page_snippet: Optional[str]
    top_results: list[SearchHit]  # top ~5-10, for competitor comparison
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchResult:
        raw_hits = data.get("top_results", [])
        hits = [
            h if isinstance(h, SearchHit) else SearchHit.from_dict(h)
            for h in raw_hits
        ]
        return cls(
            query=data.get("query", ""),
            query_was_derived=data.get("query_was_derived", False),
            page_rank=data.get("page_rank"),
            page_snippet=data.get("page_snippet"),
            top_results=hits,
            error=data.get("error"),
        )


@dataclass
class Finding:
    id: str                       # e.g. "no_json_ld"
    category: str                 # "readability" | "visibility" | "structure" | "query_fit"
    severity: str                 # "high" | "medium" | "low"
    title: str
    evidence: str                 # concrete numbers/quotes from the page
    fix: str                      # plain-language fix
    fix_snippet: Optional[str] = None   # copy-paste code (e.g. JSON-LD block)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        return cls(
            id=data.get("id", ""),
            category=data.get("category", ""),
            severity=data.get("severity", ""),
            title=data.get("title", ""),
            evidence=data.get("evidence", ""),
            fix=data.get("fix", ""),
            fix_snippet=data.get("fix_snippet"),
        )


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditReport:
        findings = [
            f if isinstance(f, Finding) else Finding.from_dict(f)
            for f in data.get("findings", [])
        ]
        fetch_data = data.get("fetch", {})
        fetch = fetch_data if isinstance(fetch_data, FetchResult) else FetchResult.from_dict(fetch_data)

        search_data = data.get("search", {})
        search = search_data if isinstance(search_data, SearchResult) else SearchResult.from_dict(search_data)

        return cls(
            url=data.get("url", ""),
            query=data.get("query", ""),
            score=data.get("score", 0),
            summary=data.get("summary", ""),
            can_read=data.get("can_read", []),
            cannot_read=data.get("cannot_read", []),
            findings=findings,
            fetch=fetch,
            search=search,
        )
