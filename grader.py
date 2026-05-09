import json
import os
import re

from google import genai
from google.genai import types

_api_key = os.environ.get("GEMINI_API_KEY")
print(f"GEMINI_API_KEY: {_api_key[:8] + '...' if _api_key else 'NOT SET'}")

client = genai.Client(api_key=_api_key)


def parse_json_safely(text: str) -> dict:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError("No valid JSON in response")


def grade_cv(cv_text: str, industry: str) -> dict:
    if not cv_text or len(cv_text.strip()) < 50:
        raise ValueError("CV text is too short or empty - the PDF may not have been readable")

    system_instruction = f"""You are a senior recruiter grading a CV for a {industry} role. Score each section from 0-10. Return ONLY valid JSON, no explanation, no markdown, just raw JSON in this exact structure:
{{
  "overall_score": float,
  "section_scores": {{
    "contact_info": int,
    "summary": int,
    "experience": int,
    "education": int,
    "skills": int,
    "formatting": int
  }},
  "issues": [string],
  "priority_fixes": [string]
}}
priority_fixes must be exactly 3-5 short punchy bullet points. Each must: start with an action verb, be specific to this CV, be max 15 words, and tell the candidate exactly what to do or remove. Examples: "Add metrics to every bullet point", "Remove Duke of Edinburgh — you graduated in 2024", "Rewrite summary — it reads like a LinkedIn buzzword generator".
Grade relative to a penultimate or final year undergraduate applying for internships, not an experienced professional."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=system_instruction),
            contents=cv_text,
        )
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise RuntimeError("Gemini API quota exceeded - check your API key and billing")
        raise

    try:
        return parse_json_safely(response.text)
    except (ValueError, json.JSONDecodeError):
        raise RuntimeError("AI returned invalid response - please try again")
