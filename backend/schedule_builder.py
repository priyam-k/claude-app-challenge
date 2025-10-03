"""
Schedule Builder Module
Handles the 2-step process:
1. Find relevant courses based on query
2. Build actual schedules with conflict detection
"""

from typing import List, Dict, Tuple
import anthropic
import os
from scraper import fetch_course_sections, fetch_department_courses, fetch_gened_courses, GENED_CODES
import json
import re

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def time_to_minutes(time_str: str) -> int:
    """Convert time string like '9:30am' to minutes since midnight"""
    if not time_str:
        return 0

    time_str = time_str.lower().strip()
    is_pm = 'pm' in time_str
    time_str = time_str.replace('am', '').replace('pm', '').strip()

    parts = time_str.split(':')
    if len(parts) != 2:
        return 0

    try:
        hour = int(parts[0])
        minute = int(parts[1])

        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0

        return hour * 60 + minute
    except:
        return 0


def sections_conflict(section1: Dict, section2: Dict) -> bool:
    """Check if two sections have time conflicts"""
    days1 = section1.get('days', '')
    days2 = section2.get('days', '')

    if not days1 or not days2:
        return False

    # Check if they share any days
    days1_set = set(days1)
    days2_set = set(days2)

    if not days1_set.intersection(days2_set):
        return False  # No shared days

    # Parse times
    time1 = section1.get('time', '')
    time2 = section2.get('time', '')

    if not time1 or not time2 or '-' not in time1 or '-' not in time2:
        return False

    start1, end1 = time1.split('-')
    start2, end2 = time2.split('-')

    start1_min = time_to_minutes(start1)
    end1_min = time_to_minutes(end1)
    start2_min = time_to_minutes(start2)
    end2_min = time_to_minutes(end2)

    # Check for overlap
    return not (end1_min <= start2_min or end2_min <= start1_min)


