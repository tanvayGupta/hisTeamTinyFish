"""Fetch module for collecting page content via TinyFish Fetch API and raw HTTP GET.

Constructs FetchResult according to shared contracts in schemas.py.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional
from bs4 import BeautifulSoup
import requests

from raw_compare import compare_texts
from schemas import FetchResult
from tinyfish_client import tf_fetch

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def extract_headings_from_markdown(text: str) -> list[dict[str, Any]]:
    """Extract markdown headings with level and clean text."""
    headings: list[dict[str, Any]] = []
    if not text:
        return headings

    for line in text.splitlines():
        line = line.strip()
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            # Clean possible markdown link or formatting from heading text
            clean_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading_text)
            clean_text = clean_text.strip("#*`_ ")
            if clean_text:
                headings.append({"level": level, "text": clean_text})
    return headings


def extract_links_from_markdown_and_list(
    extracted_text: str,
    raw_link_urls: list[str],
) -> list[dict[str, str]]:
    """Extract structured links [{"text": "...", "href": "..."}] from markdown text and TinyFish link list."""
    structured_links: list[dict[str, str]] = []
    seen_hrefs: set[str] = set()

    # 1. Parse markdown links [text](href)
    if extracted_text:
        md_links = re.findall(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", extracted_text)
        for text, href in md_links:
            clean_href = href.strip()
            clean_text = text.strip()
            if clean_href not in seen_hrefs:
                seen_hrefs.add(clean_href)
                structured_links.append({"text": clean_text, "href": clean_href})

    # 2. Append any additional URLs returned by TinyFish fetch
    for item in raw_link_urls:
        if isinstance(item, str):
            href = item.strip()
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                structured_links.append({"text": "", "href": href})
        elif isinstance(item, dict):
            href = str(item.get("href") or item.get("url") or "").strip()
            text = str(item.get("text") or "").strip()
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                structured_links.append({"text": text, "href": href})

    return structured_links


def get_raw_page_data(url: str, timeout: int = 12) -> dict[str, Any]:
    """Fetch raw HTML via standard HTTP GET and parse semantic metadata."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        final_url = resp.url
        status_code = resp.status_code
        html = resp.text
    except Exception as exc:
        logger.warning("Raw HTTP GET failed for %s: %s", url, exc)
        return {
            "status": None,
            "final_url": url,
            "raw_text": "",
            "raw_word_count": 0,
            "raw_title": None,
            "meta_description": None,
            "canonical": None,
            "robots_meta": None,
            "json_ld": [],
            "images_total": 0,
            "images_missing_alt": 0,
            "error": f"Raw fetch failed: {type(exc).__name__}",
        }

    soup = BeautifulSoup(html, "html.parser")

    # Raw title
    raw_title: Optional[str] = None
    if soup.title and soup.title.string:
        raw_title = soup.title.string.strip()

    # Meta description
    meta_desc: Optional[str] = None
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if not desc_tag:
        desc_tag = soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    # Canonical link
    canonical: Optional[str] = None
    canon_tag = soup.find("link", attrs={"rel": re.compile(r"^canonical$", re.I)})
    if canon_tag and canon_tag.get("href"):
        canonical = canon_tag["href"].strip()

    # Robots meta tag
    robots_meta: Optional[str] = None
    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots_tag and robots_tag.get("content"):
        robots_meta = robots_tag["content"].strip()

    # JSON-LD blocks
    json_ld_blocks: list[dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        if script.string:
            try:
                parsed = json.loads(script.string.strip())
                if isinstance(parsed, list):
                    json_ld_blocks.extend([item for item in parsed if isinstance(item, dict)])
                elif isinstance(parsed, dict):
                    json_ld_blocks.append(parsed)
            except Exception:
                pass

    # Images and alt attribute coverage
    img_tags = soup.find_all("img")
    images_total = len(img_tags)
    images_missing_alt = sum(
        1 for img in img_tags
        if not img.get("alt") or not img.get("alt").strip()
    )

    # Clean raw text without scripts, styles, etc.
    clean_soup = BeautifulSoup(html, "html.parser")
    for tag in clean_soup(["script", "style", "noscript", "svg", "head"]):
        tag.decompose()
    raw_text = clean_soup.get_text(separator=" ")
    raw_words = raw_text.split()
    raw_word_count = len(raw_words)

    # Headings in raw HTML (for fallback if needed)
    raw_headings: list[dict[str, Any]] = []
    for h in clean_soup.find_all(re.compile(r"^h[1-6]$")):
        level = int(h.name[1])
        text = h.get_text(strip=True)
        if text:
            raw_headings.append({"level": level, "text": text})

    return {
        "status": status_code,
        "final_url": final_url,
        "raw_text": raw_text,
        "raw_word_count": raw_word_count,
        "raw_title": raw_title,
        "meta_description": meta_desc,
        "canonical": canonical,
        "robots_meta": robots_meta,
        "json_ld": json_ld_blocks,
        "images_total": images_total,
        "images_missing_alt": images_missing_alt,
        "raw_headings": raw_headings,
        "error": None if status_code < 400 else f"HTTP {status_code}",
    }


def get_fetch_result(url: str) -> FetchResult:
    """Collect page evidence via TinyFish Fetch and plain HTTP GET, then compute gaps."""
    # 1. Fetch raw HTML data
    raw_data = get_raw_page_data(url)

    # 2. Call TinyFish Fetch API
    tf_data = tf_fetch(url, format="markdown", links=True)

    extracted_text = ""
    extracted_word_count = 0
    headings: list[dict[str, Any]] = []
    links: list[dict[str, str]] = []
    final_url = raw_data.get("final_url") or url
    status = raw_data.get("status")
    tf_error: Optional[str] = None

    if tf_data.get("error"):
        tf_error = tf_data.get("error")

    results = tf_data.get("results", [])
    if results and isinstance(results, list):
        res = results[0]
        extracted_text = res.get("text") or ""
        extracted_word_count = len(extracted_text.split())
        final_url = res.get("final_url") or final_url
        raw_links = res.get("links") or []

        # Extract markdown headings
        headings = extract_headings_from_markdown(extracted_text)
        # Extract structured links
        links = extract_links_from_markdown_and_list(extracted_text, raw_links)

    # If TinyFish returned no markdown headings, fallback to raw HTML headings
    if not headings and raw_data.get("raw_headings"):
        headings = raw_data["raw_headings"]

    # 3. Compare raw text and extracted text
    raw_text = raw_data.get("raw_text", "")
    missing_from_extraction, only_in_extraction = compare_texts(
        raw_text=raw_text,
        extracted_text=extracted_text,
    )

    # Overall error consolidation
    overall_error: Optional[str] = None
    if tf_error and raw_data.get("error"):
        overall_error = f"{tf_error}; {raw_data.get('error')}"
    elif tf_error:
        overall_error = tf_error
    elif raw_data.get("error"):
        overall_error = raw_data.get("error")

    return FetchResult(
        url=url,
        final_url=final_url,
        status=status,
        extracted_text=extracted_text,
        extracted_word_count=extracted_word_count,
        headings=headings,
        links=links,
        raw_word_count=raw_data.get("raw_word_count", 0),
        raw_title=raw_data.get("raw_title"),
        meta_description=raw_data.get("meta_description"),
        canonical=raw_data.get("canonical"),
        robots_meta=raw_data.get("robots_meta"),
        json_ld=raw_data.get("json_ld", []),
        images_total=raw_data.get("images_total", 0),
        images_missing_alt=raw_data.get("images_missing_alt", 0),
        missing_from_extraction=missing_from_extraction,
        only_in_extraction=only_in_extraction,
        error=overall_error,
    )
