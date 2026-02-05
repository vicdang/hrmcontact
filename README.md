# HRM Contact Export Tool

Automated tool for exporting employee contact lists from the TRNA HRM (Human Resource Management) system to Excel files.

## 📋 Features

- ✅ **CAS Authentication**: Automatic login via Central Authentication Service (CAS)
- ✅ **Session Caching**: Saves authentication session to avoid repeated logins
- ✅ **Automatic Re-login**: Automatically re-authenticates when session expires
- ✅ **Automatic Pagination**: Detects and handles pagination automatically
- ✅ **Data Export**: Exports complete contact information to Excel format
- ✅ **Project Filtering**: Filter contacts by HRM Project ID
- ✅ **Type-Safe Code**: Full type hints and comprehensive docstrings
- ✅ **Error Handling**: Robust error handling with informative error messages

## 🚀 Installation

### 1. Clone or download the project
```bash
cd employee
```

### 2. Create a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure credentials
Copy `.env.example` to `.env` and fill in your HRM credentials:
```env
HRM_DOMAIN=trna
HRM_USERNAME=your_username
HRM_PASSWORD=your_password
```

## 📖 Usage

### First Run (Auto-login)
```bash
python main.py --project-id 1368
```

The script will:
1. Authenticate against HRM via CAS
2. Cache the session in `.session` file
3. Export contacts to `output/contacts.xlsx`

### Subsequent Runs (Using Cached Session)
```bash
python main.py --project-id 1368
```

No login needed - automatically uses the cached session.

### Force Fresh Login
```bash
python main.py --project-id 1368 --force-login
```

Clears the cached session and performs a fresh CAS authentication.

### Custom Output Filename
```bash
python main.py --project-id 1368 --out "my_contacts.xlsx"
```

### Using Specific PHPSESSID
```bash
python main.py --project-id 1368 --phpsessid "ST-xxxxx"
```

## 📋 Command-line Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--project-id` | Integer | ✅ Yes | - | HRM project ID to export |
| `--out` | Path | ❌ No | `output/contacts.xlsx` | Output Excel file path |
| `--force-login` | Flag | ❌ No | False | Force new CAS login |
| `--phpsessid` | String | ❌ No | - | Use specific PHPSESSID cookie |
| `--sleep` | Float | ❌ No | 0.4 | Delay between requests (seconds) |
| `--base-url` | URL | ❌ No | Auto-detected | Custom HRM base URL |

## 📁 Project Structure

```
employee/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── login.py                 # CAS authentication module
│   └── export.py                # Export logic
├── output/                      # Directory for Excel exports
├── main.py                      # Entry point
├── config.py                    # Centralized configuration
├── requirements.txt             # Python dependencies
├── .env                         # Credentials (git-ignored)
├── .env.example                 # Config template
├── .gitignore                   # Git exclusion rules
└── README.md                    # This file
```

## 🔑 Session Management

- **Session File**: `.session` (JSON format)
- **Git Policy**: Never committed (see `.gitignore`)
- **Behavior**:
  1. First run: Performs CAS authentication, saves session
  2. Subsequent runs: Reuses cached session if available
  3. Session expires: Automatically detects expiration and re-authenticates
  4. Force reset: Use `--force-login` flag

## 📤 Exported Data

The Excel file contains the following columns:

| Column | Description |
|--------|-------------|
| Badge ID | Employee identification number |
| Fullname (VN) | Employee name in Vietnamese |
| Fullname (EN) | Employee name in English |
| Email | Work email address |
| Work Phone | Work phone number |
| Position | Job position/title |
| Location | Work location/office |
| Projects/Groups | Associated projects (pipe-separated) |
| View Detail URL | Link to employee details page |
| Resume URL | Link to employee resume |
| Project 1, 2, N | Individual project columns (auto-expanded) |

## 🐛 Troubleshooting

### "Cannot find table#resultTable"
**Cause**: Session expired or not logged in

**Solution**:
```bash
python main.py --project-id 1368 --force-login
```

### "HTTP 500" Error
**Cause**: Project ID may not exist or access denied

**Solution**:
- Verify the project ID is correct
- Check permissions in HRM
- Contact HRM administrator

### "Login failed"
**Cause**: Invalid credentials or CAS server issues

**Solution**:
1. Verify `.env` file has correct credentials
2. Check HRM domain setting
3. Clear session cache: `Remove-Item .session -Force`
4. Try again: `python main.py --project-id 1368`

### "Module not found" Error
**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

## 🔧 Development & Debugging

### View Debug Output
Add `--sleep 1` to see detailed output:
```bash
python main.py --project-id 1368 --sleep 1
```

### Reset Session Cache
```powershell
# PowerShell
Remove-Item .session -Force

# Or delete the file manually
```

### Test Authentication
```bash
python -m src.login
```

### View Configuration
```bash
python config.py
```

## 📝 Important Notes

- **Session TTL**: Sessions are typically valid for 24 hours
- **Rate Limiting**: Default 0.4s delay between requests to avoid throttling
- **Data Format**: Exports are in Excel `.xlsx` format (not `.xls`)
- **Pagination**: Supports unlimited records through automatic pagination
- **Case Sensitivity**: Project IDs are typically numeric

## 🔐 Security

- **Credentials**: Never commit `.env` file to version control
- **Session File**: `.session` is automatically git-ignored
- **PHPSESSID**: Contains authentication token - handle carefully
- **Password Storage**: Use strong passwords and environment variable protection

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review error messages for specific details
3. Ensure all dependencies are installed
4. Contact HRM system administrator for access issues

## 📄 License

This tool is provided as-is for internal use.

## 🎯 Version History

- **v1.0.0** (2024): Initial release
  - CAS authentication with session caching
  - Automatic pagination detection
  - Excel export with comprehensive data
  - Full type hints and docstrings
