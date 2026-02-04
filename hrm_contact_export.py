#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import time
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

HRM_DOMAIN = os.getenv("HRM_DOMAIN", "hrm.trna.com.vn")


PAGING_PARAM_CANDIDATES = [
    "page", "pageNo", "page_no", "pageno", "p", "pageIndex", "page_index"
]


class SessionExpiredException(Exception):
    """Raised when session has expired"""
    pass


def build_hrm_domain_url(domain: str) -> str:
    """
    Convert domain to full hrm URL.
    Examples:
    - 'trna' -> 'https://hrm.trna.com.vn'
    - 'trna.com.vn' -> 'https://hrm.trna.com.vn'
    - 'hrm.trna.com.vn' -> 'https://hrm.trna.com.vn'
    
    Follows logic from login.py: https://hrm.{domain}.com.vn
    """
    if domain.startswith('https://'):
        return domain
    if domain.startswith('hrm.'):
        return f"https://{domain}"
    # Add .com.vn if not already present
    if not domain.endswith('.com.vn'):
        return f"https://hrm.{domain}.com.vn"
    return f"https://hrm.{domain}"


def login_and_get_session_v2(username: str, password: str, domain: str = HRM_DOMAIN) -> Tuple[requests.Session, str]:
    """
    Thay vì handle CAS trực tiếp, ta import login logic từ login.py
    """
    base_url = build_hrm_domain_url(domain)
    contact_search_url = f"{base_url}/index.php/pim/viewContactSearch"
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
    })
    
    payload = {
        "txtUsername": username,
        "txtPassword": password
    }
    
    login_url = f"{base_url}/index.php/auth/validateCredentials"
    
    try:
        print(f"[*] Logging in...", file=sys.stderr)
        r = session.post(login_url, data=payload, timeout=30)
        r.raise_for_status()
        
        # Make a request to contact search to trigger any post-login logic
        print(f"[*] Accessing contact search page...", file=sys.stderr)
        res = session.get(contact_search_url, params=[("tf[project_id][]", "1")])
        
    except requests.RequestException as e:
        raise RuntimeError(f"Login failed: {e}")
    
    phpsessid = session.cookies.get("PHPSESSID")
    if not phpsessid:
        raise RuntimeError("Login successful but PHPSESSID not found in cookies")
    
    print(f"[*] PHPSESSID: {phpsessid}", file=sys.stderr)
    return session, phpsessid


@dataclass
class PageParse:
    rows: List[Dict[str, str]]
    max_page: int
    current_page: int
    total_count_text: str


def build_params(project_id: int, page_param: Optional[str] = None, page: Optional[int] = None) -> List[Tuple[str, str]]:
    """
    The request uses: tf[favorite_contact][]=&tf[project_id][]=1368
    We'll keep it exactly like the UI.
    """
    params: List[Tuple[str, str]] = [
        ("tf[favorite_contact][]", ""),
        ("tf[project_id][]", str(project_id))
    ]
    if page_param and page is not None:
        params.append((page_param, str(page)))
    return params


def fetch_html(session: requests.Session, url: str, params: List[Tuple[str, str]], timeout: int = 30) -> str:
    r = session.get(url, params=params, timeout=timeout, allow_redirects=True)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} for {r.url}")
    return r.text


def parse_max_page_and_current(soup: BeautifulSoup) -> Tuple[int, int, str]:
    """
    From snippet:
      <ul class="paging top"> ... <a class="current">1</a> ... submitPage(4) ...
      <li class="desc">1-50 of 195</li>
    :contentReference[oaicite:3]{index=3}
    """
    paging = soup.select_one("ul.paging.top")
    max_page = 1
    current_page = 1
    total_text = ""

    if paging:
        # total count text
        desc = paging.select_one("li.desc")
        if desc:
            total_text = desc.get_text(strip=True)

        # current page
        cur = paging.select_one("a.current")
        if cur:
            try:
                current_page = int(cur.get_text(strip=True))
            except ValueError:
                current_page = 1

        # max page from submitPage(n)
        html = str(paging)
        nums = [int(n) for n in re.findall(r"submitPage\((\d+)\)", html)]
        if nums:
            max_page = max(nums)

    return max_page, current_page, total_text


def normalize_text(x: str) -> str:
    return re.sub(r"\s+", " ", x or "").strip()


