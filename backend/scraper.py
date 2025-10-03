"""
UMD Schedule of Classes Scraper
Fetches and caches course data from app.testudo.umd.edu
"""

import httpx
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import re

# Cache directory
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Cache expiry (1 day)
CACHE_EXPIRY_HOURS = 24

# Term mapping
TERM_CODES = {
    "spring": "01",
    "summer": "05",
    "fall": "08",
    "winter": "12"
}

# Gen-ed codes
GENED_CODES = {
    "FSAW": "Academic Writing",
    "FSAR": "Analytic Reasoning",
    "FSMA": "Math",
    "FSOC": "Oral Communications",
    "FSPW": "Professional Writing",
    "DSHS": "History and Social Sciences",
    "DSHU": "Humanities",
    "DSNS": "Natural Sciences",
    "DSNL": "Natural Science Lab",
    "DSSP": "Scholarship in Practice",
    "DVCC": "Cultural Competency",
    "DVUP": "Understanding Plural Societies",
    "SCIS": "Signature Courses - Big Question"
}


def get_current_term() -> str:
    """Get current term ID (e.g., 202501 for Spring 2025)"""
    now = datetime.now()
    year = now.year
    month = now.month

    # Determine term based on month
    if 1 <= month <= 5:
        term = "01"  # Spring
    elif 6 <= month <= 7:
        term = "05"  # Summer
    elif 8 <= month <= 11:
        term = "08"  # Fall
    else:  # December
        term = "12"  # Winter
        year += 1  # Winter is next year

    return f"{year}{term}"


def get_cache_path(cache_key: str) -> Path:
    """Get cache file path for a given key"""
    safe_key = re.sub(r'[^\w\-]', '_', cache_key)
    return CACHE_DIR / f"{safe_key}.json"


def is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is not expired"""
    if not cache_path.exists():
        return False

    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.now() - mtime
    return age < timedelta(hours=CACHE_EXPIRY_HOURS)


def save_to_cache(cache_key: str, data: dict):
    """Save data to cache"""
    cache_path = get_cache_path(cache_key)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({
            'cached_at': datetime.now().isoformat(),
            'data': data
        }, f, indent=2)


def load_from_cache(cache_key: str) -> Optional[dict]:
    """Load data from cache if valid"""
    cache_path = get_cache_path(cache_key)

    if is_cache_valid(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached = json.load(f)
            return cached['data']

    return None


def parse_course_html(html_content: str, dept: str = None) -> List[Dict]:
    """Parse course data from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    courses = []

    # Find all course containers
    course_divs = soup.find_all('div', class_='course')

    for course_div in course_divs:
        try:
            # Extract course ID
            course_id_elem = course_div.find('div', class_='course-id')
            if not course_id_elem:
                continue

            course_code = course_id_elem.get_text(strip=True)

            # Extract title
            title_elem = course_div.find('span', class_='course-title')
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Extract credits
            credits_elem = course_div.find('span', class_='course-min-credits')
            credits = 0
            if credits_elem:
                try:
                    credits = int(credits_elem.get_text(strip=True))
                except:
                    credits = 3  # Default

            # Extract gen-ed codes from subcategory links
            geneds = []
            subcategory_spans = course_div.find_all('span', class_='course-subcategory')
            for span in subcategory_spans:
                link = span.find('a')
                if link:
                    code_text = link.get_text(strip=True)
                    if code_text in GENED_CODES:
                        geneds.append(code_text)

            # Extract description from approved-course-text divs
            description = ""
            desc_divs = course_div.find_all('div', class_='approved-course-text')
            if desc_divs:
                # Get all text with proper spacing between elements
                desc_texts = []
                for d in desc_divs:
                    text = d.get_text(separator=' ', strip=True)
                    if text:
                        desc_texts.append(text)
                description = " ".join(desc_texts)

            course_data = {
                'code': course_code,
                'title': title,
                'credits': credits,
                'description': description[:500] if len(description) > 500 else description,  # Truncate long descriptions
                'geneds': geneds,
                'department': dept or course_code[:4] if len(course_code) >= 4 else ""
            }

            courses.append(course_data)

        except Exception as e:
            print(f"Error parsing course: {e}")
            continue

    return courses


async def fetch_department_courses(dept: str, term_id: str = None) -> List[Dict]:
    """Fetch all courses for a department"""
    if term_id is None:
        term_id = get_current_term()

    cache_key = f"dept_{dept}_{term_id}"

    # Check cache first
    cached_data = load_from_cache(cache_key)
    if cached_data:
        print(f"Using cached data for {dept} (term {term_id})")
        return cached_data

    # Fetch from SOC
    url = f"https://app.testudo.umd.edu/soc/{term_id}/{dept.upper()}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            courses = parse_course_html(response.text, dept.upper())

            # Save to cache
            save_to_cache(cache_key, courses)
            print(f"Fetched and cached {len(courses)} courses for {dept}")

            return courses

        except Exception as e:
            print(f"Error fetching {dept}: {e}")
            return []


