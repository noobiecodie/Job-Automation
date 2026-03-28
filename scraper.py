"""
scraper.py

Beginner-friendly job scraper for UI/UX/Product Design roles.

We scrape from RemoteOK because it is:
- Publicly accessible
- Lightweight (simple HTML pages)
- Friendly for beginners (no login required)

This module exposes ONE main function:
    scrape_jobs(keywords: list[str], max_jobs_per_keyword: int = 15) -> list[dict]
which returns a list of job dictionaries ready to be saved to CSV.
"""

from __future__ import annotations

import re
import time
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup


# A polite, browser-like user-agent helps avoid simple blocks.
# This is NOT a guarantee; websites can still block bots sometimes.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def _safe_text(value: Optional[str]) -> str:
    """Return clean text, or empty string if missing."""
    return (value or "").strip()


def _get_soup(url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
    """
    Download a page and return a BeautifulSoup parser.

    Error handling:
    - If the website request fails, we return None (and the caller can continue).
    """
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print(f"[scraper] Request failed: {url}\n  Reason: {exc}")
        return None


def _html_to_text(html: str) -> str:
    """
    Convert HTML into readable plain text using BeautifulSoup.

    We use this because job descriptions often contain HTML tags like <p>, <ul>, etc.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    # Clean up common "weird" whitespace characters that often appear in scraped text.
    text = text.replace("\u00a0", " ").replace("\ufeff", "").strip()
    # Keep it reasonably sized (CSV friendly)
    return text[:8000]


def _keyword_to_remoteok_url(keyword: str) -> str:
    """
    Convert a keyword like "UX Designer" into a RemoteOK search URL.

    RemoteOK supports URLs such as:
    - https://remoteok.com/remote-ux-jobs
    - https://remoteok.com/remote-ui-jobs
    - https://remoteok.com/remote-product-designer-jobs

    We implement a simple mapping for the 3 required keywords.
    If something else is passed, we fall back to RemoteOK's general search query.
    """
    normalized = keyword.lower().strip()

    if normalized == "ux designer":
        return "https://remoteok.com/remote-ux-jobs"
    if normalized == "ui designer":
        return "https://remoteok.com/remote-ui-jobs"
    if normalized == "product designer":
        return "https://remoteok.com/remote-product-designer-jobs"

    # Fallback: query parameter search (works for many terms)
    # Example: https://remoteok.com/remote-ux+designer-jobs
    term = normalized.replace(" ", "+")
    return f"https://remoteok.com/remote-{term}-jobs"


def _fetch_remoteok_api(timeout: int = 20) -> Optional[List[dict]]:
    """
    Fetch RemoteOK's public API.

    Why use the API:
    - It's far more reliable than scraping HTML (which can change anytime)
    - We still use BeautifulSoup in this project to clean HTML descriptions into text

    RemoteOK API returns a list:
    - First item is metadata
    - Remaining items are job objects
    """
    api_url = "https://remoteok.com/api"
    try:
        response = requests.get(api_url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        return None
    except requests.RequestException as exc:
        print(f"[scraper] Request failed: {api_url}\n  Reason: {exc}")
        return None
    except ValueError as exc:
        print(f"[scraper] Could not parse JSON from API.\n  Reason: {exc}")
        return None


def _keyword_matches_role(keyword: str, role: str) -> bool:
    """
    Simple, beginner-friendly matching.

    Example:
    - keyword: "UX Designer"
    - role: "UX/UI Designer"
    This should match, even though the text is not identical.
    """
    kw_words = [w.strip().lower() for w in keyword.split() if w.strip()]
    role_lower = (role or "").lower()
    return all(word in role_lower for word in kw_words)


def _passes_experience_filter(text: str, experience_min: int) -> bool:
    """
    Check whether a job description/title passes the experience filter.

    Idea:
    - You select how many years of experience you have.
    - We keep jobs where the job's required years is LESS THAN OR EQUAL to yours.
    - If we can't detect a number of years, we keep the job (to avoid hiding good roles).
    """
    if experience_min <= 0:
        # 0 means "show everything".
        return True

    if not text:
        return True

    # Look for patterns like "3+ years of experience", "5 yrs experience", etc.
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s+of\s+experience",
        r"(\d+)\+?\s*(?:years?|yrs?)\s+experience",
        r"(\d+)\+?\s*(?:years?|yrs?)",
    ]

    matches: List[int] = []
    for pat in patterns:
        for m in re.findall(pat, text, flags=re.IGNORECASE):
            try:
                matches.append(int(m))
            except ValueError:
                continue

    if not matches:
        # If we can't parse any explicit number, keep the job.
        return True

    required_years = min(matches)
    return required_years <= experience_min


def _normalize_boards(boards: Optional[List[str]]) -> List[str]:
    """
    Map different UI labels to internal board names.
    """
    mapping = {
        "remoteok": "RemoteOK",
        "wellfound": "Wellfound",
        "wellfound (angellist)": "Wellfound",
        "uplers": "Uplers",
    }

    result: List[str] = []
    for b in boards or ["RemoteOK"]:
        key = b.strip().lower()
        name = mapping.get(key)
        if name and name not in result:
            result.append(name)

    if not result:
        result = ["RemoteOK"]

    return result


def scrape_jobs(
    keywords: List[str],
    max_jobs_per_keyword: int = 15,
    location_filter: str = "All",
    boards: Optional[List[str]] = None,
    experience_min: int = 0,
) -> List[Dict[str, str]]:
    """
    Scrape jobs from RemoteOK for the provided keywords.

    Returns a list of dicts with these keys (matching your CSV columns):
    - company
    - role
    - location
    - description
    - apply_link
    - cover_letter (empty for now; main.py will fill it)

    Location filter:
    - "All": do not filter by location
    - "India": keep jobs where location contains "India"
    - "Remote": keep jobs where location contains "Remote"

    Boards:
    - Currently implemented: "RemoteOK"
    - "Wellfound" and "Uplers" are recognized but skipped in this beginner version

    Experience filter:
    - experience_min = your years of experience
    - We KEEP jobs where the posting's required years <= your years.
    - If the posting does not mention years clearly, we keep it.

    Error handling:
    - Website failures: continue to the next keyword.
    - Missing data: fill with empty strings.
    """
    all_jobs: List[Dict[str, str]] = []
    seen_links: Set[str] = set()

    normalized_boards = _normalize_boards(boards)

    # Explain limitations of extra boards in this version.
    if "Wellfound" in normalized_boards:
        print(
            "[scraper] Wellfound / AngelList currently requires a real browser "
            "(JS + anti-bot). Skipping this source in this beginner-friendly version."
        )
    if "Uplers" in normalized_boards:
        print(
            "[scraper] Uplers jobs are not reliably accessible via simple HTML requests. "
            "Skipping this source in this version."
        )

    if "RemoteOK" not in normalized_boards:
        print("[scraper] No supported job boards selected (RemoteOK is required in this version).")
        return all_jobs

    api_data = _fetch_remoteok_api()
    if not api_data:
        return all_jobs

    # First element is usually metadata; jobs start from index 1.
    jobs_from_api = [item for item in api_data[1:] if isinstance(item, dict)]

    for keyword in keywords:
        print(f"[scraper] Searching '{keyword}' on RemoteOK...")
        found = 0

        # We filter by matching the keyword in the job title/position.
        for item in jobs_from_api:
            if found >= max_jobs_per_keyword:
                break

            role = _safe_text(item.get("position"))
            if not _keyword_matches_role(keyword=keyword, role=role):
                continue

            company = _safe_text(item.get("company"))
            location = _safe_text(item.get("location") or "Remote")

            # Apply the location filter (simple string matching to keep it beginner-friendly).
            lf = (location_filter or "All").strip().lower()
            if lf == "india" and "india" not in location.lower():
                continue
            if lf == "remote" and "remote" not in location.lower():
                continue

            # RemoteOK API fields:
            # - "description" is often HTML
            # - "url" is a RemoteOK job page
            # - "apply_url" may exist for direct application
            description = _html_to_text(_safe_text(item.get("description")))
            apply_link = _safe_text(item.get("apply_url") or item.get("url") or "")

            # Combine title + description for experience parsing.
            full_text = f"{role}\n{description}"
            if not _passes_experience_filter(full_text, experience_min=experience_min):
                continue

            # If key data is missing, we still keep the job, but with empty strings.
            # Also avoid duplicates (RemoteOK can return the same job for multiple keywords).
            if apply_link and apply_link in seen_links:
                continue
            if apply_link:
                seen_links.add(apply_link)

            job = {
                "company": company,
                "role": role,
                "location": location,
                "description": description,
                "apply_link": apply_link,
                "cover_letter": "",  # filled later
            }

            all_jobs.append(job)
            found += 1

            # Small delay: friendlier to the API (and reduces accidental rate limiting)
            time.sleep(0.2)

        print(f"[scraper] Found {found} jobs for '{keyword}'.")

    return all_jobs

