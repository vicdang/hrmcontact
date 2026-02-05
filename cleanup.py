#!/usr/bin/env python3
"""
Cleanup script - Removes old files after restructuring
Run this ONCE after verifying the new structure works
"""
import os
import shutil

# Old files to remove (no longer needed, replaced by src/ version)
OLD_FILES = [
    "login.py",           # Moved to src/login.py
    "hrm_contact_export.py",  # Moved to src/export.py
    "test_login.py",      # Old test files
    "test_export.py",     # Old test files
    "test_session.py",    # Old test files
    "debug_form.py",      # Debug file
    "debug_response.html", # Debug file
]

# Excel files to move to output/
EXCEL_FILES = [
    "*_contacts.xlsx",
]

def cleanup():
    print("[*] Cleaning up old files...")
    
    # Remove old files
    for file in OLD_FILES:
        if os.path.exists(file):
            os.remove(file)
            print(f"[✓] Removed: {file}")
    
    # Move excel files to output/ (optional)
    for file in EXCEL_FILES:
        if os.path.exists(file):
            dest = os.path.join("output", file)
            if not os.path.exists(dest):
                shutil.move(file, dest)
                print(f"[✓] Moved: {file} → output/")
            else:
                os.remove(file)
                print(f"[✓] Removed: {file} (already exists in output/)")
    
    print("\n[✓] Cleanup complete!")
    print("\nProject structure is now clean:")
    print("  src/           - Source code")
    print("  output/        - Excel exports")
    print("  main.py        - Entry point")
    print("  requirements.txt")
    print("  .env          - Your credentials")
    print("  .env.example  - Config template")
    print("  README.md     - Documentation")

if __name__ == "__main__":
    import sys
    print("=" * 50)
    print("HRM Export Tool - Cleanup Script")
    print("=" * 50)
    print("\nThis will remove old files:")
    for f in OLD_FILES:
        print(f"  - {f}")
    print("\nAnd optionally move Excel files to output/")
    
    response = input("\nContinue? (y/n): ").strip().lower()
    if response == 'y':
        cleanup()
    else:
        print("Cancelled.")
