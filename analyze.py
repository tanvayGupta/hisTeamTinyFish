"""Pure analysis of shared FetchResult and SearchResult contracts."""

from schemas import AuditReport, FetchResult, SearchResult, Finding
from fixes import fix_for


def _finding(fid, category, severity, title, evidence, fetch, search):
    fix, snippet = fix_for(fid, fetch, fetch.final_url or fetch.url)
    return Finding(fid, category, severity, title, evidence, fix, snippet)


def build_report(fetch: FetchResult, search: SearchResult) -> AuditReport:
    findings = []
    extracted = max(fetch.extracted_word_count, 0)
    raw = max(fetch.raw_word_count, 0)
    if fetch.missing_from_extraction or (raw >= 20 and extracted < raw * .6):
        details = f"{len(fetch.missing_from_extraction)} raw text/heading items are missing; extracted {extracted} words vs {raw} raw HTML words."
        findings.append(_finding("extraction_gap", "readability", "high", "Important page content is missing from extraction", details, fetch, search))
    if len(fetch.only_in_extraction) >= 2 or (raw < extracted * .4 and extracted >= 20):
        findings.append(_finding("js_dependent", "readability", "high", "Page content depends on rendered JavaScript", f"{len(fetch.only_in_extraction)} items appear only in extracted content; {raw} raw words vs {extracted} extracted words.", fetch, search))
    title = fetch.raw_title or ""
    if not title:
        findings.append(_finding("no_title", "structure", "medium", "Page has no title", "The raw HTML title is missing.", fetch, search))
    elif len(title) < 20 or len(title) > 65:
        findings.append(_finding("weak_title", "structure", "medium", "Page title needs improvement", f"Title is {len(title)} characters; recommended range is 20–65.", fetch, search))
    description = fetch.meta_description or ""
    if not 70 <= len(description) <= 160:
        findings.append(_finding("no_meta_description", "structure", "medium", "Meta description is missing or outside the target length", f"Description length: {len(description)} characters; target range is 70–160.", fetch, search))
    if search.page_rank is None:
        findings.append(_finding("not_ranking", "visibility", "high", "Page was not found for this query", f"No matching page appeared for “{search.query}” in {len(search.top_results)} supplied results.", fetch, search))
    elif search.top_results and search.page_rank > 1:
        competitor_words = {w.lower().strip(".,:;!?()") for h in search.top_results if h.rank < search.page_rank for w in (h.title + " " + h.snippet).split()}
        page_words = {w.lower().strip(".,:;!?()") for w in (title + " " + fetch.extracted_text).split()}
        unique = sorted(w for w in competitor_words - page_words if len(w) > 5)
        if unique:
            findings.append(_finding("outranked", "query_fit", "medium", "Higher-ranked results cover terms absent from this page", f"Higher-ranked results include terms not found in the page: {', '.join(unique[:6])}.", fetch, search))
    if not fetch.json_ld:
        findings.append(_finding("no_json_ld", "structure", "low", "No JSON-LD structured data found", "The raw HTML contains 0 parsed JSON-LD blocks.", fetch, search))
    if fetch.images_missing_alt:
        findings.append(_finding("image_alt", "structure", "medium", "Some images lack alternative text", f"{fetch.images_missing_alt} of {fetch.images_total} images lack alt text.", fetch, search))

    penalties = {"high": 15, "medium": 8, "low": 3}
    score = max(0, 100 - sum(penalties[f.severity] for f in findings))
    can_read = [f"Extracted {extracted} words and {len(fetch.headings)} headings."]
    if fetch.links:
        can_read.append(f"Found {len(fetch.links)} links.")
    cannot_read = []
    if fetch.missing_from_extraction:
        cannot_read.append(f"{len(fetch.missing_from_extraction)} raw text/heading items are absent from extraction.")
    if fetch.only_in_extraction:
        cannot_read.append(f"{len(fetch.only_in_extraction)} items appear only in rendered extraction, not raw HTML.")
    if not cannot_read:
        cannot_read.append("No raw-to-extracted text gaps were reported.")
    if search.page_rank is None:
        cannot_read.append(f"Page did not appear in the supplied results for “{search.query}”.")
    summary = f"Audit score: {score}/100. " + (f"Found {len(findings)} actionable issues." if findings else "No issues were detected in the supplied evidence.")
    return AuditReport(fetch.url, search.query, score, summary, can_read, cannot_read, findings, fetch, search)
