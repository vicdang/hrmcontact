"""
Configuration Module for HRM Contact Export Tool

Centralized configuration management for paths, settings, and defaults.
All file paths are managed from this module to ensure consistency across
the application.

Module Attributes:
    PROJECT_ROOT: Absolute path to the project root directory
    OUTPUT_DIR: Directory for storing exported Excel files
    SESSION_FILE: Path to cached CAS session file (.session)
    ENV_FILE: Path to environment variables file (.env)
    DEFAULT_OUTPUT_FILENAME: Default name for Excel export files

Example:
    >>> from config import get_output_path, generate_output_filename, get_session_file_path
    >>> output = get_output_path("contacts.xlsx")
    >>> timestamped_output = get_output_path(generate_output_filename(1368))
    >>> session = get_session_file_path()
"""

from pathlib import Path
from typing import Union
from datetime import datetime

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Project root directory (automatically detected from this file location)
PROJECT_ROOT: Path = Path(__file__).parent.resolve()

# Output directory for exported Excel files
OUTPUT_DIR: Path = PROJECT_ROOT / "output"

# Session file for cached CAS authentication tokens
SESSION_FILE: Path = PROJECT_ROOT / ".session"

# Environment file containing credentials (not in git)
ENV_FILE: Path = PROJECT_ROOT / ".env"

# ============================================================================
# DEFAULTS
# ============================================================================

# Default filename for contact exports
DEFAULT_OUTPUT_FILENAME: str = "contacts.xlsx"

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================================
# FUNCTIONS
# ============================================================================

def generate_output_filename(project_id: int) -> str:
    """
    Generate an output filename with timestamp and project ID.
    
    Format: <timestamp>_<project_id>_contacts.xlsx
    where timestamp is in format: YYYYMMDD_HHMMSS
    
    Args:
        project_id: HRM project ID to include in filename
        
    Returns:
        Filename with timestamp and project ID (without path)
        
    Example:
        >>> filename = generate_output_filename(1368)
        >>> print(filename)
        20260205_143022_1368_contacts.xlsx
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{project_id}_contacts.xlsx"


def get_output_path(filename: str = DEFAULT_OUTPUT_FILENAME) -> str:
    """
    Get the full file path for an output file in the output directory.
    
    This function ensures all exports go to the proper output folder
    rather than the project root.
    
    Args:
        filename: Name of the output file (default: "contacts.xlsx")
        
    Returns:
        Absolute path to the output file as a string
        
    Example:
        >>> path = get_output_path("contacts_2024.xlsx")
        >>> print(path)
        /absolute/path/to/project/output/contacts_2024.xlsx
    """
    return str(OUTPUT_DIR / filename)


def get_session_file_path() -> str:
    """
    Get the file path for cached CAS session data.
    
    The session file stores authentication tokens and cookies to avoid
    repeated login attempts. It is ignored by git (see .gitignore).
    
    Returns:
        Absolute path to the session file as a string
        
    Example:
        >>> session_path = get_session_file_path()
        >>> print(session_path)
        /absolute/path/to/project/.session
    """
    return str(SESSION_FILE)

if __name__ == "__main__":
    # Debug: Print configuration paths
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Session file: {SESSION_FILE}")
    print(f"Default output: {get_output_path()}")