async def find_relevant_courses(query: str, term_id: str) -> Tuple[List[Dict], Dict, List[str]]:
    """Step 1: Find 7-10 relevant courses based on query"""

    # Use AI to parse query with better understanding
    parse_prompt = f"""Parse this schedule building query. Return ONLY valid JSON.

Query: "{query}"

Extract:
- departments: list of department codes (e.g. ["CMSC", "MATH"])
- level: course level (1-4) or null
- geneds: gen-ed codes
- keywords: topic keywords
- specific_courses: list of course codes TO INCLUDE in the new schedule (e.g. ["CMSC320", "MATH310"])
- excluded_courses: list of courses already taken/completed (e.g. if user says "already took CMSC216", add "CMSC216" here)
- preferences: dict with "prefer_mornings", "minimize_gaps", "best_profs", "spread_out"

CRITICAL RULES:
1. If user says "already took X" or "completed X" or "finished X", add X to excluded_courses, NOT specific_courses
2. If user lists courses without "already took", they want those IN the new schedule (add to specific_courses)
3. Parse all course codes in DEPT### format (e.g. CMSC216, MATH246)

Return JSON:
{{
  "departments": [],
  "level": null,
  "geneds": [],
  "keywords": [],
  "specific_courses": [],
  "excluded_courses": [],
  "preferences": {{}}
}}"""

    parse_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": parse_prompt}]
    )

    filters = {"departments": [], "level": None, "geneds": [], "keywords": [], "specific_courses": [], "excluded_courses": [], "preferences": {}}

    try:
        parse_text = parse_response.content[0].text
        start = parse_text.find('{')
        end = parse_text.rfind('}') + 1
        if start >= 0 and end > start:
            filters = json.loads(parse_text[start:end])
            print(f"Parsed filters: {filters}")
    except Exception as e:
        print(f"Parse error: {e}")

    # Fetch courses
    all_courses = []
    specific_courses = filters.get('specific_courses', [])
    excluded_courses = filters.get('excluded_courses', [])

    # Add specific courses first
    for course_code in specific_courses:
        courses = await fetch_department_courses(course_code[:4].upper(), term_id)
        matching = [c for c in courses if c['code'] == course_code.upper()]
        all_courses.extend(matching)

    # Then add from departments
    for dept in filters.get('departments', [])[:3]:
        courses = await fetch_department_courses(dept.upper(), term_id)
        # Exclude already added specific courses and excluded courses
        courses = [c for c in courses if c['code'] not in [sc.upper() for sc in specific_courses]
                   and c['code'] not in [ec.upper() for ec in excluded_courses]]
        all_courses.extend(courses)

    for gened in filters.get('geneds', [])[:2]:
        if gened.upper() in GENED_CODES:
            courses = await fetch_gened_courses(gened.upper(), term_id)
            # Exclude excluded courses
            courses = [c for c in courses if c['code'] not in [ec.upper() for ec in excluded_courses]]
            all_courses.extend(courses)

    # Apply filters
    if filters.get('level'):
        level_str = str(filters['level'])
        # Keep specific courses even if wrong level
        filtered = [c for c in all_courses if c['code'] in [sc.upper() for sc in specific_courses] or (len(c['code']) >= 5 and c['code'][4] == level_str)]
        if filtered:
            all_courses = filtered

    keywords = filters.get('keywords', [])
    if keywords:
        keyword_courses = []
        for c in all_courses:
            course_text = (c['title'] + ' ' + c.get('description', '')).upper()
            if any(kw.upper() in course_text for kw in keywords):
                keyword_courses.append(c)
        # Keep specific courses even if they don't match keywords
        for sc in specific_courses:
            matching = [c for c in all_courses if c['code'] == sc.upper()]
            for m in matching:
                if m not in keyword_courses:
                    keyword_courses.append(m)
        if keyword_courses:
            all_courses = keyword_courses

    # Smart filtering: aim for ~10 courses with diversity
    final_courses = []
    dept_counts = {}

    # First, add all specific courses
    for c in all_courses:
        if c['code'] in [sc.upper() for sc in specific_courses]:
            final_courses.append(c)
            dept = c['code'][:4]
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # Then add others with department diversity
    # First pass: add up to 2 from each department
    for c in all_courses:
        if c in final_courses:
            continue
        if len(final_courses) >= 10:
            break
        dept = c['code'][:4]
        if dept_counts.get(dept, 0) < 2:
            final_courses.append(c)
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # Second pass: if we don't have enough, add more (up to 3 per dept)
    if len(final_courses) < 8:
        for c in all_courses:
            if c in final_courses:
                continue
            if len(final_courses) >= 10:
                break
            dept = c['code'][:4]
            if dept_counts.get(dept, 0) < 3:
                final_courses.append(c)
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

    print(f"Selected {len(final_courses)} courses for schedule building")
    return final_courses, filters.get('preferences', {}), specific_courses


async def build_schedules_from_courses(courses: List[Dict], preferences: Dict, term_id: str, specific_courses: List[str]) -> List[Dict]:
    """Step 2: Build actual schedules from the course list"""
    from planetterp import enrich_section_with_ratings

    # Calculate target credits: if user lists specific courses, use their total; otherwise target 15
    if specific_courses:
        # Find the total credits from specific courses
        specific_credits = sum(c['credits'] for c in courses if c['code'] in [sc.upper() for sc in specific_courses])
        # Use that as target, but allow some flexibility (e.g., if 19, use 19)
        max_credits = max(specific_credits, 15)
    else:
        # Default target: 15 credits
        max_credits = preferences.get('max_credits', 15)

    # Fetch sections for all courses and enrich with ratings
    courses_with_sections = []

    for course in courses:
        sections = await fetch_course_sections(course['code'], term_id)

        # Enrich sections with professor ratings and course GPA
        enriched_sections = []
        for section in sections:
            enriched = await enrich_section_with_ratings(section, course['code'])
            enriched_sections.append(enriched)

        if enriched_sections:
            courses_with_sections.append({
                **course,
                'sections': enriched_sections,
                'is_specific': course['code'] in [sc.upper() for sc in specific_courses]
            })

    # Now build 2-3 different schedule options
    schedules = []

    # Option 1: Best professors (if requested)
    best_profs = preferences.get('best_profs', False)
    schedule1 = build_one_schedule(courses_with_sections, best_profs=best_profs, max_credits=max_credits, specific_courses=specific_courses)
    if schedule1:
        schedules.append(schedule1)

    # Option 2: Morning classes (if requested or if first didn't work)
    if preferences.get('prefer_mornings', False) or not schedule1:
        schedule2 = build_one_schedule(courses_with_sections, prefer_morning=True, max_credits=max_credits, specific_courses=specific_courses)
        if schedule2 and (not schedule1 or schedule2 != schedule1):
            schedules.append(schedule2)

    # Option 3: Balanced/spread out (if less than 2 schedules so far)
    if len(schedules) < 2:
        schedule3 = build_one_schedule(courses_with_sections, spread_out=True, max_credits=max_credits, specific_courses=specific_courses)
        if schedule3 and schedule3 not in schedules:
            schedules.append(schedule3)

    return schedules[:3]  # Return max 3 schedules


