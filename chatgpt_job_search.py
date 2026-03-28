"""
chatgpt_job_search.py

Use OpenAI + web search to discover current job openings and company insights.

This module is intentionally beginner-friendly:
- Main job search function: search_jobs_with_chatgpt(...)
- Company insights function: get_company_insights(...)
"""

from __future__ import annotations

import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI


DEFAULT_SEARCH_MODEL = "gpt-5"
INDIA_STATES_AND_UTS = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
]


def _get_client() -> Optional[OpenAI]:
    """Create OpenAI client if OPENAI_API_KEY is available."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("[chatgpt_search] Missing OPENAI_API_KEY.")
        return None
    return OpenAI()


def _extract_json_array(text: str) -> List[Dict[str, str]]:
    """
    Try to parse JSON array from model output.
    We support raw JSON or markdown code fences.
    """
    if not text:
        return []

    cleaned = text.strip()

    # Remove markdown fences if present.
    cleaned = cleaned.replace("```json", "```")
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()

    # Direct parse first.
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError:
        pass

    # Fallback: find first JSON array in text.
    match = re.search(r"\[\s*\{.*\}\s*\]", cleaned, flags=re.DOTALL)
    if not match:
        return []

    try:
        data = json.loads(match.group(0))
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError:
        return []

    return []


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Parse a JSON object from model output."""
    if not text:
        return {}

    cleaned = text.strip().replace("```json", "```")
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()

    # Try strict JSON first.
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Fallback: find first {...} block.
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return {}

    block = match.group(0)
    try:
        data = json.loads(block)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Last fallback for python-style dict outputs.
    try:
        data = ast.literal_eval(block)
        if isinstance(data, dict):
            return data
    except (SyntaxError, ValueError):
        return {}

    return {}


def _months_to_human(months: int) -> str:
    years = months // 12
    rem = months % 12
    return f"{years} years {rem} months"


def _normalize_role(role: str) -> str:
    text = (role or "").strip().lower()
    if text == "product designer":
        return "Product Designer"
    if text == "ui designer":
        return "UI Designer"
    if text == "ux designer":
        return "UX Designer"
    return role


def _location_matches(location_text: str, selected_locations: List[str]) -> bool:
    """
    Check if a job location matches selected locations.

    Selected values are OR-based:
    - If any selected location matches, job is kept.
    """
    if not selected_locations:
        return True

    loc = (location_text or "").lower()
    selected = [x.strip() for x in selected_locations if x.strip()]
    if not selected:
        return True

    india_keywords = {"india", *{s.lower() for s in INDIA_STATES_AND_UTS}}
    remote_keywords = {"remote", "work from home", "wfh", "anywhere"}

    for value in selected:
        v = value.lower()
        if v == "remote":
            if any(k in loc for k in remote_keywords):
                return True
        elif v == "india (any)":
            if any(k in loc for k in india_keywords):
                return True
        else:
            if v in loc:
                return True

    return False


def search_jobs_with_chatgpt(
    job_positions: List[str],
    company_type: str,
    max_jobs: int = 20,
    experience_months: int = 0,
    company_name: str = "",
    selected_locations: Optional[List[str]] = None,
    model: str = DEFAULT_SEARCH_MODEL,
    timeout_seconds: int = 0,
) -> List[Dict[str, str]]:
    """
    Search jobs using ChatGPT web search and return normalized rows.

    Output keys:
    - company
    - role
    - location
    - description
    - apply_link
    - cover_letter
    - source
    - company_type
    """
    client = _get_client()
    if client is None:
        return []

    selected_roles = [_normalize_role(r) for r in job_positions if r.strip()]
    if not selected_roles:
        return []

    role_text = ", ".join(selected_roles)
    company_constraint = (
        f"ONLY for this company: {company_name.strip()}." if company_name.strip() else "Across multiple companies."
    )
    selected_locations = selected_locations or []
    location_constraint = ", ".join(selected_locations) if selected_locations else "All locations"

    primary_prompt = f"""
Use web search to find CURRENT active job openings.

Role filter:
{role_text}

Company type filter:
{company_type}

Candidate experience:
{_months_to_human(experience_months)}
Prefer jobs where required experience is less than or equal to this when explicitly stated.

Company name filter:
{company_constraint}

Location filter:
{location_constraint}

Return ONLY a JSON array (no extra text).
Each item must include:
- company
- role
- location
- description (2-5 lines summary, include required experience if known)
- apply_link (direct application URL, not just homepage)
- source (job board or company careers page)

Rules:
- Return up to {max_jobs} high-quality results.
- Prefer postings from last 30 days when possible.
- Skip duplicates and broken links.
- Role must be one of the selected roles or clearly equivalent.
""".strip()

    deep_prompt = f"""
Do a deeper second-pass web search for the same goal below and return additional results that were missed.

Role filter:
{role_text}

Company type filter:
{company_type}

Candidate experience:
{_months_to_human(experience_months)}
Prefer jobs where required experience is less than or equal to this when explicitly stated.

Company name filter:
{company_constraint}

Location filter:
{location_constraint}

Return ONLY a JSON array.
Each item must include: company, role, location, description, apply_link, source.

Rules:
- Focus on sources not already obvious (company careers pages, startup job boards, niche design job pages).
- Include only currently open roles.
- Return up to {max_jobs} rows.
""".strip()

    rows: List[Dict[str, str]] = []
    start_time = time.monotonic()
    for prompt in [primary_prompt, deep_prompt]:
        # Stop early if timeout budget is exhausted.
        if timeout_seconds > 0 and (time.monotonic() - start_time >= timeout_seconds):
            print("[chatgpt_search] Timeout budget reached before finishing deep search.")
            break
        try:
            response = client.responses.create(
                model=model,
                tools=[{"type": "web_search_preview"}],
                input=prompt,
            )
        except Exception as exc:
            print(f"[chatgpt_search] API/search error: {exc}")
            continue
        rows.extend(_extract_json_array((response.output_text or "").strip()))

    if not rows:
        print("[chatgpt_search] No parseable JSON results.")
        return []

    all_jobs: List[Dict[str, str]] = []
    seen_links = set()
    company_query = company_name.strip().lower()

    for row in rows:
        apply_link = str(row.get("apply_link", "")).strip()
        if not apply_link or apply_link in seen_links:
            continue

        role = str(row.get("role", "")).strip()
        company = str(row.get("company", "")).strip()
        if not role or not company:
            continue

        # If company is explicitly searched, keep only that company.
        if company_query and company_query not in company.lower():
            continue

        # Keep only selected roles by simple text containment.
        if not any(sel.lower().replace(" designer", "") in role.lower() for sel in selected_roles):
            continue

        # Apply location matching on returned rows as an extra safety filter.
        location = str(row.get("location", "")).strip()
        if not _location_matches(location, selected_locations):
            continue

        seen_links.add(apply_link)
        job = {
            "company": company,
            "role": role,
            "location": location,
            "description": str(row.get("description", "")).strip(),
            "apply_link": apply_link,
            "cover_letter": "",
            "source": str(row.get("source", "ChatGPT Web Search")).strip(),
            "company_type": company_type,
        }
        all_jobs.append(job)
        if len(all_jobs) >= max_jobs:
            break

    return all_jobs


