## KentHackIt 2026 — Hackathon Project

AI.GMI is a web app that grades and roasts CVs using AI. Users select an industry, upload their own CV or pick from template CVs, and receive a structured grade with brutal feedback. An ElevenLabs-voiced narration delivers the roast. The app is live at http://78.141.247.63:8000 and accessible via QR code for live demos.

## Architecture

```
User uploads CV (PDF) or selects template
        ↓
React + Vite frontend (served from FastAPI)
        ↓
FastAPI backend (Vultr Compute — London)
        ↓
pdfplumber extracts text [PDF uploads only]
        ↓
Gemini 2.5 Flash — Grader Agent
        ↓
Gemini 2.5 Flash — Roaster Agent
        ↓
ElevenLabs TTS — audio generation
        ↓
Frontend renders grade + roast + audio
```


## File Structure
```
KentHackIt-May9-10/
├── frontend/
│   ├── src/
│   │   └── App.jsx
│   ├── public/
│   │   └── logo.png
│   └── dist/
├── static/
├── venv/
├── app.py
├── grader.py
├── roaster.py
├── pipeline.py
├── voice.py
├── requirements.txt
└── nohup.out
```

## Agent Design

### Grader Agent — grader.py

Model: Gemini 2.5 Flash

Input: CV text + industry
```
Output: structured JSON:
{
  "overall_score": 6.4,
  "section_scores": {
    "contact_info": 6,
    "summary": 5,
    "experience": 7,
    "education": 8,
    "skills": 6,
    "formatting": 6
  },
  "issues": ["issue 1", "issue 2"],
  "priority_fixes": ["fix 1", "fix 2", "fix 3"]
}
```
Scored 0–10 per section, graded relative to penultimate/final year undergraduates applying for internships. priority_fixes returns 3–5 punchy action-verb bullets, max 15 words each, specific to the CV.

### Roaster Agent — roaster.py

Model: Gemini 2.5 Flash

Input: CV text + grader JSON output

Output: 3-sentence roast — hits the most embarrassing specific detail immediately, includes a disbelieving "Hahahaha", ends with a devastating backhanded compliment.

### Voice Layer — voice.py

ElevenLabs API converts roast text to audio via client.text_to_speech.convert(). Audio saved to static/roast.mp3 and served to the frontend.



## Template CVs (hardcoded in frontend)

Junior React Dev — Tech, poor formatting, good projects
Mid AI Researcher — Data Science, strong metrics and internship experience


## Edge Case Handling

Empty or unreadable PDF → returns clear error message
PDF under 50 characters extracted → flags as unreadable
Non-PDF file uploaded → rejected with error message
No file selected → caught before API call
Gemini returns malformed JSON → safe regex parser extracts valid JSON
API quota exceeded → returns user-friendly error

## Tech Stack
```
Frontend: React + Vite (single-file App.jsx, no external UI libraries)
Backend: FastAPI + uvicorn
PDF parsing: pdfplumber
Grading agent: Gemini 2.5 Flash
Roasting agent: Gemini 2.5 Flash
Voice: ElevenLabs API
Output validation: regex JSON parser
Hosting: Vultr Cloud Compute (London, Ubuntu 24.04, 2GB RAM, 55GB SSD)
Version control: GitHub
Dev tooling: Claude Code
```
## Dependencies

fastapi
uvicorn
python-multipart
pdfplumber
google-genai
elevenlabs

pip install -r requirements.txt

## Environment Variables

export GEMINI_API_KEY="your-key"
export ELEVENLABS_API_KEY="your-key"

## Deployment — Vultr

Firewall rules: 
TCP 22 (SSH),
TCP 8000 (app)
```
cd frontend && npm run build          # build React app
cd ..
source venv/bin/activate
export GEMINI_API_KEY="your-key"
export ELEVENLABS_API_KEY="your-key"
nohup uvicorn app:app --host 0.0.0.0 --port 8000 &
```

