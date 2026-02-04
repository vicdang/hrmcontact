#!/usr/bin/env python3
"""
HRM Contact Export - Main Entry Point

Usage:
    python main.py --project-id 1368
    python main.py --project-id 1368 --out "my_contacts.xlsx"
    python main.py --project-id 1368 --force-login
    python main.py --project-id 1368 --phpsessid "ST-xxx"
"""
import sys
from src.export import main

if __name__ == "__main__":
    main()
