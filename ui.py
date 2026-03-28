"""
ui.py

Main-page UI for non-developers.
Run this:
    python -m streamlit run ui.py
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from chatgpt_job_search import INDIA_STATES_AND_UTS, get_company_insights, get_company_people, search_jobs_with_chatgpt
from cover_letter_generator import generate_cover_letter


CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.csv")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "search_history.json")
JOB_POSITIONS = ["Product Designer", "UI Designer", "UX Designer"]
COMPANY_TYPES = ["Product based", "Agency", "Marketing", "Development firm", "IT", "All"]
LOCATION_FILTER_OPTIONS = ["Remote", "India (Any)"] + INDIA_STATES_AND_UTS
ROLE_FILTER_OPTIONS = ["Product Designer", "UI Designer", "UX Designer", "UX Researcher", "Design Lead"]
LOCATION_PILL_OPTIONS = ["Remote", "India", "Pune", "Hybrid"]
EXPERIENCE_BANDS = ["0-2 years", "2-5 years", "5-8 years", "8+ years"]
# 0 means no timeout (run until completion).
SEARCH_TIMEOUT_SECONDS = 0

_COPY_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2">'
    '</rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>'
)


def _inject_ui_css() -> None:
    """Dark frontend styling from provided CSS tokens."""
    bg = "#000000"
    card = "#1c1c1c"
    text = "#ffffff"
    muted = "#a3a3a3"
    border = "#333333"
    field_bg = "#3d3d3d"
    field_text = "#ffffff"
    chip_bg = "#3d3d3d"
    chip_text = "#ffffff"
    table_bg = "#1c1c1c"
    table_text = "#ffffff"
    primary = "#ffffff"
    primary_fg = "#000000"
    accent = "#3b82f6"
    accent_soft = "#60a5fa"
    accent_bg = "rgba(59,130,246,0.16)"
    shadow = "0px 1px 2px 0px hsl(0 0% 0% / 0.18)"
    css_template = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg: __BG__;
  --card: __CARD__;
  --text: __TEXT__;
  --muted: __MUTED__;
  --primary: __PRIMARY__;
  --primary-fg: __PRIMARY_FG__;
  --border: __BORDER__;
  --field-bg: __FIELD_BG__;
  --field-text: __FIELD_TEXT__;
  --chip-bg: __CHIP_BG__;
  --chip-text: __CHIP_TEXT__;
  --table-bg: __TABLE_BG__;
  --table-text: __TABLE_TEXT__;
  --accent: __ACCENT__;
  --accent-soft: __ACCENT_SOFT__;
  --accent-bg: __ACCENT_BG__;
  --shadow: __SHADOW__;
  --radius: 0.5rem;
}

.stApp {
  background: var(--bg) !important;
  color: var(--text);
  font-family: 'Inter', 'Segoe UI', sans-serif;
}

section.main > div {
  max-width: 980px;
  margin: 0 auto;
}

div[data-testid="stTabs"] button[role="tab"] {
  font-weight: 600;
  border-radius: var(--radius);
  color: var(--muted);
  background: transparent;
  border: 1px solid transparent;
}

div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  color: var(--text);
  border-bottom: 2px solid var(--text) !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
  display: none !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-border"] {
  background-color: var(--border) !important;
}

.app-header {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 18px;
  box-shadow: var(--shadow);
}

.app-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.01em;
  color: var(--text);
}

.app-subtitle {
  color: var(--muted);
  margin-top: 2px;
  font-size: 13px;
}

.section-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--text);
}

.search-caption {
  text-align: center;
  color: var(--muted);
  margin: 12px 0 12px 0;
  font-size: 14px;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.history-pill {
  color: var(--muted);
  font-size: 14px;
  font-weight: 600;
}

div[data-testid="stButton"] > button[kind="primary"] {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: var(--primary-fg) !important;
  font-weight: 600;
}

div[data-testid="stButton"] > button {
  border-radius: var(--radius);
  height: 40px;
  background: #ffffff !important;
  border: 1px solid var(--border);
  color: #000000 !important;
  font-weight: 500;
  transition: background 0.15s, border-color 0.15s;
}

div[data-testid="stButton"] > button * {
  color: #000000 !important;
}

div[data-testid="stButton"] > button p {
  color: #000000 !important;
}

div[data-testid="stButton"] > button:hover {
  background: #f0f0f0 !important;
  border-color: var(--muted);
}

div[data-testid="stButton"] > button[kind="primary"] * {
  color: var(--primary-fg) !important;
}

div[data-testid="stButton"] > button[kind="primary"] p {
  color: var(--primary-fg) !important;
}

div[data-testid="stTextInput"] input {
  border-radius: var(--radius) !important;
  background: var(--field-bg) !important;
  color: var(--field-text) !important;
  border: 1px solid var(--border) !important;
}

div[data-testid="stTextInput"] input::placeholder {
  color: var(--muted) !important;
}

div[data-testid="stTextInput"] input:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.15) !important;
}

div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  border-radius: var(--radius);
  background: var(--field-bg) !important;
  color: var(--field-text) !important;
  border-color: var(--border) !important;
}

div[data-baseweb="tag"] {
  background: var(--chip-bg) !important;
  color: var(--chip-text) !important;
  border-color: transparent !important;
  border-radius: 999px !important;
}

div[data-testid="stSlider"] [data-baseweb="slider"] {
  color: var(--accent) !important;
}

div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}

div[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stTickBar"] > div {
  background: var(--accent) !important;
}

div[data-testid="stSlider"] [data-baseweb="slider"] div[style*="background"] {
  background: #374151 !important;
}

label, .stCaption, .stMarkdown, .stText, p, span, div {
  color: var(--text);
}

.stCaption, [data-testid="stCaption"] {
  color: var(--muted) !important;
}

div[data-testid="stDataFrame"] {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--table-bg) !important;
  color: var(--table-text) !important;
  box-shadow: var(--shadow);
}

div[data-testid="stDataFrame"] * {
  color: var(--table-text) !important;
}

div[data-testid="stAlert"] {
  border-radius: var(--radius);
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
}

div[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
}

div[data-testid="stExpander"] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

hr {
  border-color: var(--border) !important;
}

.history-link {
  color: var(--muted);
  font-weight: 600;
  text-align: right;
}

div[data-testid="stPills"] button {
  border-radius: 999px !important;
  border: 1px solid #334155 !important;
  background: var(--card) !important;
  color: var(--text) !important;
  font-weight: 500;
}

div[data-testid="stPills"] button[aria-pressed="true"] {
  background: var(--accent-bg) !important;
  border-color: var(--accent) !important;
  color: #dbeafe !important;
  font-weight: 600;
}

div[data-testid="stPills"] button:hover {
  border-color: #475569 !important;
}

div[data-testid="stPills"] button:focus,
div[data-testid="stPills"] button:focus-visible {
  box-shadow: 0 0 0 2px rgba(59,130,246,0.30) !important;
  outline: none !important;
}

div[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.30) !important;
}

/* Neutral track + blue selected track only */
div[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child {
  background: #374151 !important;
}

div[data-testid="stSlider"] [data-baseweb="slider"] > div > div:nth-child(2) {
  background: var(--accent) !important;
}

div[data-testid="stDownloadButton"] > button {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: var(--radius) !important;
}

div[data-testid="stSpinner"] > div {
  color: var(--muted) !important;
}

h1, h2, h3, h4, h5, h6 {
  color: var(--text) !important;
}

div[data-testid="stMarkdownContainer"] h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text) !important;
}

div[data-testid="stForm"] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

section[data-testid="stSidebar"] {
  background: var(--card) !important;
  border-right: 1px solid var(--border) !important;
  padding-bottom: 70px !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
  padding-bottom: 80px !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div > div > div:last-child {
  position: fixed !important;
  bottom: 0 !important;
  left: 0 !important;
  width: calc(16rem + 32px) !important;
  background: #1c1c1c !important;
  border-top: 1px solid #333333 !important;
  padding: 10px 16px !important;
  z-index: 9999 !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div > div > div:last-child button {
  width: 100% !important;
  background: #ffffff !important;
  color: #000000 !important;
  font-weight: 600 !important;
  height: 40px !important;
  border-radius: 0.5rem !important;
  font-size: 14px !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div > div > div:last-child button p {
  color: #000000 !important;
}

section[data-testid="stSidebar"] * {
  color: var(--text);
}

section[data-testid="stSidebar"] h2 {
  color: var(--text) !important;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
}

section[data-testid="stSidebar"] hr {
  border-color: var(--border) !important;
}
</style>
    """
    css = (
        css_template.replace("__BG__", bg)
        .replace("__CARD__", card)
        .replace("__TEXT__", text)
        .replace("__MUTED__", muted)
        .replace("__BORDER__", border)
        .replace("__PRIMARY__", primary)
        .replace("__PRIMARY_FG__", primary_fg)
        .replace("__SHADOW__", shadow)
        .replace("__FIELD_BG__", field_bg)
        .replace("__FIELD_TEXT__", field_text)
        .replace("__CHIP_BG__", chip_bg)
        .replace("__CHIP_TEXT__", chip_text)
        .replace("__TABLE_BG__", table_bg)
        .replace("__TABLE_TEXT__", table_text)
        .replace("__ACCENT__", accent)
        .replace("__ACCENT_SOFT__", accent_soft)
        .replace("__ACCENT_BG__", accent_bg)
    )
    st.markdown(css, unsafe_allow_html=True)


