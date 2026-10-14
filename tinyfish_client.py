"""TinyFish API client wrapper for Search and Fetch endpoints.

Provides authenticated requests, timeout handling, retries, and graceful error handling.
Credentials are never logged or exposed.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional
from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger(__name__)

SEARCH_API_URL = "https://api.search.tinyfish.ai"
FETCH_API_URL = "https://api.fetch.tinyfish.ai"
DEFAULT_TIMEOUT = 15


def get_api_key() -> Optional[str]:
    """Retrieve TinyFish API key from environment without logging it."""
    return os.getenv("TINYFISH_API_KEY")


def tf_fetch(
    url: str,
    format: str = "markdown",
    links: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 1,
) -> dict[str, Any]:
    """Call TinyFish Fetch API (POST https://api.fetch.tinyfish.ai).

    Returns a dict with 'results' list and 'errors' list, or an 'error' message.
    Never raises uncaught exceptions.
    """
    api_key = get_api_key()
    if not api_key:
        return {
            "results": [],
            "errors": [{"message": "TINYFISH_API_KEY environment variable is not set"}],
            "error": "TINYFISH_API_KEY is not configured",
        }

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "urls": [url],
        "format": format,
        "links": links,
    }

    last_error: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                FETCH_API_URL,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            if resp.status_code == 200:
                return resp.json()
            elif 400 <= resp.status_code < 500 and resp.status_code != 429:
                # Client error (e.g. 400 Bad Request, 401 Unauthorized, 403 Forbidden) - don't retry
                return {
                    "results": [],
                    "errors": [{"status": resp.status_code, "body": resp.text[:200]}],
                    "error": f"TinyFish Fetch API error (status {resp.status_code})",
                    "status_code": resp.status_code,
                }
            else:
                last_error = f"TinyFish Fetch returned HTTP {resp.status_code}"
        except requests.RequestException as exc:
            last_error = f"Network error during TinyFish Fetch: {type(exc).__name__}"

        if attempt < retries:
            time.sleep(1.0)

    return {
        "results": [],
        "errors": [{"message": last_error}],
        "error": last_error or "TinyFish Fetch failed after retries",
    }


def tf_search(
    query: str,
    timeout: int = DEFAULT_TIMEOUT,
    page: int = 0,
    retries: int = 1,
) -> dict[str, Any]:
    """Call TinyFish Search API (GET https://api.search.tinyfish.ai).

    Returns a dict with 'results' list, 'query', 'total_results', etc.
    Never raises uncaught exceptions.
    """
    api_key = get_api_key()
    if not api_key:
        return {
            "query": query,
            "results": [],
            "error": "TINYFISH_API_KEY is not configured",
        }

    headers = {
        "X-API-Key": api_key,
    }
    params: dict[str, Any] = {
        "query": query,
    }
    if page > 0:
        params["page"] = page

    last_error: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(
                SEARCH_API_URL,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            if resp.status_code == 200:
                return resp.json()
            elif 400 <= resp.status_code < 500 and resp.status_code != 429:
                return {
                    "query": query,
                    "results": [],
                    "error": f"TinyFish Search API error (status {resp.status_code})",
                    "status_code": resp.status_code,
                }
            else:
                last_error = f"TinyFish Search returned HTTP {resp.status_code}"
        except requests.RequestException as exc:
            last_error = f"Network error during TinyFish Search: {type(exc).__name__}"

        if attempt < retries:
            time.sleep(1.0)

    return {
        "query": query,
        "results": [],
        "error": last_error or "TinyFish Search failed after retries",
    }
