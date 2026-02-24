# Project Structure

## 📁 Directory Layout

```
employee/
├── src/                        # Source code package
│   ├── __init__.py            # Package initialization
│   ├── login.py               # CAS Authentication module
│   │   ├── get_authenticated_session()  # Main CAS flow
│   │   ├── save_session()               # Persist session
│   │   └── load_session()               # Load cached session
│   └── export.py              # Contact export module
│       ├── export_contacts()           # Main export function
│       ├── build_hrm_domain_url()      # URL builder
│       ├── parse_rows()                # HTML parsing
│       ├── detect_page_param()         # Pagination detection
│       └── main()                      # CLI entry point
│
├── output/                     # Exported files directory
│   ├── .gitkeep               # Placeholder for git tracking
│   └── *.xlsx                 # Generated exports (timestamped by project)
│
├── main.py                     # Entry point (runs src.export.main())
├── requirements.txt            # Python dependencies
├── .env                        # Credentials (git ignored)
├── .env.example               # Config template
├── .gitignore                 # Git ignore rules
├── cleanup.py                 # Cleanup old files (run once)
├── README.md                  # Main documentation
└── STRUCTURE.md               # This file
```

## 🔄 How It Works

### Entry Points

#### CLI Usage
```bash
# Using main.py (recommended) - default filename includes timestamp
python main.py --project-id 1368
# Output: output/20260224_180636_1368_contacts.xlsx

# Direct module usage
python -m src.export --project-id 1368
```

### Module Flow

```
main.py
  ↓
src/export.py::main()
  ├→ load_session() [from src/login.py]
  ├→ OR get_authenticated_session() [from src/login.py]
  ├→ detect_page_param()
  ├→ parse_rows()
  └→ Export to Excel
```

### CAS Authentication Flow

```
1. POST credentials to HRM /validateCredentials
   ↓ (redirects to CAS)
2. GET CAS login form
3. POST credentials to CAS form
   ↓ (returns Service Ticket)
4. GET redirect with Service Ticket back to HRM
   ↓ (establishes PHPSESSID)
5. Return authenticated Session object
```

## 📦 Key Modules

### `src/login.py` - Authentication
Handles Central Authentication Service (CAS) integration

**Functions:**
- `build_hrm_url(domain)` - Build HRM URL from domain shorthand
- `get_authenticated_session()` - Execute full CAS authentication flow
- `save_session(session)` - Persist session to `.session` file
- `load_session()` - Load cached session from file

**Constants:**
- `HRM_BASE` - Base HRM URL
- `HRM_LOGIN_URL` - Login endpoint
- `CAS_SERVER` - CAS server URL
- `SESSION_FILE` - Cache file path (`.session`)

### `src/export.py` - Contact Export
Handles HRM contact list extraction and Excel export

**Functions:**
- `export_contacts()` - Main export function with all options
- `build_hrm_domain_url()` - URL builder
- `detect_page_param()` - Auto-detect pagination parameter
- `fetch_html()` - Fetch page with session
- `parse_rows()` - Extract contact data from HTML
- `parse_max_page_and_current()` - Parse pagination info
- `build_params()` - Build request parameters
- `main()` - CLI interface

**Classes:**
- `SessionExpiredException` - Custom exception for expired sessions
- `PageParse` - Dataclass for parsed page data

## 🔐 Session Management

### Session File Format (`.session`)
```json
{
    "phpsessid": "ST-213390--cptH-CIvetBTkFVHjqdUGYcItg-access",
    "cookies": {
        "PHPSESSID": "ST-213390--cptH-CIvetBTkFVHjqdUGYcItg-access"
    }
}
```

### Session Lifecycle
1. **First run**: No `.session` file
   - Auto-login via CAS
   - Save session to `.session`
   - Export data

2. **Subsequent runs**: `.session` file exists
   - Load session from file
   - Use saved PHPSESSID
   - Export data (faster, no login)

3. **Session expires**: Detected during fetch
   - Raise `SessionExpiredException`
   - Delete `.session` file
   - Auto re-login
   - Save new session
   - Retry export

4. **Force login**: `--force-login` flag
   - Ignore `.session` file
   - Perform new login
   - Save new session

## 📄 Configuration Files

### `.env` (Credentials - Git Ignored)
```env
HRM_DOMAIN=trna
HRM_USERNAME=your_username
HRM_PASSWORD=your_password
```

### `.env.example` (Template - Git Tracked)
Template for new users to copy

### `.gitignore` (Git Rules)
Ignores:
- `.env` - Sensitive credentials
- `.session` - Cached sessions
- `.venv/`, `venv/` - Virtual environments
- `*.xlsx` - Exported files
- `__pycache__/`, `*.pyc` - Python cache
- `output/*` - Output files (except `.gitkeep`)

## 🗑️ Migration from Old Structure

### Old Files to Remove
```
❌ login.py → ✅ src/login.py
❌ hrm_contact_export.py → ✅ src/export.py
❌ test_login.py → (optional, old tests)
❌ test_export.py → (optional, old tests)
❌ test_session.py → (optional, old tests)
❌ debug_form.py → (debug file)
❌ debug_response.html → (debug file)
```

### Cleanup
Run once to remove old files:
```bash
python cleanup.py
```

## 🚀 Usage Examples

### Standard Export
```bash
# First time (auto-login, save session)
python main.py --project-id 1368

# Next time (use cached session)
python main.py --project-id 1368
```

### With Options
```bash
# Custom output file
python main.py --project-id 1368 --out output/my_contacts.xlsx

# Force new login
python main.py --project-id 1368 --force-login

# Custom PHPSESSID
python main.py --project-id 1368 --phpsessid "ST-xxx"

# Adjust request delay
python main.py --project-id 1368 --sleep 1
```

## 🔧 Development

### Adding New Features
1. Add functions to `src/export.py` or `src/login.py`
2. Update CLI in `src/export.py::main()`
3. Test via `python main.py --help`

### Testing
```bash
# Basic test
python main.py --project-id 1368

# Verbose output
python main.py --project-id 1368 --sleep 1

# Force login to test CAS
python main.py --project-id 1368 --force-login
```

### Debugging
- Check `.session` file: `cat .session | head -c 100`
- Force new login: `Remove-Item .session -Force`
- View output: Check `output/` folder for timestamped Excel files

## 📋 Dependencies

See `requirements.txt`:
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `openpyxl` - Excel file generation
- `python-dotenv` - Environment variables

## 📝 Notes

- **Session TTL**: ~24 hours (default)
- **Pagination**: Auto-detected, handles unlimited records
- **Output Format**: `.xlsx` (Excel format)
- **Python Version**: 3.6+
- **Platform**: Windows/Linux/macOS