def _months_to_label(months: int) -> str:
    years = months // 12
    rem = months % 12
    return f"{years} years {rem} months"


def _map_role_filters_to_search_roles(selected_roles: List[str]) -> List[str]:
    mapping = {
        "Product Designer": "Product Designer",
        "UI Designer": "UI Designer",
        "UX Designer": "UX Designer",
        "UX Researcher": "UX Designer",
        "Design Lead": "Product Designer",
    }
    result: List[str] = []
    for r in selected_roles:
        mapped = mapping.get(r)
        if mapped and mapped not in result:
            result.append(mapped)
    return result


def _map_location_pills_to_search_locations(selected_locations: List[str]) -> List[str]:
    mapping = {"India": "India (Any)"}
    out: List[str] = []
    for loc in selected_locations:
        mapped = mapping.get(loc, loc)
        if mapped not in out:
            out.append(mapped)
    return out


def _map_experience_band_to_months(value: str) -> int:
    return {
        "0-2 years": 24,
        "2-5 years": 60,
        "5-8 years": 96,
        "8+ years": 144,
    }.get(value, 60)


def _save_df_to_csv(df: pd.DataFrame, path: str) -> None:
    """
    Append new search results below existing rows in jobs.csv.
    If jobs.csv is locked (e.g., open in Excel), save to a timestamped fallback file.
    """
    if df.empty:
        st.warning("No data to save.")
        return
    try:
        if os.path.exists(path):
            existing = pd.read_csv(path, keep_default_na=False, encoding="utf-8-sig")
            all_cols = list(dict.fromkeys(list(existing.columns) + list(df.columns)))
            existing = existing.reindex(columns=all_cols, fill_value="")
            incoming = df.reindex(columns=all_cols, fill_value="")
            combined = pd.concat([existing, incoming], ignore_index=True)
            combined.to_csv(path, index=False, encoding="utf-8-sig")
        else:
            df.to_csv(path, index=False, encoding="utf-8-sig")
        st.info(f"Saved {len(df)} rows to `{os.path.basename(path)}`")
    except PermissionError:
        folder = os.path.dirname(path)
        fallback = os.path.join(folder, f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(fallback, index=False, encoding="utf-8-sig")
        st.warning(f"`jobs.csv` is locked. Saved to `{os.path.basename(fallback)}` instead. Close jobs.csv and retry.")
    except Exception as e:
        st.error(f"Failed to save CSV: {e}")


def _ordered_columns(df: pd.DataFrame) -> pd.DataFrame:
    required = ["company", "role", "location", "description", "apply_link", "cover_letter"]
    for col in required:
        if col not in df.columns:
            df[col] = ""
    extras = [c for c in ["source", "company_type"] if c in df.columns]
    return df[required + extras]


def _ensure_api_key(api_key_text: str) -> bool:
    key = (api_key_text or "").strip()
    if key:
        os.environ["OPENAI_API_KEY"] = key
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _run_with_timeout(
    fn,
    timeout_seconds: int,
    loader_label: str,
    *args,
    **kwargs,
):
    """
    Run any function with a visible loader.
    If timeout_seconds > 0, enforce timeout.
    If timeout_seconds == 0, allow unlimited runtime.
    """
    progress_box = st.empty()
    status_box = st.empty()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        start = time.monotonic()
        while not future.done():
            elapsed = time.monotonic() - start
            if timeout_seconds > 0:
                remaining = max(0, timeout_seconds - int(elapsed))
                ratio = min(1.0, elapsed / timeout_seconds)
                progress_box.progress(ratio, text=f"{loader_label} ({remaining}s left)")
            else:
                # Indefinite progress feedback while search is running.
                ratio = (elapsed % 20) / 20.0
                progress_box.progress(ratio, text=f"{loader_label} (running {int(elapsed)}s)")
            status_box.caption("Searching... please wait.")
            if timeout_seconds > 0 and elapsed >= timeout_seconds:
                progress_box.empty()
                status_box.empty()
                return False, None
            time.sleep(0.25)

        progress_box.empty()
        status_box.empty()
        return True, future.result()


def _load_history() -> Dict[str, List[Dict[str, Any]]]:
    if not os.path.exists(HISTORY_PATH):
        return {"company_searches": [], "filter_searches": []}
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {
                "company_searches": data.get("company_searches", []),
                "filter_searches": data.get("filter_searches", []),
            }
    except (json.JSONDecodeError, OSError):
        pass
    return {"company_searches": [], "filter_searches": []}


def _save_history(history: Dict[str, List[Dict[str, Any]]]) -> None:
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=True)


