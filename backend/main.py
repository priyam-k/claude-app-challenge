import base64
import io
import os
import re

import anthropic
from calendar_scraper import fetch_umd_events, search_events
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

# Import our scrapers
from scraper import (
    GENED_CODES,
    fetch_course_sections,
    fetch_department_courses,
    fetch_gened_courses,
    get_current_term,
    search_courses,
)

load_dotenv()

app = FastAPI(title="Testudo++ API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://claude-app-challenge-930s3wbyt-priyam-ks-projects-69af5de8.vercel.app",  # Vercel production
        "https://claude-app-challenge.vercel.app",  # Vercel custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Enhanced campus data with CORRECT UMD geography
# IMPORTANT: North is bottom-right, South is top-left, McKeldin is the centerline
CAMPUS_DATA = {
    "dining": [
        {
            "name": "251 North Dining Hall",
            "hours": "Mon-Fri: 7am-9pm, Sat-Sun: 10am-8pm",
            "location": "NORTH campus, bottom-right area of campus",
            "walk_times": {
                "McKeldin": "12 min",
                "Stamp": "10 min",
                "Iribe": "20 min",
                "Cole Field House": "3 min",
                "Cambridge": "10 min",
                "Ellicott": "5 min",
            },
            "options": ["vegetarian", "vegan", "halal", "all-you-can-eat"],
        },
        {
            "name": "South Campus Dining Hall",
            "hours": "Mon-Fri: 7am-8pm, Sat-Sun: 10am-7pm",
            "location": "SOUTH campus, top-left area near Ellicott Hall (FAR from Cambridge - 20 min walk)",
            "walk_times": {
                "Ellicott": "20 min",
                "Eppley": "25 min",
                "Stamp": "12 min",
                "McKeldin": "5 min",
                "Cambridge": "20 min",
                "Yahentamitsi": "18 min",
            },
            "options": ["vegetarian", "vegan", "all-you-can-eat"],
            "note": "NOT near Cambridge Community - Cambridge is on opposite side of campus",
        },
        {
            "name": "Yahentamitsi Dining Hall",
            "hours": "Mon-Fri: 7am-9pm, Sat-Sun: 10am-8pm",
            "location": "NORTH campus area, near Cambridge Community",
            "walk_times": {
                "Cambridge": "2 min",
                "Oakland": "7 min",
                "Cumberland": "3 min",
                "McKeldin": "10 min",
                "South Campus Dining": "25 min",
                "Ellicott": "22 min",
            },
            "options": ["vegetarian", "vegan", "kosher", "all-you-can-eat"],
            "note": "VERY CLOSE to Cambridge Community (2 min)",
        },
        {
            "name": "The Diner",
            "hours": "Mon-Fri: 7am-midnight, Sat-Sun: 10am-midnight",
            "location": "inside Stamp Student Union, center campus",
            "walk_times": {
                "Stamp": "0 min",
                "McKeldin": "5 min",
                "Hornbake": "6 min",
                "Ellicott": "12 min",
                "Cambridge": "12 min",
            },
            "options": ["vegetarian", "late night", "grab-and-go"],
        },
    ],
    "shuttles": [
        {
            "route": "104 (Campus Connector)",
            "stops": [
                "Iribe Center (north)",
                "Stamp Student Union (center)",
                "Eppley Rec Center (south)",
                "Cole Field House (north)",
            ],
            "frequency": "Every 15 min",
            "hours": "7am-7pm Mon-Fri",
            "use_for": "Quick trips between north and south campus",
        },
        {
            "route": "111 (Blue)",
            "stops": [
                "McKeldin Library (center)",
                "Kim Engineering",
                "Eppley (south campus)",
                "Regents Drive Garage",
            ],
            "frequency": "Every 10 min",
            "hours": "7am-11pm Mon-Fri",
            "use_for": "Getting to south campus from center",
        },
        {
            "route": "115 (Orange)",
            "stops": ["Stamp", "College Park Metro", "The View Apartments"],
            "frequency": "Every 20 min",
            "hours": "7am-11pm daily",
            "use_for": "Off-campus trips and metro access",
        },
    ],
    "campus_layout": {
        "north_campus_area": {
            "buildings": [
                "Iribe Center",
                "Cole Field House",
                "Cambridge Community",
                "Ellicott Community",
                "Oakland Hall",
                "Cumberland Hall",
                "Yahentamitsi Dining",
                "Eppley Recreation Center",
                "251 North Dining",
            ],
            "location": "Bottom-right area of campus map",
            "description": "Computer science, engineering, and north dorms",
        },
        "center_campus": {
            "buildings": [
                "McKeldin Library",
                "Stamp Student Union",
                "Hornbake Library",
                "Main Chapel",
                "Reckord Armory",
            ],
            "location": "Central area - McKeldin is the centerline",
            "description": "Heart of campus - libraries, student union, most classes",
        },
        "south_campus_area": {
            "buildings": [
                "South Campus Dining Hall",
                "South Campus Commons",
            ],
            "location": "Top-left area of campus map (OPPOSITE from Cambridge)",
            "description": "Residential area and recreation",
        },
    },
    "walking_times": {
        "McKeldin to Stamp": "5 min",
        "McKeldin to Iribe": "10 min",
        "McKeldin to Cambridge": "15 min",
        "McKeldin to Ellicott": "17 min",
        "Stamp to Cambridge": "10 min",
        "Stamp to Ellicott": "12 min",
        "Stamp to Eppley": "15 min",
        "Cambridge to Ellicott": "5 min",
        "Cambridge to South Campus Dining": "20 min (FAR apart)",
        "Cambridge to Yahentamitsi": "2 min (VERY CLOSE)",
        "Ellicott to South Campus Dining": "20 min (cross campus)",
        "Ellicott to Cambridge": "5 min",
        "Iribe to Cambridge": "10 min",
        "Cole Field House to Cambridge": "8 min",
        "251 North Dining to Cambridge": "10 min",
    },
}


class ScheduleQuery(BaseModel):
    query: str
    term_id: str = None


class AdvisorQuery(BaseModel):
    query: str
    term_id: str = None


class CompassQuery(BaseModel):
    query: str


@app.get("/")
def root():
    return {"message": "Testudo++ API is running"}


@app.get("/api/terms")
def get_available_terms():
    """Return available term options"""
    from datetime import datetime

    year = datetime.now().year

    return {
        "terms": [
            {"id": f"{year}05", "label": f"Summer {year}"},
            {"id": f"{year}08", "label": f"Fall {year}"},
            {"id": f"{year}12", "label": f"Winter {year+1}"},
            {"id": f"{year+1}01", "label": f"Spring {year+1}"},
        ],
        "current": get_current_term(),
    }


@app.post("/api/schedule/build")
async def build_schedule(request: ScheduleQuery):
    """NEW 2-step schedule builder with actual times and sections"""
    from schedule_builder import build_schedules_from_courses, find_relevant_courses

    term_id = request.term_id or get_current_term()

    try:
        # Step 1: Find relevant courses (20-30 courses)
        courses, preferences, specific_courses = await find_relevant_courses(
            request.query, term_id
        )

        # Step 2: Build schedules with conflict detection
        schedules = await build_schedules_from_courses(
            courses, preferences, term_id, specific_courses
        )

        # Format response
        formatted_schedules = []
        for schedule in schedules:
            formatted_courses = []
            for item in schedule["courses"]:
                section = item["section"]
                formatted_courses.append(
                    {
                        "code": item["course_code"],
                        "title": item["course_title"],
                        "credits": item["credits"],
                        "section": section["section_id"],
                        "instructor": section["instructor"],
                        "prof_rating": section.get("prof_rating"),
                        "course_gpa": item.get("course_gpa"),
                        "days": section["days"],
                        "time": section["time"],
                        "location": section["location"],
                        "open_seats": section["open_seats"],
                    }
                )

            formatted_schedules.append(
                {
                    "courses": formatted_courses,
                    "total_credits": schedule["total_credits"],
                }
            )

        return {
            "schedules": formatted_schedules,
            "courses_found": len(courses),
            "explanation": f"{len(formatted_schedules)} schedule(s) from {len(courses)} relevant courses found",
        }

    except Exception as e:
        print(f"Schedule building error: {e}")
        import traceback

        traceback.print_exc()
        return {
            "schedules": [],
            "courses_found": 0,
            "explanation": f"0 schedules from 0 courses found - Error: {str(e)}"
        }


@app.post("/api/events/scan")
async def scan_event(file: UploadFile = File(...)):
    """Extract event details from an image using OCR + Claude"""

    # Read and encode image
    image_data = await file.read()
    image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

    # Determine media type
    media_type = file.content_type or "image/jpeg"

    # Use Claude with vision to extract event details
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Extract event details from this flyer/image. Return JSON with:
{
  "event": {
    "title": "Event Name",
    "datetime": "YYYYMMDDTHHMMSS format for ics",
    "location": "Location",
    "description": "Brief description"
  }
}

If you can't find a field, use "Not specified".""",
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text

    # Parse JSON from response
    try:
        import json

        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response_text[start:end])
    except:
        pass

    # Fallback
    return {
        "event": {
            "title": "Campus Event",
            "datetime": "20250415T180000",
            "location": "Stamp Student Union",
            "description": "Event details extracted from image",
        }
    }


