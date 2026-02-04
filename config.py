"""
Configuration file for HRM Export Tool

Centralized configuration for paths and settings
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()

# Output directory for exported files
OUTPUT_DIR = PROJECT_ROOT / "output"

# Session file path
SESSION_FILE = PROJECT_ROOT / ".session"

# Environment file path
ENV_FILE = PROJECT_ROOT / ".env"

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

# Default output filename
DEFAULT_OUTPUT_FILENAME = "contacts.xlsx"

def get_output_path(filename: str = DEFAULT_OUTPUT_FILENAME) -> str:
    """Get full path for output file"""
    return str(OUTPUT_DIR / filename)

def get_session_file_path() -> str:
    """Get session file path"""
    return str(SESSION_FILE)

if __name__ == "__main__":
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Session file: {SESSION_FILE}")
    print(f"Default output: {get_output_path()}")