async def fetch_gened_courses(gened_code: str, term_id: str = None) -> List[Dict]:
    """Fetch all courses for a gen-ed requirement"""
    if term_id is None:
        term_id = get_current_term()

    if gened_code.upper() not in GENED_CODES:
        return []

    cache_key = f"gened_{gened_code}_{term_id}"

    # Check cache first
    cached_data = load_from_cache(cache_key)
    if cached_data:
        print(f"Using cached data for gen-ed {gened_code}")
        return cached_data

    # Fetch from SOC gen-ed endpoint
    url = f"https://app.testudo.umd.edu/soc/gen-ed/{term_id}/{gened_code.upper()}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            courses = parse_course_html(response.text)

            # Save to cache
            save_to_cache(cache_key, courses)
            print(f"Fetched and cached {len(courses)} gen-ed courses for {gened_code}")

            return courses

        except Exception as e:
            print(f"Error fetching gen-ed {gened_code}: {e}")
            return []


async def fetch_course_sections(course_code: str, term_id: str = None) -> List[Dict]:
    """Fetch detailed section information for a specific course"""
    if term_id is None:
        term_id = get_current_term()

    # Extract department from course code (e.g., CMSC216 -> CMSC)
    dept = ''.join([c for c in course_code if c.isalpha()])

    cache_key = f"sections_{course_code}_{term_id}"

    # Check cache first
    cached_data = load_from_cache(cache_key)
    if cached_data:
        return cached_data

    url = f"https://app.testudo.umd.edu/soc/{term_id}/{dept}/{course_code}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            sections = []

            # Find all section divs
            section_divs = soup.find_all('div', class_='section')

            for section_div in section_divs:
                try:
                    # Section ID
                    section_id_elem = section_div.find('span', class_='section-id')
                    section_id = section_id_elem.get_text(strip=True) if section_id_elem else ""

                    # Instructor
                    instructor_elem = section_div.find('span', class_='section-instructor')
                    instructor = instructor_elem.get_text(strip=True) if instructor_elem else "TBA"

                    # Seats
                    open_seats_elem = section_div.find('span', class_='open-seats-count')
                    open_seats = int(open_seats_elem.get_text(strip=True)) if open_seats_elem else 0

                    total_seats_elem = section_div.find('span', class_='total-seats-count')
                    total_seats = int(total_seats_elem.get_text(strip=True)) if total_seats_elem else 0

                    # Days and times
                    days_elem = section_div.find('span', class_='section-days')
                    days = days_elem.get_text(strip=True) if days_elem else ""

                    start_time_elem = section_div.find('span', class_='class-start-time')
                    end_time_elem = section_div.find('span', class_='class-end-time')

                    start_time = start_time_elem.get_text(strip=True) if start_time_elem else ""
                    end_time = end_time_elem.get_text(strip=True) if end_time_elem else ""

                    time_str = f"{start_time}-{end_time}" if start_time and end_time else ""

                    # Building/room
                    building_elem = section_div.find('span', class_='building-code')
                    room_elem = section_div.find('span', class_='class-room')

                    building = building_elem.get_text(strip=True) if building_elem else ""
                    room = room_elem.get_text(strip=True) if room_elem else ""
                    location = f"{building} {room}".strip() if building or room else ""

                    sections.append({
                        'section_id': section_id,
                        'instructor': instructor,
                        'days': days,
                        'time': time_str,
                        'location': location,
                        'open_seats': open_seats,
                        'total_seats': total_seats
                    })

                except Exception as e:
                    print(f"Error parsing section: {e}")
                    continue

            # Save to cache
            save_to_cache(cache_key, sections)
            print(f"Fetched {len(sections)} sections for {course_code}")

            return sections

        except Exception as e:
            print(f"Error fetching sections for {course_code}: {e}")
            return []


async def search_courses(query: str, term_id: str = None) -> List[Dict]:
    """
    Smart search for courses based on query.
    Determines if it's a department search, gen-ed search, or specific course.
    """
    query = query.upper().strip()

    # Check if it's a gen-ed code
    for code in GENED_CODES.keys():
        if code in query or GENED_CODES[code].upper() in query:
            return await fetch_gened_courses(code, term_id)

    # Check if it's a department (2-4 letters)
    dept_match = re.match(r'^([A-Z]{2,4})', query)
    if dept_match:
        dept = dept_match.group(1)
        return await fetch_department_courses(dept, term_id)

    return []


# Test function
if __name__ == "__main__":
    import asyncio

    async def test():
        # Test department fetch
        print("Testing CMSC courses...")
        courses = await fetch_department_courses("CMSC")
        print(f"Found {len(courses)} CMSC courses")
        if courses:
            print(f"Sample: {courses[0]}")

        # Test gen-ed fetch
        print("\nTesting FSOC gen-ed...")
        gened_courses = await fetch_gened_courses("FSOC")
        print(f"Found {len(gened_courses)} FSOC courses")

    asyncio.run(test())
