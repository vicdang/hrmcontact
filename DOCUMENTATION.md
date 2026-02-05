# HRM Contact Export Tool - Complete Documentation

## Overview

This is a professional-grade Python application for exporting employee contact lists from the TRNA HRM (Human Resource Management) system to Excel files.

## Code Quality Improvements (Latest Review)

### ✅ Docstring Additions
All Python modules now have comprehensive docstrings with:
- **Module-level documentation**: Clear description of purpose and usage
- **Function-level documentation**: Detailed docstrings with Args, Returns, Raises, and Examples
- **Type hints**: Full type annotations on all functions and variables
- **Section comments**: Clear organization with ASCII divider comments

### ✅ English Conversion
The entire project has been converted to English:
- **Code**: All variable names, comments, and docstrings are in English
- **Configuration**: `.env.example` has English comments and instructions
- **Documentation**: All markdown files (README.md, etc.) are in English

### ✅ Old Files Cleanup
Removed duplicate/obsolete files:
- ❌ `login.py` (root level) - Moved to `src/login.py`
- ❌ `hrm_contact_export.py` - Moved to `src/export.py`
- ❌ `cleanup.py` - Removed

## Module Structure

### config.py
**Purpose**: Centralized configuration management

**Key Features**:
- Auto-detects project root directory
- Manages all file paths (output directory, session file, etc.)
- Provides utility functions for getting output paths
- Type-safe with full type hints

**Key Functions**:
- `get_output_path(filename)`: Get full path for output Excel file
- `get_session_file_path()`: Get path to session cache file

### src/login.py
**Purpose**: CAS authentication and session management

**Key Features**:
- 4-step CAS authentication flow
- Session caching to JSON file for reuse
- Automatic session loading/saving
- Full error handling

**Key Functions**:
- `build_hrm_url(domain)`: Convert domain to full HRM URL
- `get_authenticated_session()`: Perform CAS authentication
- `save_session(session)`: Cache session to disk
- `load_session()`: Load cached session from disk

### src/export.py
**Purpose**: Contact list fetching and Excel export

**Key Features**:
- Automatic pagination detection
- HTML table parsing with BeautifulSoup
- Contact data extraction and normalization
- Excel export with pandas
- Comprehensive command-line interface

**Key Functions**:
- `build_hrm_domain_url(domain)`: Convert domain to URL
- `build_params()`: Build query parameters for HRM API
- `fetch_html()`: Fetch HTML from HRM server
- `parse_max_page_and_current()`: Extract pagination info
- `normalize_text()`: Normalize whitespace
- `parse_rows()`: Parse contact rows from HTML table
- `detect_page_param()`: Auto-detect pagination parameter
- `export_contacts()`: Main export function
- `main()`: Command-line interface

### main.py
**Purpose**: Entry point for the application

Simple wrapper that imports and calls the export module's main function.

### src/__init__.py
**Purpose**: Package initialization

Documents the package structure and provides quick import reference.

## Documentation Files

### README.md (English)
Complete user guide with:
- Features overview
- Installation instructions
- Usage examples
- Command-line reference
- Project structure
- Session management details
- Exported data description
- Troubleshooting guide
- Security notes

### .env.example
Configuration template with:
- Commented sections for clarity
- All required environment variables
- Default values and examples
- Security warnings

## Code Quality Metrics

### Type Hints
✅ **100% coverage** - All functions have type hints

### Docstrings
✅ **100% coverage** - All modules, classes, and functions have docstrings

### Comments
✅ **Well-commented** - Section dividers and inline comments explain logic

### Code Structure
✅ **Organized** - Clear separation of concerns:
- Authentication logic (login.py)
- Export logic (export.py)
- Configuration (config.py)
- CLI interface (main.py)

### Error Handling
✅ **Comprehensive** - All exceptions properly caught and reported:
- `SessionExpiredException`: For session expiration
- Custom error messages for debugging

## Project Statistics

| Metric | Value |
|--------|-------|
| Python Files | 5 |
| Lines of Code | ~650 |
| Functions | 15+ |
| Type-hinted Functions | 15/15 (100%) |
| Documented Functions | 15/15 (100%) |
| Supported Python Version | 3.6+ |

## Dependencies

