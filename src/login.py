"""
CAS Authentication Module

Handles Central Authentication Service (CAS) login flow with session persistence.

This module provides functions to:
- Perform 4-step CAS authentication flow against the HRM system
- Save and load authenticated sessions from disk to avoid repeated logins
- Manage PHPSESSID cookies and session tokens

The authentication flow:
    1. POST credentials to HRM login endpoint
    2. HRM redirects to CAS server (Central Authentication Service)
    3. GET CAS login form and parse required fields
    4. POST credentials to CAS with form fields
    5. CAS validates credentials and provides Service Ticket
    6. Redirect back to HRM with Service Ticket
    7. HRM validates Service Ticket and creates session

Session caching:
    - Sessions are saved to a JSON file after successful authentication
    - Subsequent runs reuse cached sessions to avoid re-authentication
    - Sessions are automatically cleared on expiration

Environment Variables:
    HRM_DOMAIN: HRM server domain (default: "hrm.trna.com.vn")
    HRM_USERNAME: Login username (required)
    HRM_PASSWORD: Login password (required)
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

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
USERNAME = os.getenv("HRM_USERNAME")
PASSWORD = os.getenv("HRM_PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError("HRM_USERNAME and HRM_PASSWORD must be set in .env file")

CAS_SERVER = "https://access.trna.com.vn"
SESSION_FILE = config.get_session_file_path()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_hrm_url(domain: str) -> str:
    """
    Build the full HRM base URL from a domain name.
    
    Handles various domain formats and converts them to the standard HTTPS URL.
    
    Args:
        domain: Domain name in various formats:
            - Short format: "trna" -> "https://hrm.trna.com.vn"
            - Full format: "hrm.trna.com.vn" -> "https://hrm.trna.com.vn"
            - Already HTTPS: "https://..." -> used as-is
            
    Returns:
        Full HTTPS URL to HRM base (without path)
        
    Example:
        >>> build_hrm_url("trna")
        'https://hrm.trna.com.vn'
    """
    if domain.startswith('https://'):
        return domain
    if domain.endswith('.com.vn'):
        return f"https://hrm.{domain}"
    return f"https://hrm.{domain}.com.vn"


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

HRM_BASE = build_hrm_url(HRM_DOMAIN)
HRM_LOGIN_URL = f"{HRM_BASE}/index.php/auth/validateCredentials"
BASE_URL = f"{HRM_BASE}/index.php/pim/viewContactSearch"


def get_authenticated_session() -> requests.Session:
    """
    Perform CAS authentication and return an authenticated session.
    
    This function handles the complete 4-step CAS authentication flow:
    1. POST to HRM which redirects to CAS
    2. GET CAS login form
    3. POST credentials to CAS
    4. Follow redirect with Service Ticket back to HRM
    
    The returned session will have a valid PHPSESSID cookie set.
    
    Returns:
        requests.Session: An authenticated session object with valid cookies
        
    Raises:
        ValueError: If authentication fails or form parsing fails
        
    Example:
        >>> session = get_authenticated_session()
        >>> phpsessid = session.cookies.get("PHPSESSID")
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    # Step 1: POST to HRM login endpoint (redirects to CAS)
    print("[*] Step 1: POST to HRM login endpoint...", flush=True)
    r1 = session.post(HRM_LOGIN_URL, data={
        "txtUsername": USERNAME,
        "txtPassword": PASSWORD
    }, allow_redirects=False)
    print(f"[*] HRM returned {r1.status_code}", flush=True)
    
    if 'Location' in r1.headers:
        cas_redirect = r1.headers['Location']
        print(f"[*] Redirecting to CAS: {cas_redirect}", flush=True)
        
        # Step 2: GET CAS login form
        print("[*] Step 2: GET CAS login form...", flush=True)
        r2 = session.get(cas_redirect, allow_redirects=False)
        print(f"[*] CAS returned {r2.status_code}", flush=True)
        
        # Extract form fields from CAS page
        soup = BeautifulSoup(r2.text, "html.parser")
        form = soup.find("form", {"id": "fm1"})
        if not form:
            form = soup.find("form")
        
        if form:
            # Get all hidden fields from form
            payload = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                value = inp.get("value")
                if name:
                    payload[name] = value or ""
            
            # Add user credentials
            payload["username"] = USERNAME
            payload["password"] = PASSWORD
            
            # Get form action URL
            form_action = form.get("action", "").strip()
            print(f"[*] Form action from CAS: '{form_action}'", flush=True)
            
            # Step 3: Determine CAS submit URL
            if not form_action or form_action == "":
                cas_submit_url = r2.url  # POST to same URL we just fetched from
            elif form_action.startswith("/"):
                cas_submit_url = f"{CAS_SERVER}{form_action}"
            elif form_action.startswith("http"):
                cas_submit_url = form_action
            else:
                # Relative URL
                cas_submit_url = f"{CAS_SERVER}/cas/{form_action}"
            
            # Step 3: POST credentials to CAS
            print(f"[*] Step 3: POST credentials to CAS: {cas_submit_url}", flush=True)
            r3 = session.post(cas_submit_url, data=payload, allow_redirects=False)
            print(f"[*] CAS POST returned {r3.status_code}", flush=True)
            
            # Step 4: Follow redirect back to HRM with Service Ticket
            if 'Location' in r3.headers:
                hrm_redirect = r3.headers['Location']
                print(f"[*] Redirecting back to HRM: {hrm_redirect}", flush=True)
                
                print("[*] Step 4: Following redirect to HRM...", flush=True)
                r4 = session.get(hrm_redirect, allow_redirects=True)
                print(f"[*] HRM returned {r4.status_code}", flush=True)
    
    phpsessid = session.cookies.get("PHPSESSID")
    print(f"[*] Final PHPSESSID: {phpsessid}", flush=True)
    
    return session


# ============================================================================
# SESSION PERSISTENCE FUNCTIONS
# ============================================================================

def save_session(session: requests.Session) -> None:
    """
    Save session cookies and PHPSESSID to a JSON file on disk.
    
    This allows subsequent runs to reuse the authenticated session
    without needing to re-authenticate via CAS.
    
    Args:
        session: The authenticated requests.Session object to save
        
    Example:
        >>> session = get_authenticated_session()
        >>> save_session(session)
    """
    session_data = {
        "phpsessid": session.cookies.get("PHPSESSID"),
        "cookies": dict(session.cookies)
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)
    print(f"[*] Session saved to {SESSION_FILE}", flush=True)


def load_session() -> Tuple[Optional[requests.Session], Optional[str]]:
    """
    Load a previously saved session from disk.
    
    Reconstructs a requests.Session object with cached cookies and PHPSESSID.
    Returns None if the session file doesn't exist or can't be loaded.
    
    Returns:
        Tuple of:
            - requests.Session: The reconstructed session object, or None if load fails
            - str: The PHPSESSID value, or None if load fails
            
    Example:
        >>> session, phpsessid = load_session()
        >>> if session:
        ...     # Use cached session
        ...     pass
    """
    if not os.path.exists(SESSION_FILE):
        return None, None
    
    try:
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)
        
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        # Restore cookies from saved data
        for key, value in session_data.get("cookies", {}).items():
            session.cookies.set(key, value)
        
        print(f"[*] Session loaded from {SESSION_FILE}", flush=True)
        return session, session_data.get("phpsessid")
    except Exception as e:
        print(f"[!] Failed to load session: {e}", flush=True)
        return None, None

if __name__ == "__main__":
    # Debug: Test authentication
    session = get_authenticated_session()
    save_session(session)
    print("[OK] Authentication successful!")