def _append_history(kind: str, payload: Dict[str, Any]) -> None:
    history = _load_history()
    bucket = "company_searches" if kind == "company" else "filter_searches"
    payload["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history[bucket].insert(0, payload)
    _save_history(history)


def _latest_filter_rows_from_history() -> List[Dict[str, Any]]:
    """
    Get the most recent filter-search output rows from persisted history.
    This helps show results upfront even after app restart.
    """
    history = _load_history()
    rows = history.get("filter_searches", [])
    if not rows:
        return []
    latest = rows[0] if isinstance(rows[0], dict) else {}
    output_rows = latest.get("output_rows", [])
    return output_rows if isinstance(output_rows, list) else []


def _compact_rows_for_history(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Keep a history-safe copy of output rows.
    We store key columns and shorten long text fields to avoid huge history files.
    """
    keep_cols = ["company", "role", "location", "description", "apply_link", "cover_letter", "source", "company_type"]
    work = df.copy()
    for col in keep_cols:
        if col not in work.columns:
            work[col] = ""
    work = work[keep_cols]

    def _short(text: Any, limit: int = 600) -> str:
        s = str(text or "")
        return s if len(s) <= limit else s[:limit] + "..."

    work["description"] = work["description"].map(lambda x: _short(x, 600))
    work["cover_letter"] = work["cover_letter"].map(lambda x: _short(x, 600))
    return work.to_dict(orient="records")


def _compact_company_details_for_history(people: Dict[str, Any], reviews: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keep a history-safe snapshot of company search details.
    """
    people = people if isinstance(people, dict) else {}
    reviews = reviews if isinstance(reviews, dict) else {}

    founder = people.get("founder", {}) if isinstance(people.get("founder", {}), dict) else {}
    hr = people.get("hr", {}) if isinstance(people.get("hr", {}), dict) else {}
    senior_raw = people.get("senior_designers", [])
    senior_designers: List[Dict[str, str]] = []
    if isinstance(senior_raw, list):
        for item in senior_raw[:8]:
            if isinstance(item, dict):
                senior_designers.append(
                    {
                        "name": str(item.get("name", "")),
                        "title": str(item.get("title", "")),
                        "email": str(item.get("email", "")),
                    }
                )

    def _short(value: Any, limit: int) -> str:
        text = str(value or "")
        return text if len(text) <= limit else text[:limit] + "..."

    return {
        "people_result": {
            "company": str(people.get("company", "")),
            "founder": {
                "name": str(founder.get("name", "")),
                "email": str(founder.get("email", "")),
            },
            "hr": {
                "name": str(hr.get("name", "")),
                "title": str(hr.get("title", "")),
                "email": str(hr.get("email", "")),
            },
            "senior_designers": senior_designers,
        },
        "review_result": {
            "company": str(reviews.get("company", "")),
            "public_buzz": _short(reviews.get("public_buzz", ""), 1500),
            "positive_reviews": _short(reviews.get("positive_reviews", ""), 2000),
            "negative_reviews": _short(reviews.get("negative_reviews", ""), 2000),
            "median_tenure": str(reviews.get("median_tenure", "")),
            "notes": _short(reviews.get("notes", ""), 1200),
        },
    }


def _render_company_history_table(company_rows: List[Dict[str, Any]]) -> None:
    """
    Render company-search history with key people and buzz summary columns.
    """
    if not company_rows:
        st.info("No company-search history yet.")
        return

    import html as _html

    table_rows = []
    for row in company_rows:
        company = str(row.get("company", "")).strip() or "Unknown"
        timestamp = str(row.get("timestamp", ""))
        people = row.get("people_result", {}) if isinstance(row.get("people_result", {}), dict) else {}
        reviews = row.get("review_result", {}) if isinstance(row.get("review_result", {}), dict) else {}
        founder_name = ""
        hr_name = ""
        senior_name = ""
        if isinstance(people.get("founder", {}), dict):
            founder_name = str(people.get("founder", {}).get("name", ""))
        if isinstance(people.get("hr", {}), dict):
            hr_name = str(people.get("hr", {}).get("name", ""))
        senior_designers = people.get("senior_designers", []) if isinstance(people.get("senior_designers", []), list) else []
        if senior_designers and isinstance(senior_designers[0], dict):
            senior_name = str(senior_designers[0].get("name", ""))
        buzz = str(reviews.get("public_buzz", ""))
        buzz_short = buzz if len(buzz) <= 120 else buzz[:120] + "..."
        table_rows.append(
            "<tr>"
            f"<td>{_html.escape(timestamp)}</td>"
            f"<td>{_html.escape(company)}</td>"
            f"<td>{_html.escape(founder_name or 'Not found')}</td>"
            f"<td>{_html.escape(hr_name or 'Not found')}</td>"
            f"<td>{_html.escape(senior_name or 'Not found')}</td>"
            "<td class=\"copy-cell-buzz\" "
            f"data-full=\"{_html.escape(buzz or 'No review summary')}\" "
            f"title=\"{_html.escape(buzz or 'No review summary')}\">"
            f"<span>{_html.escape(buzz_short or 'No review summary')}</span>"
            f"<span class=\"copy-btn-buzz\" onclick=\"copyBuzz(this)\">{_COPY_ICON_SVG}</span>"
            "</td>"
            "</tr>"
        )

    html_table = (
        "<!DOCTYPE html><html><head><style>"
        "html,body{margin:0;padding:0;background:#000;color:#e5e7eb;font-family:'Inter','Segoe UI',sans-serif;font-size:13px}"
        ".company-history-wrap{border:1px solid #2f3542;border-radius:8px;overflow-x:auto;background:#111827}"
        ".company-history-table{width:100%;border-collapse:collapse;min-width:980px}"
        ".company-history-table th{background:#111827;color:#9ca3af;font-weight:500;font-size:13px;"
        "text-transform:none;letter-spacing:0;padding:10px 14px;text-align:left;border-bottom:1px solid #2f3542;"
        "position:sticky;top:0;z-index:1}"
        ".company-history-table td{padding:10px 14px;border-bottom:1px solid #1f2937;color:#e5e7eb;max-width:320px;"
        "overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
        ".company-history-table tr:hover td{background:#1f2937}"
        ".copy-cell-buzz{position:relative;padding-right:36px !important}"
        ".copy-btn-buzz{position:absolute;right:8px;top:50%;transform:translateY(-50%);opacity:0;cursor:pointer;"
        "background:#111827;border:1px solid #374151;border-radius:4px;padding:3px 6px;color:#9ca3af;"
        "transition:opacity .15s,background .15s;display:inline-flex;align-items:center}"
        ".copy-cell-buzz:hover .copy-btn-buzz{opacity:1}"
        ".copy-btn-buzz:hover{background:#1f2937;color:#f9fafb}"
        ".copy-btn-buzz.copied{background:#2e7d32;border-color:#4caf50;color:#fff}"
        "</style></head><body>"
        '<div class="company-history-wrap"><table class="company-history-table">'
        "<thead><tr>"
        "<th>timestamp</th><th>company</th><th>founder</th><th>hr_name</th><th>senior_designer</th><th>public_buzz</th>"
        "</tr></thead><tbody>"
        + "".join(table_rows)
        + "</tbody></table></div>"
        + "<script>"
        "function copyBuzz(btn){"
        "var container=btn.closest('.copy-cell-buzz');if(!container){return;}"
        "var t=container.getAttribute('data-full')||'';"
        "var d=document.createElement('textarea');d.innerHTML=t;t=d.value;"
        "var old=btn.innerHTML;"
        "navigator.clipboard.writeText(t).then(function(){"
        "btn.textContent='\\u2713';btn.classList.add('copied');"
        "setTimeout(function(){btn.innerHTML=old;btn.classList.remove('copied');},1500);"
        "});"
        "}"
        "</script></body></html>"
    )
    height = min(560, 70 + len(company_rows) * 44)
    components.html(html_table, height=height, scrolling=True)


def _render_copyable_table(df: pd.DataFrame) -> None:
    """Render a DataFrame as an HTML table with copy icons on apply_link and cover_letter."""
    if df.empty:
        st.info("No results to display.")
        return

    import html as _html

    copy_cols = {"apply_link", "cover_letter"}
    trunc_limits: Dict[str, int] = {"description": 120, "cover_letter": 80}

    header_cells = ""
    for col in df.columns:
        col_esc = _html.escape(str(col))
        header_cells += '<th data-col="' + col_esc + '">' + col_esc + "</th>"

    body_rows = ""
    for _, row in df.iterrows():
        body_rows += "<tr>"
        for col in df.columns:
            val = str(row[col]) if pd.notna(row[col]) else ""
            full_esc = _html.escape(val)
            limit = trunc_limits.get(col)
            if limit and len(val) > limit:
                display_esc = _html.escape(val[:limit] + "\u2026")
            else:
                display_esc = full_esc
            if col in copy_cols and val.strip():
                body_rows += (
                    '<td class="copy-cell" data-col="' + _html.escape(str(col)) + '" title="' + full_esc + '">'
                    "<span>" + display_esc + "</span>"
                    '<span class="copy-btn" data-full="' + full_esc
                    + '" onclick="copyCell(this)">'
                    + _COPY_ICON_SVG
                    + "</span></td>"
                )
            else:
                body_rows += '<td data-col="' + _html.escape(str(col)) + '" title="' + full_esc + '">' + display_esc + "</td>"
        body_rows += "</tr>"

    height = min(600, 50 + len(df) * 42)
    page = (
        "<!DOCTYPE html><html><head><style>"
        "html,body{margin:0;padding:0;box-sizing:border-box;"
        "font-family:'Inter','Segoe UI',sans-serif;background:#000;color:#fff;font-size:13px}"
        ".tw{overflow-x:auto;border:1px solid #333;border-radius:8px;background:#1c1c1c}"
        "table{width:100%;border-collapse:collapse}"
        "th{background:#262626;color:#a3a3a3;font-weight:600;font-size:12px;"
        "text-transform:uppercase;letter-spacing:.03em;padding:10px 14px;"
        "text-align:left;border-bottom:1px solid #333;position:sticky;top:0;z-index:1}"
        "td{padding:8px 14px;border-bottom:1px solid #2a2a2a;max-width:280px;"
        "overflow:hidden;text-overflow:ellipsis;vertical-align:top;color:#e0e0e0}"
        "th[data-col='apply_link'],td[data-col='apply_link'],"
        "th[data-col='cover_letter'],td[data-col='cover_letter']{min-width:260px;max-width:260px}"
        "th[data-col='source'],td[data-col='source']{min-width:120px;max-width:120px}"
        "tr:hover td{background:#262626}"
        ".copy-cell{position:relative;padding-right:36px}"
        ".copy-btn{position:absolute;right:8px;top:50%;transform:translateY(-50%);"
        "opacity:0;cursor:pointer;background:#3d3d3d;border:1px solid #555;"
        "border-radius:4px;padding:3px 6px;color:#ccc;"
        "transition:opacity .15s,background .15s;display:inline-flex;align-items:center}"
        ".copy-cell:hover .copy-btn{opacity:1}"
        ".copy-btn:hover{background:#555;color:#fff}"
        ".copy-btn.copied{background:#2e7d32;border-color:#4caf50;color:#fff}"
        "</style></head><body>"
        '<div class="tw"><table>'
        "<thead><tr>" + header_cells + "</tr></thead>"
        "<tbody>" + body_rows + "</tbody>"
        "</table></div>"
        "<script>"
        "function copyCell(b){"
        "var t=b.getAttribute('data-full');"
        "var d=document.createElement('textarea');"
        "d.innerHTML=t;t=d.value;"
        "var o=b.innerHTML;"
        "navigator.clipboard.writeText(t).then(function(){"
        "b.textContent='\\u2713';"
        "b.classList.add('copied');"
        "setTimeout(function(){b.innerHTML=o;b.classList.remove('copied');},1500);"
        "});"
        "}"
        "</script></body></html>"
    )
    components.html(page, height=height, scrolling=True)


def _render_company_results(people: Dict[str, Any], reviews: Dict[str, Any]) -> None:
    """Display company people and review information."""
    company = people.get("company", "") or reviews.get("company", "")
    if not company:
        return

    if people:
        st.markdown(f"### People at {company}")
        founder = people.get("founder", {})
        hr = people.get("hr", {})
        designers = people.get("senior_designers", [])
        rows: List[Dict[str, str]] = []
        if isinstance(founder, dict) and founder:
            rows.append({
                "Role": "Founder",
                "Name": str(founder.get("name", "Not found")),
                "Email": str(founder.get("email", "Not publicly available")),
            })
        if isinstance(hr, dict) and hr:
            title = hr.get("title", "HR")
            rows.append({
                "Role": str(title) if title and title not in ("Not found", "") else "HR",
                "Name": str(hr.get("name", "Not found")),
                "Email": str(hr.get("email", "Not publicly available")),
            })
        if isinstance(designers, list):
            for d in designers:
                if isinstance(d, dict):
                    rows.append({
                        "Role": str(d.get("title", "Senior Designer")),
                        "Name": str(d.get("name", "Not found")),
                        "Email": str(d.get("email", "Not publicly available")),
                    })
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.info(f"Could not find people information for {company}.")

    if reviews:
        st.markdown(f"### Reviews & Buzz — {company}")
        buzz = reviews.get("public_buzz", "")
        if buzz:
            st.markdown(f"**What people are saying:** {buzz}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Positive**")
            st.markdown(reviews.get("positive_reviews", "") or "No data available.")
        with col2:
            st.markdown("**Negative**")
            st.markdown(reviews.get("negative_reviews", "") or "No data available.")
        tenure = reviews.get("median_tenure", "")
        if tenure:
            st.markdown(f"**Median Tenure:** {tenure}")
        notes = reviews.get("notes", "")
        if notes:
            st.caption(notes)


if "filters_applied" not in st.session_state:
    st.session_state.filters_applied = False
if "applied_filters" not in st.session_state:
    st.session_state.applied_filters = {}
if "latest_company_name" not in st.session_state:
    st.session_state.latest_company_name = ""
if "latest_company_results" not in st.session_state:
    st.session_state.latest_company_results = []
if "latest_company_insights" not in st.session_state:
    st.session_state.latest_company_insights = {}
if "latest_filter_results" not in st.session_state:
    st.session_state.latest_filter_results = []
if not st.session_state.latest_filter_results:
    st.session_state.latest_filter_results = _latest_filter_rows_from_history()
if "last_company_searched" not in st.session_state:
    st.session_state.last_company_searched = ""
if "company_people_results" not in st.session_state:
    st.session_state.company_people_results = {}
if "company_review_results" not in st.session_state:
    st.session_state.company_review_results = {}

st.set_page_config(page_title="AI Job Finder + Cover Letters", layout="wide", initial_sidebar_state="expanded")
_inject_ui_css()

# ── Sidebar: all filters and options ──
with st.sidebar:
    st.markdown(
        """
        <div class="app-header">
          <div class="top-nav">
            <div>
              <div class="app-title">AI Job Finder</div>
              <div class="app-subtitle">Product / UI / UX Roles</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("## Filters")

    selected_role_pills = st.pills(
        "ROLE",
        options=ROLE_FILTER_OPTIONS,
        default=["Product Designer", "UI Designer", "UX Designer"],
        selection_mode="multi",
    )
    selected_location_pills = st.pills(
        "LOCATION",
        options=LOCATION_PILL_OPTIONS,
        default=["India"],
        selection_mode="multi",
    )
    selected_experience_band = st.pills(
        "EXPERIENCE",
        options=EXPERIENCE_BANDS,
        default="2-5 years",
        selection_mode="single",
    )

    selected_company_type = st.selectbox("COMPANY TYPE", options=COMPANY_TYPES, index=COMPANY_TYPES.index("All"))
    max_jobs = st.slider("Max number of jobs to find", min_value=1, max_value=100, value=20)
    generate_letters = st.checkbox("Generate cover letters (uses OpenAI API)", value=False)

    st.markdown("---")
    api_key_input = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", label_visibility="collapsed")
    search_jobs_btn = st.button("Search Jobs", type="primary", use_container_width=True, key="sidebar_search_btn")

# ── Main page ──
main_tab, history_tab = st.tabs(["Search", "History"])

with main_tab:
    st.markdown('<div class="search-caption">Search a company to discover key people, emails, and reviews</div>', unsafe_allow_html=True)
    search_keyword = st.text_input(
        "Search company",
        key="global_keyword",
        placeholder="Type a company name and press Enter...",
        label_visibility="collapsed",
    )

    company_to_search = search_keyword.strip()
    if company_to_search and company_to_search != st.session_state.last_company_searched:
        if not _ensure_api_key(api_key_input):
            st.error("OpenAI API key is required. Paste it in the sidebar and try again.")
        else:
            st.session_state.last_company_searched = company_to_search
            with st.spinner(f"Looking up {company_to_search}..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    pf = pool.submit(get_company_people, company_to_search)
                    rf = pool.submit(
                        get_company_insights,
                        company_to_search,
                        ["Product Designer", "UI Designer", "UX Designer"],
                    )
                    st.session_state.company_people_results = pf.result()
                    st.session_state.company_review_results = rf.result()
            compact_details = _compact_company_details_for_history(
                st.session_state.company_people_results,
                st.session_state.company_review_results,
            )
            _append_history(
                "company",
                {
                    "company": company_to_search,
                    **compact_details,
                },
            )
    elif not company_to_search:
        st.session_state.last_company_searched = ""
        st.session_state.company_people_results = {}
        st.session_state.company_review_results = {}

    if st.session_state.company_people_results or st.session_state.company_review_results:
        _render_company_results(
            st.session_state.company_people_results,
            st.session_state.company_review_results,
        )
    elif st.session_state.last_company_searched:
        st.warning(f"No information found for '{st.session_state.last_company_searched}'. Try a different company name.")

    if st.session_state.latest_filter_results:
        results_df = _ordered_columns(pd.DataFrame(st.session_state.latest_filter_results))
        st.markdown(f"### Job Results ({len(results_df)})")
        _render_copyable_table(results_df)

    if search_jobs_btn:
        selected_positions = _map_role_filters_to_search_roles(selected_role_pills or [])
        selected_locations = _map_location_pills_to_search_locations(selected_location_pills or [])
        experience_months = _map_experience_band_to_months(str(selected_experience_band or "2-5 years"))
        if not selected_positions:
            st.error("Please select at least one job position.")
            st.stop()
        if not selected_locations:
            st.error("Please select at least one location.")
            st.stop()
        st.session_state.applied_filters = {
            "positions": selected_positions,
            "company_type": selected_company_type,
            "max_jobs": max_jobs,
            "locations": selected_locations,
            "experience_months": experience_months,
            "generate_letters": generate_letters,
        }
        st.session_state.filters_applied = True

    if search_jobs_btn and st.session_state.applied_filters:
        if not _ensure_api_key(api_key_input):
            st.error("OpenAI API key is missing. Paste it and try again.")
            st.stop()

        f = st.session_state.applied_filters
        ok, jobs = _run_with_timeout(
            search_jobs_with_chatgpt,
            SEARCH_TIMEOUT_SECONDS,
            "Searching jobs with AI",
            job_positions=list(f.get("positions", [])),
            company_type=str(f.get("company_type", "All")),
            max_jobs=int(f.get("max_jobs", 20)),
            experience_months=int(f.get("experience_months", 0)),
            company_name="",
            selected_locations=list(f.get("locations", [])),
        )
        if not ok:
            st.error("Job search timed out.")
            st.stop()

        if not jobs:
            _append_history(
                "filter",
                {
                    "positions": ", ".join(f.get("positions", [])),
                    "company_type": str(f.get("company_type", "All")),
                    "max_jobs": int(f.get("max_jobs", 20)),
                    "locations": ", ".join(f.get("locations", [])),
                    "experience": _months_to_label(int(f.get("experience_months", 0))),
                    "results_count": 0,
                    "output_rows": [],
                },
            )
            st.warning("No matching jobs found for these filters.")
            st.stop()

        df = _ordered_columns(pd.DataFrame(jobs))
        if bool(f.get("generate_letters", False)):
            with st.spinner("Generating cover letters..."):
                for i in range(len(df)):
                    company = str(df.at[i, "company"]).strip()
                    role = str(df.at[i, "role"]).strip()
                    description = str(df.at[i, "description"]).strip()
                    if company and role and description:
                        df.at[i, "cover_letter"] = generate_cover_letter(company=company, role=role, description=description)

        _append_history(
            "filter",
            {
                "positions": ", ".join(f.get("positions", [])),
                "company_type": str(f.get("company_type", "All")),
                "max_jobs": int(f.get("max_jobs", 20)),
                "locations": ", ".join(f.get("locations", [])),
                "experience": _months_to_label(int(f.get("experience_months", 0))),
                "results_count": len(df),
                "output_rows": _compact_rows_for_history(df),
            },
        )

        _save_df_to_csv(df, CSV_PATH)
        st.session_state.latest_filter_results = df.to_dict(orient="records")
        st.success(f"Found {len(df)} jobs. Data saved to jobs.csv")
        _render_copyable_table(df)

        filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name=filename,
            mime="text/csv",
        )
    # keep layout close to screenshot: no extra "latest results" blocks here

with history_tab:
    st.markdown("### Search History")
    history = _load_history()
    company_hist_tab, filter_hist_tab = st.tabs(["Company Searches", "Filter Searches"])

    with company_hist_tab:
        company_rows = history.get("company_searches", [])
        _render_company_history_table(company_rows)

    with filter_hist_tab:
        filter_rows = history.get("filter_searches", [])
        if filter_rows:
            # Main history grid: summary columns only (hide large output payload).
            summary_rows = []
            for row in filter_rows:
                summary_rows.append(
                    {
                        "timestamp": row.get("timestamp", ""),
                        "positions": row.get("positions", ""),
                        "company_type": row.get("company_type", ""),
                        "max_jobs": row.get("max_jobs", ""),
                        "locations": row.get("locations", ""),
                        "experience": row.get("experience", ""),
                        "results_count": row.get("results_count", 0),
                    }
                )
            df_hist = pd.DataFrame(summary_rows)
            df_hist.insert(0, "selected", False)
            edited = st.data_editor(
                df_hist,
                width="stretch",
                hide_index=True,
                column_config={"selected": st.column_config.CheckboxColumn("Select")},
                disabled=[c for c in df_hist.columns if c != "selected"],
            )
            selected_count = int(edited["selected"].sum()) if "selected" in edited.columns else 0
            st.caption(f"Selected rows: {selected_count}")

            # Show full output rows for selected history entries.
            if selected_count > 0:
                st.markdown("#### Output from selected history rows")
                selected_indices = edited.index[edited["selected"]].tolist()
                for idx in selected_indices:
                    original = filter_rows[idx]
                    out_rows = original.get("output_rows", [])
                    title = (
                        f"{original.get('timestamp', '')} | "
                        f"{original.get('positions', '')} | "
                        f"results={original.get('results_count', 0)}"
                    )
                    with st.expander(title, expanded=False):
                        if out_rows:
                            _render_copyable_table(pd.DataFrame(out_rows))
                        else:
                            st.info("No output rows stored for this search.")
        else:
            st.info("No filter-search history yet.")