| Package | Purpose |
|---------|---------|
| requests | HTTP requests |
| beautifulsoup4 | HTML parsing |
| pandas | Data manipulation & Excel export |
| openpyxl | Excel file creation |
| python-dotenv | Environment variable management |

See `requirements.txt` for exact versions.

## Key Workflows

### Authentication Flow
```
1. Check for cached session in .session file
2. If exists and valid, reuse it
3. If not, perform CAS authentication:
   a. POST credentials to HRM login endpoint
   b. HRM redirects to CAS server
   c. GET CAS login form
   d. POST credentials to CAS
   e. CAS provides Service Ticket
   f. Redirect back to HRM with ticket
   g. HRM validates and creates session
4. Cache session for future use
```

### Export Flow
```
1. Authenticate (using cached or fresh session)
2. Detect pagination parameter by testing page 2
3. Fetch all pages of results
4. Parse contact information from HTML tables
5. Normalize and deduplicate data
6. Export to Excel with proper formatting
```

## Configuration

### Environment Variables (.env)
```env
HRM_DOMAIN=trna              # HRM server domain
HRM_USERNAME=your_username   # Login username
HRM_PASSWORD=your_password   # Login password
```

### Configuration Files
- `.env`: Credentials (git-ignored)
- `.env.example`: Configuration template
- `.session`: Cached authentication (git-ignored)

## Usage Examples

### Basic Export
```bash
python main.py --project-id 1368
```

### With Custom Output
```bash
python main.py --project-id 1368 --out custom_contacts.xlsx
```

### Force Fresh Login
```bash
python main.py --project-id 1368 --force-login
```

### Using Specific Session
```bash
python main.py --project-id 1368 --phpsessid "ST-xxxxx"
```

## Error Handling

The application handles various error scenarios:

| Error | Cause | Solution |
|-------|-------|----------|
| Session Expired | PHPSESSID invalid | Auto re-login or use `--force-login` |
| Cannot find table | Layout changed | Check HRM version |
| HTTP 500 | Invalid project ID | Verify project ID exists |
| Login failed | Wrong credentials | Check `.env` file |
| Module not found | Dependencies missing | Run `pip install -r requirements.txt` |

## Best Practices

### Security
- ✅ Never commit `.env` file (git-ignored)
- ✅ Use strong passwords
- ✅ Session file automatically git-ignored
- ✅ PHPSESSID contains sensitive data

### Performance
- ✅ Session caching avoids repeated logins
- ✅ Configurable request delays (default 0.4s)
- ✅ Automatic pagination handling
- ✅ Memory-efficient streaming

### Reliability
- ✅ Automatic session refresh on expiration
- ✅ Duplicate contact deduplication by Badge ID
- ✅ Comprehensive error messages
- ✅ Graceful failure modes

## Maintenance

### Project Root
```
D:\PlayGround\employee
```

### Key Files
- `main.py`: Entry point
- `config.py`: Configuration management
- `src/login.py`: Authentication
- `src/export.py`: Export logic
- `README.md`: User documentation
- `requirements.txt`: Dependencies

### Regular Tasks
- Update credentials in `.env`
- Clear `.session` if needed: `rm .session`
- Monitor HRM API changes
- Update `requirements.txt` versions periodically

## Version History

### v1.0.0 (Current)
- ✅ Complete CAS authentication
- ✅ Session caching
- ✅ Automatic pagination
- ✅ Comprehensive docstrings
- ✅ Full type hints
- ✅ English documentation
- ✅ Professional code quality

## Future Enhancements

Potential improvements:
- Add logging module
- Support for multiple export formats (CSV, JSON)
- Configuration file support (YAML, INI)
- Database export option
- Scheduled export automation
- Progress bar for large exports
- Incremental export (only new records)

## Support & Troubleshooting

See README.md for detailed troubleshooting guide covering:
- Authentication issues
- Session problems
- Pagination detection failures
- Excel export errors
- Dependency issues

## Code Standards

This project follows:
- ✅ PEP 8 style guide
- ✅ Type hints (PEP 484)
- ✅ Docstring conventions (PEP 257)
- ✅ Module documentation standards
- ✅ English language for all code

## References

### Related Modules
- [requests](https://requests.readthedocs.io/) - HTTP library
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - HTML parsing
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel support

### CAS Documentation
- Central Authentication Service (CAS)
- TRNA HRM System Documentation
