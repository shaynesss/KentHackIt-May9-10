import tempfile
import os

import pdfplumber
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pipeline import run_pipeline
from voice import generate_roast_audio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/grade")
async def grade(file: UploadFile = File(...), industry: str = Form(...)):
    if not file or not file.filename:
        return JSONResponse(status_code=422, content={"detail": "Please upload a CV."})

    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=422, content={"detail": "Only PDF files are supported."})

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        with pdfplumber.open(tmp_path) as pdf:
            cv_text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    finally:
        os.unlink(tmp_path)

    if len(cv_text) < 50:
        return JSONResponse(status_code=422, content={"detail": "Could not read PDF — make sure it is not a scanned image or password protected."})

    try:
        result = run_pipeline(cv_text, industry)
        generate_roast_audio(result["roast"])
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

    return result


@app.post("/grade-text")
async def grade_text(cv_text: str = Form(...), industry: str = Form(...)):
    if not cv_text.strip():
        return JSONResponse(status_code=422, content={"detail": "CV text is empty."})

    try:
        result = run_pipeline(cv_text, industry)
        generate_roast_audio(result["roast"])
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

    return result


app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
