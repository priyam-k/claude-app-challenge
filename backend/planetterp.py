"""
PlanetTerp API Integration
Fetches professor ratings and course GPAs
"""

import httpx
from typing import Dict, Optional

BASE_URL = "https://planetterp.com/api/v1"


async def get_professor_rating(prof_name: str) -> Optional[Dict]:
    """Get professor rating from PlanetTerp"""
    if not prof_name or prof_name.upper() in ['TBA', 'STAFF', '']:
        return None

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{BASE_URL}/professor",
                params={"name": prof_name}
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('name'),
                    'rating': data.get('average_rating'),
                    'slug': data.get('slug')
                }
        except:
            pass

    return None


async def get_course_gpa(course_code: str) -> Optional[float]:
    """Get average GPA for a course from PlanetTerp"""
    if not course_code:
        return None

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{BASE_URL}/course",
                params={"name": course_code}
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('average_gpa')
        except:
            pass

    return None


async def enrich_section_with_ratings(section: Dict, course_code: str) -> Dict:
    """Add professor rating and course GPA to a section"""
    enriched = section.copy()

    # Get professor rating
    prof_data = await get_professor_rating(section.get('instructor', ''))
    if prof_data:
        enriched['prof_rating'] = prof_data.get('rating')
        enriched['prof_slug'] = prof_data.get('slug')

    # Get course GPA
    course_gpa = await get_course_gpa(course_code)
    if course_gpa:
        enriched['course_gpa'] = course_gpa

    return enriched