@app.get("/api/events/upcoming")
async def get_upcoming_events():
    """Get upcoming UMD events"""
    events = await fetch_umd_events(days_ahead=14)
    return {"events": events}


@app.post("/api/compass/ask")
async def campus_compass(request: CompassQuery):
    """Answer campus-related queries using structured data + AI"""
    import json

    # Fetch upcoming events
    events = await fetch_umd_events(days_ahead=14)

    # Prepare events for context (limit to relevant ones)
    events_context = events[:10]

    prompt = f"""You are a UMD campus assistant with ACCURATE knowledge of campus geography. Answer this question using ONLY the provided campus data.

Question: "{request.query}"

Campus Data:
Dining Halls: {json.dumps(CAMPUS_DATA['dining'], indent=2)}
Shuttle Routes: {json.dumps(CAMPUS_DATA['shuttles'], indent=2)}
Campus Layout: {json.dumps(CAMPUS_DATA['campus_layout'], indent=2)}
Walking Times: {json.dumps(CAMPUS_DATA['walking_times'], indent=2)}

Upcoming Events:
{json.dumps(events_context, indent=2)}

CRITICAL LOCATION RULES - DO NOT DEVIATE:
1. McKeldin Library = CENTER of campus (the centerline)
2. Cambridge Community is in NORTH campus area (bottom-right on map)
3. Ellicott Hall is in SOUTH campus area (top-left on map)
4. Cambridge and Ellicott are on OPPOSITE sides of campus (22 min walk apart)
5. South Campus Dining Hall is NEAR Ellicott (3 min), FAR from Cambridge (20 min)
6. Yahentamitsi Dining is NEAR Cambridge (2 min), FAR from South Campus Dining (25 min)
7. NEVER say Cambridge is near South Campus Dining Hall - they are 20 min apart
8. NEVER say Ellicott is near Cambridge - they are 22 min apart on opposite sides
9. ONLY use the walking times from the data provided - DO NOT guess or estimate

When answering:
- Use EXACT walking times from the data
- Mention specific dining hall names with their distances
- Recommend shuttles for 12+ min walks
- Include hours if relevant
- For events, mention date/time/location"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"answer": message.content[0].text}


@app.post("/api/advisor/recommend")
async def course_advisor(request: AdvisorQuery):
    """Recommend courses based on requirements using real UMD course data"""
    import json

    # STEP 1: Use AI to parse the query into structured filters
    parse_prompt = f"""Parse this course search query into structured filters. Return ONLY valid JSON.

