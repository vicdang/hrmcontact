#!/usr/bin/env python3
"""
HRM Contact Export Module

Main module for exporting HRM contact lists filtered by project to Excel files.

This module provides functionality to:
- Authenticate against HRM using CAS (Central Authentication Service)
- Fetch paginated contact lists filtered by project ID
- Automatically detect pagination parameters
- Parse HTML response tables and extract contact information
- Export contact data to Excel files with proper formatting

Key Features:
- Session caching: Reuses authenticated sessions to avoid repeated logins
- Automatic pagination: Detects and handles pagination automatically
- Robust HTML parsing: Uses BeautifulSoup to parse contact tables
- Excel export: Uses pandas and openpyxl for Excel file generation
- Error handling: Automatic session refresh on expiration

Export Data Columns:
- Badge ID: Employee identification number
- Fullname (VN): Vietnamese name
- Fullname (EN): English name  
- Email: Email address
- Work Phone: Work phone number
- Position: Job position
- Location: Work location
- Projects/Groups: Associated projects (pipe-separated)
- View Detail URL: Link to employee details page
- Resume URL: Link to resume file
- Project 1, 2, N: Individual project columns

Example Usage:
    python -m src.export --project-id 1368
    python -m src.export --project-id 1368 --out custom_contacts.xlsx

Environment Variables:
    HRM_DOMAIN: HRM server domain (default: "hrm.trna.com.vn")
    HRM_USERNAME: Login username (required)
    HRM_PASSWORD: Login password (required)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

HRM_DOMAIN = os.getenv("HRM_DOMAIN", "hrm.trna.com.vn")

# Candidate parameter names for pagination (tested in order)
PAGING_PARAM_CANDIDATES = [
    "page", "pageNo", "page_no", "pageno", "p", "pageIndex", "page_index"
]

# ============================================================================
# EXCEPTIONS
# ============================================================================


class SessionExpiredException(Exception):
    """
    Raised when the user session has expired and re-authentication is needed.
    
    This exception is raised when the HTML response contains CAS login page
    indicators, meaning the session is no longer valid.
    """
    pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_hrm_domain_url(domain: str) -> str:
    """
    Convert a domain name to a full HRM HTTPS URL.
    
    Handles various domain formats and converts them to the standard format.
    
    Args:
        domain: Domain in one of these formats:
            - Short: "trna" -> "https://hrm.trna.com.vn"
            - Full domain: "hrm.trna.com.vn" -> "https://hrm.trna.com.vn"
            - Already HTTPS: "https://..." -> returned as-is
            
    Returns:
        Complete HTTPS URL to HRM base (without path)
        
    Example:
        >>> build_hrm_domain_url("trna")
        'https://hrm.trna.com.vn'
    """
    if domain.startswith('https://'):
        return domain
    if domain.startswith('hrm.'):
        return f"https://{domain}"
    # Add .com.vn if not already present
    if not domain.endswith('.com.vn'):
        return f"https://hrm.{domain}.com.vn"
    return f"https://hrm.{domain}"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PageParse:
    """
    Data class representing parsed data from a single page of results.
    
    Attributes:
        rows: List of dictionaries containing contact information
        max_page: Maximum page number available in pagination
        current_page: Current page number
        total_count_text: Text from paging label (e.g., "1-50 of 195")
    """
    rows: List[Dict[str, str]]
    max_page: int
    current_page: int
    total_count_text: str


# ============================================================================
# PAGINATION & FETCHING FUNCTIONS
# ============================================================================

def build_params(project_id: int, page_param: Optional[str] = None, page: Optional[int] = None) -> List[Tuple[str, str]]:
    """
    Build query parameters for HRM contact search API.
    
    The HRM API uses a specific parameter format for filtering and pagination:
    - tf[favorite_contact][]: Filter for favorite contacts
    - tf[project_id][]: Filter by project ID
    - page_param: Pagination parameter (detected dynamically)
    
    Args:
        project_id: HRM project ID to filter by
        page_param: Name of pagination parameter (e.g., "page", "pageNo")
        page: Page number (only added if page_param is specified)
        
    Returns:
        List of (key, value) tuples suitable for requests library params
        
    Example:
        >>> build_params(1368)
        [('tf[favorite_contact][]', ''), ('tf[project_id][]', '1368')]
        >>> build_params(1368, "page", 2)
        [('tf[favorite_contact][]', ''), ('tf[project_id][]', '1368'), ('page', '2')]
    """
    params: List[Tuple[str, str]] = [
        ("tf[favorite_contact][]", ""),
        ("tf[project_id][]", str(project_id))
    ]
    if page_param and page is not None:
        params.append((page_param, str(page)))
    return params


def fetch_html(session: requests.Session, url: str, params: List[Tuple[str, str]], timeout: int = 30) -> str:
    """
    Fetch HTML content from HRM server.
    
    Handles redirect loops by detecting when the server is redirecting to
    authentication pages, which indicates session expiration.
    
    Args:
        session: Authenticated requests Session object
        url: Full URL to fetch from
        params: Query parameters as list of tuples
        timeout: Request timeout in seconds
        
    Returns:
        HTML content as string
        
    Raises:
        SessionExpiredException: If session has expired (too many redirects)
        RuntimeError: If HTTP status code is not 200
    """
    try:
        # Use allow_redirects=True but limit to 5 redirects for detection
        r = session.get(url, params=params, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code} for {r.url}")
        return r.text
    except requests.exceptions.TooManyRedirects as e:
        # Too many redirects usually means session expired and server is 
        # redirecting to login page in a loop
        print(f"[!] Too many redirects detected - session likely expired", file=sys.stderr)
        raise SessionExpiredException("Session expired (too many redirects), need to re-login")


# ============================================================================
# HTML PARSING FUNCTIONS
# ============================================================================

def parse_max_page_and_current(soup: BeautifulSoup) -> Tuple[int, int, str]:
    """
    Extract pagination information from BeautifulSoup object.
    
    Looks for:
    - Maximum page number from submitPage() JavaScript calls
    - Current page from <a class="current"> element
    - Total count text from <li class="desc"> (e.g., "1-50 of 195")
    
    Args:
        soup: BeautifulSoup object of the HTML page
        
    Returns:
        Tuple of:
            - max_page: Maximum page number (1 if no pagination)
            - current_page: Current page number (1 if not found)
            - total_text: Description text (e.g., "1-50 of 195")
            
    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '<ul class="paging top"><a class="current">2</a>...<li class="desc">51-100 of 195</li></ul>'
        >>> soup = BeautifulSoup(html, "html.parser")
        >>> parse_max_page_and_current(soup)
        (5, 2, '51-100 of 195')
    """
    paging = soup.select_one("ul.paging.top")
    max_page = 1
    current_page = 1
    total_text = ""

    if paging:
        # Extract total count text
        desc = paging.select_one("li.desc")
        if desc:
            total_text = desc.get_text(strip=True)

        # Extract current page number
        cur = paging.select_one("a.current")
        if cur:
            try:
                current_page = int(cur.get_text(strip=True))
            except ValueError:
                current_page = 1

        # Extract max page from submitPage(n) JavaScript calls
        html = str(paging)
        nums = [int(n) for n in re.findall(r"submitPage\((\d+)\)", html)]
        if nums:
            max_page = max(nums)

    return max_page, current_page, total_text


def normalize_text(x: str) -> str:
    """
    Normalize whitespace in text.
    
    Removes extra whitespace and strips leading/trailing spaces.
    
    Args:
        x: Input text (or None)
        
    Returns:
        Normalized text
        
    Example:
        >>> normalize_text("  Hello   World  ")
        'Hello World'
    """
    return re.sub(r"\s+", " ", x or "").strip()


def parse_rows(base_url: str, html: str) -> PageParse:
    """
    Parse contact rows from HTML table.
    
    Extracts contact information from HRM's result table:
    - Badge ID: First column
    - Vietnamese name: Second column visible text
    - English name: Hidden span with class "hide" 
    - Email: From mailto link or text
    - Work phone, position, location: Direct columns
    - Projects: From project links in projects column
    - URLs: From View Detail and Resume links
    
    Args:
        base_url: Base URL for resolving relative links
        html: HTML content containing the results table
        
    Returns:
        PageParse object with parsed data
        
    Raises:
        SessionExpiredException: If session has expired (CAS login page detected)
        RuntimeError: If results table not found or parsing fails
        
    Example:
        >>> page_parse = parse_rows("https://hrm.example.com", html_content)
        >>> len(page_parse.rows)
        50
        >>> page_parse.max_page
        4
    """
    soup = BeautifulSoup(html, "html.parser")

    max_page, current_page, total_text = parse_max_page_and_current(soup)

    table = soup.select_one("table#resultTable")
    if not table:
        # Check if it's a CAS login page (session expired)
        if "CAS - Central" in html or "Single Sign On" in html or "fm1" in html:
            raise SessionExpiredException("Session expired, need to re-login")
        raise RuntimeError("Cannot find table#resultTable (layout changed or not logged in).")

    out: List[Dict[str, str]] = []
    for tr in table.select("tbody tr"):
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue

        # Extract badge ID
        badge_id = normalize_text(tds[0].get_text(" ", strip=True))

        # Fullname cell contains Vietnamese name span + hidden English name span
        fullname_cell = tds[1]
        en_span = fullname_cell.select_one("span.hide[id^=empEnglishName]")
        en_name = normalize_text(en_span.get_text(" ", strip=True)) if en_span else ""
        
        # Get Vietnamese name by extracting only visible spans (not the hidden English name)
        vn_spans = fullname_cell.select("span:not(.hide)")
        vn_name = normalize_text(" ".join([s.get_text(" ", strip=True) for s in vn_spans])) if vn_spans else normalize_text(fullname_cell.get_text(" ", strip=True).replace(en_name, "").strip())

        # Extract email from mailto link or cell text
        email_a = tds[3].select_one("a[href^='mailto:']")
        email = normalize_text(email_a.get_text(strip=True)) if email_a else normalize_text(tds[3].get_text(" ", strip=True))

        # Extract other basic fields
        work_phone = normalize_text(tds[4].get_text(" ", strip=True))
        position = normalize_text(tds[5].get_text(" ", strip=True))
        location = normalize_text(tds[6].get_text(" ", strip=True))

        # Extract projects and links from projects column
        projects_cell = tds[7]
        view_detail_a = projects_cell.select_one("a.text-bold[href*='viewContactSearchDetail']")
        view_detail_url = urljoin(base_url, view_detail_a["href"]) if view_detail_a and view_detail_a.get("href") else ""

        project_links = projects_cell.select("a.projects[href]")
        projects_list = [normalize_text(a.get_text(" ", strip=True)) for a in project_links]

        # Extract resume URL from actions column
        actions_cell = tds[8] if len(tds) >= 9 else None
        resume_url = ""
        if actions_cell:
            resume_a = actions_cell.select_one("a[href*='viewResume']")
            if resume_a and resume_a.get("href"):
                resume_url = urljoin(base_url, resume_a["href"])

        out.append({
            "Badge ID": badge_id,
            "Fullname (VN)": vn_name,
            "Fullname (EN)": en_name,
            "Email": email,
            "Work Phone": work_phone,
            "Position": position,
            "Location": location,
            "Projects/Groups": " | ".join(projects_list),
            "View Detail URL": view_detail_url,
            "Resume URL": resume_url,
            "Projects List": projects_list,
        })

    return PageParse(rows=out, max_page=max_page, current_page=current_page, total_count_text=total_text)


def detect_page_param(session: requests.Session, base_url: str, project_id: int, sleep: float) -> str:
    """
    Automatically detect the pagination parameter name used by HRM.
    
    HRM may use different parameter names for pagination (page, pageNo, etc).
    This function tests common candidates by fetching page 2 with each one
    and comparing the results.
    
    Detection signals (in order of strength):
    1. Current page = 2 in parsed pagination widget
    2. Different rows on page 2 vs page 1
    3. If neither works, raises RuntimeError
    
    Args:
        session: Authenticated requests Session object
        base_url: Base URL of contact search page
        project_id: HRM project ID to filter by
        sleep: Delay between requests in seconds
        
    Returns:
        Name of pagination parameter (e.g., "page", "pageNo")
        Returns empty string if only one page exists
        
    Raises:
        RuntimeError: If pagination parameter cannot be detected
        
    Example:
        >>> param = detect_page_param(session, base_url, 1368, 0.4)
        >>> param
        'page'
    """
    html1 = fetch_html(session, base_url, build_params(project_id), timeout=30)
    p1 = parse_rows(base_url, html1)

    # If only one page, no pagination param needed
    if p1.max_page <= 1:
        return ""

    # Test each pagination parameter candidate
    for param in PAGING_PARAM_CANDIDATES:
        time.sleep(sleep)
        html2 = fetch_html(session, base_url, build_params(project_id, param, 2), timeout=30)
        p2 = parse_rows(base_url, html2)

        # Strong signal: UI says current page=2
        if p2.current_page == 2:
            return param

        # Weaker signal: different first badge ID means we got different data
        if p2.rows and p1.rows:
            if p2.rows[0].get("Badge ID") != p1.rows[0].get("Badge ID"):
                return param

    raise RuntimeError(
        "Cannot auto-detect pagination param. "
        "Next step: capture the actual request of clicking page 2 in DevTools (Network tab) to see its querystring."
    )


def export_contacts(
    project_id: int,
    output_file: Optional[str] = None,
    base_url: Optional[str] = None,
    phpsessid: Optional[str] = None,
    sleep: float = 0.4,
    force_login: bool = False
) -> None:
    """
    Main export function: Fetch HRM contacts and export to Excel.
    
    This function handles the complete workflow:
    1. Get or create an authenticated session (CAS login)
    2. Detect pagination parameter by testing page 2
    3. Fetch all pages of results
    4. Parse contact information from HTML tables
    5. Export to Excel with proper formatting
    
    Args:
        project_id: HRM project ID to filter by (required)
        output_file: Output Excel file path. If None, uses config.get_output_path()
        base_url: Custom base URL. If None, auto-built from HRM_DOMAIN
        phpsessid: Pre-existing PHPSESSID to use instead of login
        sleep: Delay between requests in seconds (default: 0.4)
        force_login: If True, ignore cached session and perform fresh CAS login
        
    Raises:
        SystemExit: If no rows are extracted (code 2)
        RuntimeError: If HTML parsing or pagination detection fails
        
    Example:
        >>> export_contacts(project_id=1368)
        [OK] Project 1368: exported 195 rows -> .../output/contacts.xlsx
        
        >>> export_contacts(1368, "custom.xlsx", force_login=True)
        [*] Auto-logging in via CAS...
        [OK] Project 1368: exported 195 rows -> custom.xlsx
    """
    # ====================================================================
    # 1. PREPARE OUTPUT AND BASE URLs
    # ====================================================================
    
    # Use config default if not provided
    if not output_file:
        output_file = config.get_output_path(config.generate_output_filename(project_id))
    
    if not base_url:
        base_url = f"{build_hrm_domain_url(HRM_DOMAIN)}/index.php/pim/viewContactSearch"

    # ====================================================================
    # 2. GET OR CREATE AUTHENTICATED SESSION
    # ====================================================================
    
    session = None
    
    if phpsessid:
        # Use provided PHPSESSID
        print(f"[*] Using provided PHPSESSID", file=sys.stderr)
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        session.cookies.set("PHPSESSID", phpsessid)
    elif not force_login:
        # Try to load saved session first
        from .login import load_session
        session, phpsessid = load_session()
        if session and phpsessid:
            print(f"[*] Using saved session", file=sys.stderr)
    
    # If no session available, perform CAS authentication
    if session is None:
        print(f"[*] Auto-logging in via CAS...", file=sys.stderr)
        from .login import get_authenticated_session, save_session
        session = get_authenticated_session()
        save_session(session)
    
    phpsessid = session.cookies.get("PHPSESSID")
    if phpsessid:
        print(f"[OK] PHPSESSID: {phpsessid}", file=sys.stderr)

    # ====================================================================
    # 3. DETECT PAGINATION PARAMETER
    # ====================================================================
    
    try:
        page_param = detect_page_param(session, base_url, project_id, sleep)
    except SessionExpiredException:
        print(f"[!] Session expired, re-logging in...", file=sys.stderr)
        if os.path.exists(config.SESSION_FILE):
            os.remove(config.SESSION_FILE)
        from .login import get_authenticated_session, save_session
        session = get_authenticated_session()
        save_session(session)
        page_param = detect_page_param(session, base_url, project_id, sleep)

    # ====================================================================
    # 4. FETCH FIRST PAGE AND GET MAX PAGE COUNT
    # ====================================================================
    
    try:
        html1 = fetch_html(session, base_url, build_params(project_id, page_param or None, 1 if page_param else None), timeout=30)
        p1 = parse_rows(base_url, html1)
    except SessionExpiredException:
        print(f"[!] Session expired, re-logging in...", file=sys.stderr)
        if os.path.exists(config.SESSION_FILE):
            os.remove(config.SESSION_FILE)
        from .login import get_authenticated_session, save_session
        session = get_authenticated_session()
        save_session(session)
        html1 = fetch_html(session, base_url, build_params(project_id, page_param or None, 1 if page_param else None), timeout=30)
        p1 = parse_rows(base_url, html1)

    # ====================================================================
    # 5. COLLECT ALL ROWS FROM ALL PAGES
    # ====================================================================
    
    all_rows: List[Dict[str, str]] = []
    seen_badges = set()

    def add_rows(rows: List[Dict[str, str]]) -> None:
        """Add rows to collection, skipping duplicates by Badge ID"""
        nonlocal all_rows, seen_badges
        for r in rows:
            badge_id = r.get("Badge ID") or str(r)
            if badge_id in seen_badges:
                continue
            seen_badges.add(badge_id)
            all_rows.append(r)

    add_rows(p1.rows)
    max_page = p1.max_page

    # Fetch remaining pages if pagination is available
    if page_param and max_page > 1:
        for page in range(2, max_page + 1):
            time.sleep(sleep)
            htmlp = fetch_html(session, base_url, build_params(project_id, page_param, page), timeout=30)
            pp = parse_rows(base_url, htmlp)
            add_rows(pp.rows)

    # ====================================================================
    # 6. EXPORT TO EXCEL
    # ====================================================================
    
    if not all_rows:
        print("No data extracted. Most likely: session expired or access denied.", file=sys.stderr)
        sys.exit(2)

    df = pd.DataFrame(all_rows)
    
    # Expand Projects List into separate columns (Project 1, Project 2, etc.)
    if "Projects List" in df.columns:
        max_projects = max(len(p) if isinstance(p, list) else 0 for p in df["Projects List"])
        for i in range(max_projects):
            df[f"Project {i+1}"] = df["Projects List"].apply(lambda x: x[i] if isinstance(x, list) and i < len(x) else "")
        df = df.drop(columns=["Projects List"])
    
    df.to_excel(output_file, index=False, engine="openpyxl")

    print(f"[OK] Project {project_id}: exported {len(all_rows)} rows -> {output_file}")
    if p1.total_count_text:
        print(f"[INFO] Paging label: {p1.total_count_text}")


def main() -> None:
    """
    Command-line interface entry point for HRM contact export.
    
    Parses command-line arguments and calls export_contacts() with appropriate parameters.
    
    Command-line Arguments:
        --project-id (required): HRM project ID to export contacts for
        --out (optional): Output Excel file path (default: output/contacts.xlsx from config)
        --base-url (optional): Custom HRM base URL
        --phpsessid (optional): Pre-existing PHPSESSID cookie to use
        --sleep (optional): Delay between HTTP requests in seconds (default: 0.4)
        --force-login (optional): Force new CAS authentication, ignore cached session
        
    Examples:
        # Basic usage (uses cached session or auto-login)
        python main.py --project-id 1368
        
        # Custom output file
        python main.py --project-id 1368 --out custom_contacts.xlsx
        
        # Force re-authentication
        python main.py --project-id 1368 --force-login
        
        # Use specific PHPSESSID
        python main.py --project-id 1368 --phpsessid "ST-xxxxx"
        
        # Custom delay between requests
        python main.py --project-id 1368 --sleep 1.0
    """
    ap = argparse.ArgumentParser(
        description="Export HRM contact list filtered by project to Excel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project-id 1368
  %(prog)s --project-id 1368 --out contacts_2024.xlsx
  %(prog)s --project-id 1368 --force-login
        """.strip()
    )
    base_url_default = f"{build_hrm_domain_url(HRM_DOMAIN)}/index.php/pim/viewContactSearch"
    
    ap.add_argument("--base-url", 
                    default=base_url_default,
                    help="HRM contact search base URL")
    ap.add_argument("--phpsessid",
                    required=False,
                    help="PHPSESSID cookie value (optional, uses saved or auto-login)")
    ap.add_argument("--project-id",
                    required=True,
                    type=int,
                    help="HRM project ID to export")
    ap.add_argument("--out",
                    default=None,
                    help=f"Output file path (default: {config.get_output_path()})")
    ap.add_argument("--sleep",
                    type=float,
                    default=0.4,
                    help="Delay between requests in seconds (default: 0.4)")
    ap.add_argument("--force-login",
                    action="store_true",
                    help="Force new CAS login, ignore cached session")
    
    args = ap.parse_args()

    export_contacts(
        project_id=args.project_id,
        output_file=args.out,
        base_url=args.base_url,
        phpsessid=args.phpsessid,
        sleep=args.sleep,
        force_login=args.force_login
    )


if __name__ == "__main__":
    main()
