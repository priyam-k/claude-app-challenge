# What's New - Real UMD Course Data Integration

## Major Updates

### ✅ Live UMD Schedule of Classes Scraper
- **Smart caching system**: Fetches data from app.testudo.umd.edu on-demand
- **Builds cache as needed**: Only pulls departments/gen-eds when requested
- **Cache expires after 24 hours**: Automatically refreshes stale data
- **Supports all departments**: CMSC, MATH, PHYS, CHEM, HIST, ENGL, PSYC, etc.
- **Gen-ed filtering**: Can fetch by FSOC, FSMA, DSHU, DVUP, and all other gen-ed codes

### ✅ Enhanced Schedule Builder
- Now uses **real UMD course data** from Spring 2025 semester
- Automatically detects:
  - Department mentions (e.g., "CMSC", "MATH")
  - Gen-ed requirements (e.g., "oral communication" → FSOC)
  - Specific course types
- Returns actual course codes, titles, credits, and descriptions

### ✅ Improved Course Advisor
- Pulls from **live UMD course catalog**
- Understands CS/CMSC requirements
- Recommends real courses based on actual descriptions and gen-ed codes
- Provides context on why each course matches

### ✅ Better Campus Compass
- Enhanced dining hall data with hours and locations
- Shuttle route details with frequencies
- Building location context (e.g., "McKeldin is center campus")
- More specific answers with nearby landmarks

## How the Scraper Works

### On-Demand Fetching
When you search for "I need a COMM gen-ed":
1. Backend detects "COMM" → fetches FSOC gen-ed courses
2. Caches results in `backend/cache/gened_FSOC_202501.json`
3. Next time: instant response from cache (valid for 24 hours)

### Department Search
When you search for "CMSC course":
1. Fetches all CMSC courses from Testudo
2. Caches in `backend/cache/dept_CMSC_202501.json`
3. Returns 93 real CMSC courses with descriptions

### Cache Location
All cached data is stored in `backend/cache/` as JSON files.

## Install New Dependency

If you haven't already:
```bash
cd backend
pip install beautifulsoup4==4.12.3
```

## Restart the Backend

To apply changes:
```bash
# Stop the current backend (Ctrl+C)
# Then restart:
uvicorn main:app --reload
```

## Test It Out

Try these queries in the app:

**Schedule Builder:**
- "I need a COMM gen-ed on Tuesdays"
- "Find me a CMSC course"
- "I need oral communication class"

**Advisor:**
- "I need one more CS core course"
- "What gen-eds should I take for humanities?"

**Compass:**
- "Where can I get vegetarian food near McKeldin?"
- "What shuttle goes to Iribe at 2:30?"

You should now see **real UMD courses** with actual descriptions instead of the same 3 placeholder courses!
