#!/usr/bin/env python3
"""
HRM Contact Export - Main Entry Point

This script serves as the entry point for the HRM Contact Export tool.
It imports and delegates to the export module's main() function.

Usage:
    python main.py --project-id 1368
    python main.py --project-id 1368 --out custom.xlsx
    python main.py --project-id 1368 --force-login

See src/export.py for detailed documentation on available options.
"""

import sys
from src.export import main

if __name__ == "__main__":
    main()
