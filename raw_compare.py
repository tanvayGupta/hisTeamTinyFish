"""Content comparison module between raw HTML text and TinyFish extracted text.

Identifies content visibility gaps:
- missing_from_extraction: content present in raw HTML but omitted in extraction.
- only_in_extraction: content present in extracted text but omitted in raw HTML
  (e.g., client-side JS rendered content).
"""

from __future__ import annotations

import re
from typing import Optional


def normalize_for_comparison(text: str) -> str:
    """Normalize text by lowering case, stripping markdown/punctuation, and collapsing whitespace."""
    if not text:
        return ""
    # Strip markdown links [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove markdown headers, list markers, and decoration symbols
    cleaned = re.sub(r"^[#*>\-\d\.\s]+", " ", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"[*_~`#]", " ", cleaned)
    # Replace any non-alphanumeric character with a space
    cleaned = re.sub(r"[^\w\s]", " ", cleaned, flags=re.UNICODE)
    # Lowercase and collapse multiple whitespace
    return " ".join(cleaned.lower().split())


def clean_display_chunk(chunk: str) -> str:
    """Clean a chunk for human-readable display in the report."""
    # Strip markdown link URLs, retaining label
    chunk = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", chunk)
    # Strip markdown hash headers and leading bullets
    chunk = re.sub(r"^[\s#*\->\d\.]+", "", chunk).strip()
    # Collapse internal whitespace
    return " ".join(chunk.split())


def split_into_chunks(text: str, min_chars: int = 25) -> list[str]:
    """Split text into distinct sentences or heading/paragraph lines."""
    if not text:
        return []

    lines = text.splitlines()
    candidates: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Split line on clear sentence boundaries if it's long
        if len(line) > 120:
            sentences = re.split(r"(?<=[.!?])\s+", line)
            for s in sentences:
                s = s.strip()
                if len(s) >= min_chars:
                    candidates.append(s)
        else:
            if len(line) >= min_chars:
                candidates.append(line)

    # Deduplicate while preserving order and filter boilerplate
    seen = set()
    result = []
    for raw_chunk in candidates:
        display = clean_display_chunk(raw_chunk)
        if len(display) < min_chars:
            continue
        norm = normalize_for_comparison(display)
        if len(norm) < 15 or norm in seen:
            continue
        seen.add(norm)
        result.append(display)

    return result


def compare_texts(
    raw_text: str,
    extracted_text: str,
    max_items: int = 15,
) -> tuple[list[str], list[str]]:
    """Compare raw text with extracted text to identify visibility gaps.

    Returns:
        (missing_from_extraction, only_in_extraction)
    """
    raw_chunks = split_into_chunks(raw_text)
    extracted_chunks = split_into_chunks(extracted_text)

    norm_raw_full = normalize_for_comparison(raw_text)
    norm_extracted_full = normalize_for_comparison(extracted_text)

    missing_from_extraction: list[str] = []
    only_in_extraction: list[str] = []

    # Chunks in raw text that do not appear in extracted text
    for chunk in raw_chunks:
        norm_chunk = normalize_for_comparison(chunk)
        # Check if the normalized chunk is contained in normalized extracted text
        if norm_chunk and norm_chunk not in norm_extracted_full:
            missing_from_extraction.append(chunk)
            if len(missing_from_extraction) >= max_items:
                break

    # Chunks in extracted text that do not appear in raw text (JS rendered)
    for chunk in extracted_chunks:
        norm_chunk = normalize_for_comparison(chunk)
        if norm_chunk and norm_chunk not in norm_raw_full:
            only_in_extraction.append(chunk)
            if len(only_in_extraction) >= max_items:
                break

    return missing_from_extraction, only_in_extraction