def parse_rows(base_url: str, html: str) -> PageParse:
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

        badge_id = normalize_text(tds[0].get_text(" ", strip=True))

        # Fullname cell contains Vietnamese name span + hidden English name span
        fullname_cell = tds[1]
        en_span = fullname_cell.select_one("span.hide[id^=empEnglishName]")
        en_name = normalize_text(en_span.get_text(" ", strip=True)) if en_span else ""
        
        # Get Vietnamese name by extracting only visible spans (not the hidden English name)
        vn_spans = fullname_cell.select("span:not(.hide)")
        vn_name = normalize_text(" ".join([s.get_text(" ", strip=True) for s in vn_spans])) if vn_spans else normalize_text(fullname_cell.get_text(" ", strip=True).replace(en_name, "").strip())

        email_a = tds[3].select_one("a[href^='mailto:']")
        email = normalize_text(email_a.get_text(strip=True)) if email_a else normalize_text(tds[3].get_text(" ", strip=True))

        work_phone = normalize_text(tds[4].get_text(" ", strip=True))
        position = normalize_text(tds[5].get_text(" ", strip=True))
        location = normalize_text(tds[6].get_text(" ", strip=True))

        # Projects/Groups column:
        # contains "View Detail" link + multiple project/group links; join project names.
        projects_cell = tds[7]
        view_detail_a = projects_cell.select_one("a.text-bold[href*='viewContactSearchDetail']")
        view_detail_url = urljoin(base_url, view_detail_a["href"]) if view_detail_a and view_detail_a.get("href") else ""

        project_links = projects_cell.select("a.projects[href]")
        projects_list = [normalize_text(a.get_text(" ", strip=True)) for a in project_links]

        # Actions column contains Resume link sometimes
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
    Probe page 2 using candidate param names.
    We declare success if:
      - parsing works
      - current_page == 2 OR extracted rows differ from page 1
    """
    html1 = fetch_html(session, base_url, build_params(project_id), timeout=30)
    p1 = parse_rows(base_url, html1)

    # If only one page, no pagination needed.
    if p1.max_page <= 1:
        return ""

    for param in PAGING_PARAM_CANDIDATES:
        time.sleep(sleep)
        html2 = fetch_html(session, base_url, build_params(project_id, param, 2), timeout=30)
        p2 = parse_rows(base_url, html2)

        # Strong signal: UI says current page=2
        if p2.current_page == 2:
            return param

        # Weaker signal: different first badge id set
        if p2.rows and p1.rows:
            if p2.rows[0].get("Badge ID") != p1.rows[0].get("Badge ID"):
                return param

    raise RuntimeError(
        "Cannot auto-detect pagination param. "
        "Next step: capture the actual request of clicking page 2 in DevTools (Network tab) to see its querystring."
    )


def main():
    ap = argparse.ArgumentParser(description="Export HRM contact list to Excel")
    base_url_default = f"{build_hrm_domain_url(HRM_DOMAIN)}/index.php/pim/viewContactSearch"
    ap.add_argument("--base-url", default=base_url_default)
    ap.add_argument("--phpsessid", required=False, help="PHPSESSID cookie value (optional, will use saved or auto-login)")
    ap.add_argument("--project-id", required=True, type=int)
    ap.add_argument("--out", default="contacts.xlsx")
    ap.add_argument("--sleep", type=float, default=0.4)
    ap.add_argument("--force-login", action="store_true", help="Force new login, don't use saved session")
    args = ap.parse_args()

    # Get or create session
    session = None
    
    if args.phpsessid:
        # Use provided PHPSESSID
        print(f"[*] Using provided PHPSESSID", file=sys.stderr)
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        session.cookies.set("PHPSESSID", args.phpsessid)
    elif not args.force_login:
        # Try to load saved session
        from login import load_session, save_session, get_authenticated_session
        session, phpsessid = load_session()
        if session and phpsessid:
            print(f"[*] Using saved session", file=sys.stderr)
    
    # If no session, login
    if session is None:
        print(f"[*] Auto-logging in via CAS...", file=sys.stderr)
        from login import get_authenticated_session, save_session
        session = get_authenticated_session()
        save_session(session)
    
    phpsessid = session.cookies.get("PHPSESSID")
    if phpsessid:
        print(f"[OK] PHPSESSID: {phpsessid}", file=sys.stderr)

    # 1) Detect paging param (or confirm single page)
    try:
        page_param = detect_page_param(session, args.base_url, args.project_id, args.sleep)
    except SessionExpiredException:
        print(f"[!] Session expired, re-logging in...", file=sys.stderr)
        import os
        if os.path.exists(".session"):
            os.remove(".session")
        from login import get_authenticated_session, save_session
        session = get_authenticated_session()
        save_session(session)
        page_param = detect_page_param(session, args.base_url, args.project_id, args.sleep)

    # 2) Fetch page 1 + determine max page from paging widget
    try:
        html1 = fetch_html(session, args.base_url, build_params(args.project_id, page_param or None, 1 if page_param else None), timeout=30)
        p1 = parse_rows(args.base_url, html1)
    except SessionExpiredException:
        print(f"[!] Session expired, re-logging in...", file=sys.stderr)
        import os
        if os.path.exists(".session"):
            os.remove(".session")
        from login import get_authenticated_session, save_session
        session = get_authenticated_session()
        save_session(session)
        html1 = fetch_html(session, args.base_url, build_params(args.project_id, page_param or None, 1 if page_param else None), timeout=30)
        p1 = parse_rows(args.base_url, html1)

    all_rows: List[Dict[str, str]] = []
    seen_badges = set()

    def add(rows: List[Dict[str, str]]):
        nonlocal all_rows, seen_badges
        for r in rows:
            k = r.get("Badge ID") or str(r)
            if k in seen_badges:
                continue
            seen_badges.add(k)
            all_rows.append(r)

    add(p1.rows)
    max_page = p1.max_page

    # 3) Crawl remaining pages
    if page_param and max_page > 1:
        for page in range(2, max_page + 1):
            time.sleep(args.sleep)
            htmlp = fetch_html(session, args.base_url, build_params(args.project_id, page_param, page), timeout=30)
            pp = parse_rows(args.base_url, htmlp)
            add(pp.rows)
    else:
        # no pagination param => either 1 page, or server uses a POST/JS-only flow.
        # In that case, you'll need the page param from DevTools capture.
        pass

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
    
    df.to_excel(args.out, index=False, engine="openpyxl")

    print(f"[OK] Project {args.project_id}: exported {len(all_rows)} rows -> {args.out}")
    if p1.total_count_text:
        print(f"[INFO] Paging label: {p1.total_count_text}")


if __name__ == "__main__":
    main()