Query: "{request.query}"

Extract:
- departments: list of 2-4 letter department codes (CMSC, MATH, PHIL, HIST, ENGL, etc.)
- level: course level (1, 2, 3, or 4 for 100/200/300/400 level, or null)
- geneds: list of gen-ed codes if mentioned (FSOC, FSMA, DSHU, DSNS, DSHS, DVCC, etc.)
- keywords: list of topic keywords (AI, machine learning, algorithms, etc.)
- course_type: "core" or "elective" or null
- search_mode: "geneds" if asking about gen-eds specifically, "departments" if asking about specific departments, or "keywords" otherwise

IMPORTANT: If the query is about gen-eds or general education requirements, set search_mode to "geneds" and populate the geneds array.
If asking for courses that satisfy multiple gen-eds, set search_mode to "geneds" and leave geneds empty (we'll search all).

Return JSON:
{{
  "departments": ["DEPT"],
  "level": null,
  "geneds": [],
  "keywords": [],
  "course_type": null,
  "search_mode": "keywords"
}}"""

    parse_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": parse_prompt}],
    )

    # Parse the AI's filter extraction
    filters = {
        "departments": [],
        "level": None,
        "geneds": [],
        "keywords": [],
        "course_type": None,
        "search_mode": "keywords",
    }

    try:
        parse_text = parse_response.content[0].text
        start = parse_text.find("{")
        end = parse_text.rfind("}") + 1
        if start >= 0 and end > start:
            filters = json.loads(parse_text[start:end])
            print(f"Advisor parsed filters: {filters}")
    except Exception as e:
        print(f"Filter parsing error: {e}")

    # STEP 2: Fetch courses based on parsed filters
    courses_to_fetch = []
    search_mode = filters.get("search_mode", "keywords")

    # If looking for gen-eds specifically, fetch from multiple gen-ed categories
    if search_mode == "geneds":
        specified_geneds = filters.get("geneds", [])

        if specified_geneds:
            # Fetch specific gen-ed categories
            for gened in specified_geneds[:3]:
                if gened.upper() in GENED_CODES:
                    courses = await fetch_gened_courses(gened.upper())
                    courses_to_fetch.extend(courses)
        else:
            # Fetch from multiple gen-ed categories to find courses with multiple gen-eds
            popular_geneds = ["DSHS", "DSHU", "DSNS", "DVCC", "DVUP", "FSMA", "FSAR"]
            for gened in popular_geneds[:5]:
                courses = await fetch_gened_courses(gened)
                courses_to_fetch.extend(courses)
    else:
        # Fetch by departments
        for dept in filters.get("departments", [])[:3]:
            courses = await fetch_department_courses(dept.upper())
            courses_to_fetch.extend(courses)

        # Also fetch by gen-eds if specified
        for gened in filters.get("geneds", [])[:2]:
            if gened.upper() in GENED_CODES:
                courses = await fetch_gened_courses(gened.upper())
                courses_to_fetch.extend(courses)

    # Default fallback
    if not courses_to_fetch:
        courses_to_fetch.extend(await fetch_department_courses("CMSC"))

    # STEP 3: Apply filters from AI parsing

    # Apply level filter
    if filters.get("level"):
        level_str = str(filters["level"])
        filtered = [
            c
            for c in courses_to_fetch
            if len(c["code"]) >= 5 and c["code"][4] == level_str
        ]
        if filtered:
            courses_to_fetch = filtered

    # Apply keyword filters
    keywords = filters.get("keywords", [])
    if keywords:
        keyword_courses = []
        for c in courses_to_fetch:
            course_text = (c["title"] + " " + c.get("description", "")).upper()
            if any(keyword.upper() in course_text for keyword in keywords):
                keyword_courses.append(c)
        if keyword_courses:
            courses_to_fetch = keyword_courses

    # Apply course type filter
    if filters.get("course_type") == "core":
        core_courses = [
            c
            for c in courses_to_fetch
            if "prerequisite" in c.get("description", "").lower()
        ]
        if core_courses:
            courses_to_fetch = core_courses
    elif filters.get("course_type") == "elective":
        elective_courses = [
            c
            for c in courses_to_fetch
            if "prerequisite" not in c.get("description", "").lower()[:200]
        ]
        if elective_courses:
            courses_to_fetch = elective_courses

    # Prepare courses for prompt
    courses_for_prompt = []
    for c in courses_to_fetch[:25]:
        courses_for_prompt.append(
            {
                "code": c["code"],
                "title": c["title"],
                "credits": c["credits"],
                "geneds": c.get("geneds", []),
                "description": (
                    c["description"][:150]
                    if len(c.get("description", "")) > 150
                    else c.get("description", "")
                ),
            }
        )

    # For gen-ed searches, prioritize courses with multiple gen-eds
    if search_mode == "geneds" and "multiple" in request.query.lower():
        # Filter to only courses with 2+ gen-eds
        multi_gened_courses = [
            c for c in courses_for_prompt if len(c.get("geneds", [])) >= 2
        ]
        if multi_gened_courses:
            courses_for_prompt = multi_gened_courses[:25]

    prompt = f"""You are a UMD academic advisor. The student asks: "{request.query}"

Available courses:
{json.dumps(courses_for_prompt, indent=2)}

Recommend 3-4 courses that best match their needs. Return ONLY JSON in this format:
{{
  "recommendations": [
    {{
      "code": "COURSE_CODE",
      "title": "Course Title",
      "description": "Brief description from the course data",
      "reason": "Why this course matches their requirement"
    }}
  ]
}}

IMPORTANT: If the query asks about gen-eds or multiple gen-eds, focus on courses with geneds listed and mention which gen-eds they satisfy in the reason.
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response_text[start:end])
    except Exception as e:
        print(f"JSON parsing error: {e}")

    # Fallback
    return {
        "recommendations": (
            courses_for_prompt[:3]
            if courses_for_prompt
            else [
                {
                    "code": "CMSC131",
                    "title": "Object-Oriented Programming I",
                    "description": "Introduction to programming",
                    "reason": "Foundational CS course",
                }
            ]
        )
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
