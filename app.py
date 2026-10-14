"""Mock-backed Streamlit demo for the SEO page auditor."""

import json
from pathlib import Path

import streamlit as st

from analyze import build_report
from schemas import FetchResult, SearchResult


ROOT = Path(__file__).parent


def load_mock(kind: str, name: str):
    return json.loads((ROOT / "mocks" / f"{kind}_{name}.json").read_text(encoding="utf-8"))


st.set_page_config(page_title="SEO Page Auditor", layout="wide")
st.title("SEO Page Auditor")
st.caption("See what page extraction captures, what it misses, and how the page appears in search.")
with st.form("audit"):
    url = st.text_input("Page URL", "https://example.com/blog/understanding-ai-search")
    query = st.text_input("Target query (optional)")
    scenario = st.selectbox("Demo page", ["Good page", "Extraction problems"])
    use_mocks = st.checkbox("Use mock data", value=True)
    run = st.form_submit_button("Run audit")

if run:
    if not use_mocks:
        st.info("Live evidence pipeline is not connected in this worktree. Enable mock data to run the report.")
    else:
        suffix = "good" if scenario == "Good page" else "js_heavy"
        search_suffix = "found" if suffix == "good" else "not_found"
        fetch = FetchResult.from_dict(load_mock("fetch", suffix))
        search = SearchResult.from_dict(load_mock("search", search_suffix))
        if url.strip():
            fetch.url = url.strip()
        if query.strip():
            search.query = query.strip()
        report = build_report(fetch, search)
        st.session_state["report"] = report

if "report" in st.session_state:
    report = st.session_state["report"]
    c1, c2 = st.columns([1, 3])
    c1.metric("AI visibility score", f"{report.score}/100")
    c2.subheader(report.summary)
    left, right = st.columns(2)
    with left:
        st.markdown("#### What AI can read")
        for item in report.can_read:
            st.write("• " + item)
    with right:
        st.markdown("#### What AI can't read")
        for item in report.cannot_read:
            st.write("• " + item)
    st.markdown("#### Extraction gap")
    raw_col, extracted_col = st.columns(2)
    raw_col.metric("Raw HTML words", report.fetch.raw_word_count)
    extracted_col.metric("Extracted words", report.fetch.extracted_word_count)
    if report.fetch.missing_from_extraction:
        st.write("Missing from extraction")
        for item in report.fetch.missing_from_extraction:
            st.warning(item)
    else:
        st.caption("No raw-only text examples were included in this fixture.")
    if report.fetch.only_in_extraction:
        st.write("Present in rendered extraction, absent from raw HTML")
        for item in report.fetch.only_in_extraction:
            st.info(item)
    st.markdown("#### Search visibility")
    if report.search.page_rank is None:
        st.error(f"Not found for “{report.query}” in the supplied results.")
    else:
        st.success(f"Ranked #{report.search.page_rank} for “{report.query}”.")
    if report.search.top_results:
        st.dataframe([hit.to_dict() for hit in report.search.top_results], use_container_width=True, hide_index=True)
    st.markdown("#### Findings")
    for severity in ("high", "medium", "low"):
        findings = [f for f in report.findings if f.severity == severity]
        if findings:
            st.markdown(f"**{severity.title()} severity**")
            for finding in findings:
                with st.expander(finding.title):
                    st.write(f"Evidence: {finding.evidence}")
                    st.write(f"Fix: {finding.fix}")
                    if finding.fix_snippet:
                        st.code(finding.fix_snippet, language="html")
