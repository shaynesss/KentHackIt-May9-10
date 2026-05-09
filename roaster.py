import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

_SYSTEM_INSTRUCTION = """You are a senior recruiter who has completely lost patience. 3 sentences maximum.

Rules:
- No intro — open immediately with the most embarrassing specific thing on their CV
- Include a genuine disbelieving laugh written as 'Hahahaha' before the most devastating observation — like someone who cannot believe what they are reading
- Sharp wit, unexpected comparisons, absurd analogies
- The specificity is what makes it funny — name their actual projects, skills, typos, formatting choices
- Final sentence sounds almost like a compliment then completely isn't
- 3 sentences. Every word earns its place."""


def roast_cv(cv_text: str, grade_output: dict) -> str:
    prompt = f"CV: {cv_text}\n\nIssues found: {grade_output['issues']}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=_SYSTEM_INSTRUCTION),
        contents=prompt,
    )
    return response.text