def build_one_schedule(courses_with_sections: List[Dict], best_profs=False, prefer_morning=False, spread_out=False, max_credits=15, specific_courses=[]) -> Dict:
    """Build a single schedule by picking non-conflicting sections"""

    selected_sections = []
    total_credits = 0
    dept_counts = {}

    # Sort courses: specific courses first, then by level consistency
    sorted_courses = sorted(courses_with_sections, key=lambda c: (
        0 if c.get('is_specific', False) else 1,  # Specific courses first
        -int(c['code'][4]) if len(c['code']) >= 5 and c['code'][4].isdigit() else 0  # Then by level
    ))

    for course in sorted_courses:
        # Check credit limit - be flexible for specific courses
        if total_credits + course['credits'] > max_credits + 1:
            # If it's a specific course, allow going over a bit
            if not course.get('is_specific', False):
                continue
            # Even for specific courses, don't go way over
            if total_credits + course['credits'] > max_credits + 3:
                continue

        sections = course.get('sections', [])
        if not sections:
            continue

        # Sort sections based on preferences
        if best_profs:
            # Sort by professor rating (highest first), then by open seats
            sections = sorted(sections, key=lambda s: (
                -(s.get('prof_rating') or 0),  # Higher rating first
                -(s.get('open_seats', 0))  # More seats first
            ))
        elif prefer_morning:
            # Prefer sections starting before noon
            sections = sorted(sections, key=lambda s: time_to_minutes(s.get('time', '').split('-')[0] if s.get('time') and '-' in s.get('time', '') else '9:00am'))
        else:
            # Default: sort by open seats
            sections = sorted(sections, key=lambda s: -(s.get('open_seats', 0)))

        # Pick first non-conflicting section
        for section in sections:
            if section.get('open_seats', 0) <= 0:
                continue

            conflicts = any(sections_conflict(section, sel['section']) for sel in selected_sections)

            if not conflicts:
                dept = course['code'][:4]

                # Soft limit on same department (unless specific course)
                if dept_counts.get(dept, 0) >= 3 and not course.get('is_specific', False):
                    break  # Try next course instead

                # Level consistency check: avoid mixing 1xx/2xx with 4xx (unless specific)
                if not course.get('is_specific', False) and selected_sections:
                    course_level = int(course['code'][4]) if len(course['code']) >= 5 and course['code'][4].isdigit() else 0
                    existing_levels = [int(s['course_code'][4]) for s in selected_sections if len(s['course_code']) >= 5 and s['course_code'][4].isdigit()]

                    if existing_levels:
                        avg_level = sum(existing_levels) / len(existing_levels)
                        # Skip if level difference is too large (e.g., 1xx with 4xx)
                        if abs(course_level - avg_level) > 2:
                            break

                selected_sections.append({
                    'course_code': course['code'],
                    'course_title': course['title'],
                    'credits': course['credits'],
                    'section': section,
                    'course_gpa': section.get('course_gpa')
                })
                total_credits += course['credits']
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                break

    # Require at least 4 courses for a valid schedule (typically 12+ credits)
    if len(selected_sections) < 4:
        return None

    return {
        'courses': selected_sections,
        'total_credits': total_credits
    }
