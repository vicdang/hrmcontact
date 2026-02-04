# Migration Guide - Old Structure → New Structure

## ✅ What Has Changed

### Before (Old Structure)
```
employee/
├── login.py                    ❌ (root level)
├── hrm_contact_export.py       ❌ (root level)
├── requirements.txt
├── .env
├── README.md
└── ... test files, debug files
```

### After (New Structure)
```
employee/
├── src/                        ✅ (organized)
│   ├── __init__.py
│   ├── login.py              (moved here)
│   └── export.py             (renamed from hrm_contact_export.py)
├── output/                     ✅ (dedicated folder for exports)
│   ├── .gitkeep
│   └── contacts.xlsx
├── main.py                     ✅ (entry point)
├── cleanup.py                  ✅ (cleanup helper)
├── requirements.txt
├── .env
├── .env.example
├── README.md                   (updated)
├── STRUCTURE.md                ✅ (new - detailed docs)
└── .gitignore                  (improved)
```

## 🔄 What Stayed the Same

- ✅ All functionality (CAS auth, session caching, export)
- ✅ All CLI options (`--project-id`, `--force-login`, etc.)
- ✅ Output format (Excel `.xlsx`)
- ✅ `.env` credentials
- ✅ Session file (`.session`)

## 📝 Usage Changes

### Old Way
```bash
python hrm_contact_export.py --project-id 1368
```

### New Way
```bash
python main.py --project-id 1368
```

**Or (direct module call):**
```bash
python -m src.export --project-id 1368
```

## 🚀 Migration Steps

### Step 1: Verify New Structure Works
Already tested ✅
- `python main.py --help` works
- `python main.py --project-id 1368` works
- CAS authentication works
- Session caching works

### Step 2: Update Your Commands
Replace all:
```bash
# Old
python hrm_contact_export.py ...

# New
python main.py ...
```

### Step 3: Cleanup Old Files (Optional)
Run cleanup script to remove old files:
```bash
python cleanup.py
```

This will remove:
- `login.py` (old, now in `src/login.py`)
- `hrm_contact_export.py` (old, now in `src/export.py`)
- Old test files
- Debug files

⚠️ **Note**: This is optional. Old files won't interfere.

### Step 4: Update Documentation/Scripts
If you have any bash scripts or docs referencing old commands, update them.

## 📚 New Documentation

- **README.md** - Main usage guide (updated)
- **STRUCTURE.md** - Detailed project structure
- **cleanup.py** - Helper to remove old files

## ✨ Improvements

### Code Organization
- ✅ Proper package structure (`src/`)
- ✅ Clean separation of concerns (auth vs export)
- ✅ Professional Python project layout

### Output Management
- ✅ Dedicated `output/` folder for exports
- ✅ All Excel files go to one place
- ✅ Easier to clean up

### Documentation
- ✅ Comprehensive README with examples
- ✅ Detailed STRUCTURE.md for developers
- ✅ Migration guide (this file)
- ✅ `.env.example` template

### Configuration
- ✅ Better `.gitignore` (organized by category)
- ✅ Clear distinction between tracked/ignored files

## 🎯 No Breaking Changes

All your existing commands still work:
```bash
# These all still work with new structure
python main.py --project-id 1368
python main.py --project-id 1368 --out output/custom.xlsx
python main.py --project-id 1368 --force-login
python main.py --project-id 1368 --phpsessid "ST-xxx"
python main.py --project-id 1368 --sleep 1
```

## 🐛 Troubleshooting Migration

### "ModuleNotFoundError: No module named 'src'"
- Make sure you're running from project root: `cd employee`
- Make sure `src/__init__.py` exists

### "No such file or directory"
- Old scripts still pointing to `hrm_contact_export.py`
- Update to use `python main.py` instead

### ".session" file not found
- This is normal - it will be created on first run
- Run: `python main.py --project-id 1368 --force-login`

## 📞 Quick Reference

| Task | Command |
|------|---------|
| First export | `python main.py --project-id 1368` |
| Next export (cached) | `python main.py --project-id 1368` |
| Force new login | `python main.py --project-id 1368 --force-login` |
| Custom output | `python main.py --project-id 1368 --out output/my_contacts.xlsx` |
| Get help | `python main.py --help` |
| Cleanup old files | `python cleanup.py` |
| Check structure | See `STRUCTURE.md` |
