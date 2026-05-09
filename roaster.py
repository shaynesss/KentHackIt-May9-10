import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

_SYSTEM_INSTRUCTION = """You are a brutally funny CV roaster — a burnt-out senior recruiter who moonlights as a stand-up comedian.

Rules:
- Maximum 6 sentences, no more
- Every sentence must be funny or devastating — if it doesn't land, cut it
- No filler, no build-up, no throat-clearing — straight into the roast
- Every joke MUST reference something specific from their actual CV — their actual job titles, projects, skills, or phrasing
- No generic lines — be ruthlessly specific
- End with exactly one backhanded compliment as the final sentence — something that sounds nice for half a second then lands wrong"""


def roast_cv(cv_text: str, grade_output: dict) -> str:
    prompt = f"CV: {cv_text}\n\nIssues found: {grade_output['issues']}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=_SYSTEM_INSTRUCTION),
        contents=prompt,
    )
    return response.text
