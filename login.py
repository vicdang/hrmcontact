import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json

# Load environment variables from .env file
load_dotenv()

HRM_DOMAIN = os.getenv("HRM_DOMAIN", "hrm.trna.com.vn")
USERNAME = os.getenv("HRM_USERNAME")
PASSWORD = os.getenv("HRM_PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError("HRM_USERNAME and HRM_PASSWORD must be set in .env file")

# Build full HRM URL
def build_hrm_url(domain):
    if not domain.endswith('.com.vn'):
        return f"https://hrm.{domain}.com.vn"
    return f"https://hrm.{domain}"

HRM_BASE = build_hrm_url(HRM_DOMAIN)
HRM_LOGIN_URL = f"{HRM_BASE}/index.php/auth/validateCredentials"
BASE_URL  = f"{HRM_BASE}/index.php/pim/viewContactSearch"
CAS_SERVER = "https://access.trna.com.vn"
SESSION_FILE = ".session"

def get_authenticated_session():
    """
    Handle CAS authentication flow:
    1. POST to HRM which redirects to CAS
    2. GET CAS login form
    3. POST credentials to CAS
    4. Follow redirect with Service Ticket back to HRM
    5. Return authenticated session
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    # Step 1: Redirect HRM validateCredentials to CAS login
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
            # Get all hidden fields
            payload = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                value = inp.get("value")
                if name:
                    payload[name] = value or ""
            
            # Add credentials
            payload["username"] = USERNAME
            payload["password"] = PASSWORD
            
            # Get form action URL
            form_action = form.get("action", "").strip()
            print(f"[*] Form action from CAS: '{form_action}'", flush=True)
            
            # If form action is empty, POST to the same URL (CAS login URL with params)
            if not form_action or form_action == "":
                # Get current URL from response history or use CAS login URL
                cas_submit_url = r2.url  # Use the URL we just GET from
            elif form_action.startswith("/"):
                cas_submit_url = f"{CAS_SERVER}{form_action}"
            elif form_action.startswith("http"):
                cas_submit_url = form_action
            else:
                # Relative URL
                cas_submit_url = f"{CAS_SERVER}/cas/{form_action}"
            
            print(f"[*] Step 3: POST credentials to CAS: {cas_submit_url}", flush=True)
            r3 = session.post(cas_submit_url, data=payload, allow_redirects=False)
            print(f"[*] CAS POST returned {r3.status_code}", flush=True)
            
            if 'Location' in r3.headers:
                hrm_redirect = r3.headers['Location']
                print(f"[*] Redirecting back to HRM: {hrm_redirect}", flush=True)
                
                # Step 4: Follow redirect back to HRM with Service Ticket
                print("[*] Step 4: Following redirect to HRM...", flush=True)
                r4 = session.get(hrm_redirect, allow_redirects=True)
                print(f"[*] HRM returned {r4.status_code}", flush=True)
    
    phpsessid = session.cookies.get("PHPSESSID")
    print(f"[*] Final PHPSESSID: {phpsessid}", flush=True)
    
    return session

def save_session(session):
    """Save PHPSESSID and cookies to file"""
    session_data = {
        "phpsessid": session.cookies.get("PHPSESSID"),
        "cookies": dict(session.cookies)
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)
    print(f"[*] Session saved to {SESSION_FILE}", flush=True)

def load_session():
    """Load PHPSESSID and cookies from file"""
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
        
        # Restore cookies
        for key, value in session_data.get("cookies", {}).items():
            session.cookies.set(key, value)
        
        print(f"[*] Session loaded from {SESSION_FILE}", flush=True)
        return session, session_data.get("phpsessid")
    except Exception as e:
        print(f"[!] Failed to load session: {e}", flush=True)
        return None, None

if __name__ == "__main__":
    session = get_authenticated_session()
    print("PHPSESSID =", session.cookies.get("PHPSESSID"))
    
    # Test request
    res = session.get(BASE_URL, params=[("tf[project_id][]", 1368)])
    print(res.status_code)