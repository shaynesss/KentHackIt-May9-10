import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

_SYSTEM_INSTRUCTION = """You are a furious British senior recruiter who has completely lost patience. You have 3 sentences maximum. No build up, no intro — hit the most embarrassing specific thing on their CV immediately. Second sentence escalates or adds another brutal specific observation. Final sentence is the most devastating backhanded compliment possible. Every word must earn its place. Be specific to their actual CV content — name real things from it. Punchy, fast, specific, brutal."""


def roast_cv(cv_text: str, grade_output: dict) -> str:
    prompt = f"CV: {cv_text}\n\nIssues found: {grade_output['issues']}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=_SYSTEM_INSTRUCTION),
        contents=prompt,
    )
    return response.text