def get_company_insights(
    company_name: str,
    job_positions: List[str],
    model: str = DEFAULT_SEARCH_MODEL,
) -> Dict[str, Any]:
    """
    Get high-level company insights from public web sources.

    Output keys:
    - company
    - public_buzz
    - positive_reviews
    - negative_reviews
    - median_tenure
    - notes
    """
    company = (company_name or "").strip()
    if not company:
        return {}

    client = _get_client()
    if client is None:
        return {}

    roles = ", ".join(_normalize_role(r) for r in job_positions if r.strip()) or "Product/UI/UX Designer roles"

    prompt = f"""
Use web search and return ONLY a JSON object with these keys:
- company
- public_buzz (short summary of what people are discussing recently)
- positive_reviews (3-6 bullet-style points in one string)
- negative_reviews (3-6 bullet-style points in one string)
- median_tenure (string; if unavailable, write "Not clearly available")
- notes (mention data quality and uncertainty)

Focus company:
{company}

Job context:
{roles}

Rules:
- Use only publicly available information.
- If data is uncertain, state uncertainty.
- Do not invent values.
""".strip()

    try:
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search_preview"}],
            input=prompt,
        )
    except Exception as exc:
        print(f"[chatgpt_search] Company insights error for '{company}': {exc}")
        return {}

    data = _extract_json_object((response.output_text or "").strip())
    if not data:
        return {}

    return {
        "company": str(data.get("company", company)).strip(),
        "public_buzz": str(data.get("public_buzz", "")).strip(),
        "positive_reviews": str(data.get("positive_reviews", "")).strip(),
        "negative_reviews": str(data.get("negative_reviews", "")).strip(),
        "median_tenure": str(data.get("median_tenure", "Not clearly available")).strip(),
        "notes": str(data.get("notes", "")).strip(),
    }


def get_company_people(
    company_name: str,
    model: str = DEFAULT_SEARCH_MODEL,
) -> Dict[str, Any]:
    """
    Use ChatGPT web search to find key people at a company.

    Output keys:
    - company
    - founder (dict with name, email)
    - hr (dict with name, title, email)
    - senior_designers (list of dicts with name, title, email)
    """
    company = (company_name or "").strip()
    if not company:
        return {}

    client = _get_client()
    if client is None:
        return {}

    prompt = f"""
Use web search to find key people at the company "{company}".

Return ONLY a JSON object with these keys:
- founder: object with "name" and "email"
- hr: object with "name", "title", and "email"
- senior_designers: array of objects, each with "name", "title", and "email"

For senior_designers, look for people with Senior Product Designer, Senior UX Designer, Senior UI Designer, or equivalent senior design roles at {company}.

Rules:
- Use only publicly available information from LinkedIn profiles, company websites, press releases, and news articles.
- For email addresses, look for publicly listed contact emails. If not found, write "Not publicly available".
- If a person or role cannot be identified, write "Not found" for name and email.
- Do not invent or guess any information.
""".strip()

    try:
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search_preview"}],
            input=prompt,
        )
    except Exception as exc:
        print(f"[chatgpt_search] Company people error for '{company}': {exc}")
        return {}

    data = _extract_json_object((response.output_text or "").strip())
    if not data:
        return {}

    return {
        "company": company,
        "founder": data.get("founder", {}),
        "hr": data.get("hr", {}),
        "senior_designers": data.get("senior_designers", []),
    }

