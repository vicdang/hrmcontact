"""
HRM Contact Export Package

Automated tool for exporting employee contact lists from the TRNA HRM system.

This package provides functionality to:
- Authenticate against the HRM system using CAS (Central Authentication Service)
- Fetch and parse employee contact information
- Export contact lists to Excel files with support for pagination and filtering

Modules:
    login: CAS authentication and session management
    export: Contact list fetching and Excel export

Example:
    >>> from src.export import export_contacts
    >>> export_contacts(project_id=1368)
    [OK] Project 1368: exported 195 rows -> ./output/contacts.xlsx
"""

__version__ = "1.0.0"
__author__ = "HRM Export Tool"
__all__ = ["login", "export"]
