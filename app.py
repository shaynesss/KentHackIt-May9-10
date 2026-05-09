import tempfile
import os

import pdfplumber
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CV Grader</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; padding: 2rem; }
    .card { background: #fff; border-radius: 12px; padding: 2rem; max-width: 640px; margin: 0 auto; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
    h1 { font-size: 1.6rem; margin-bottom: 1.5rem; }
    label { display: block; font-weight: 600; margin-bottom: .4rem; }
    select, input[type=file] { width: 100%; padding: .6rem .8rem; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; margin-bottom: 1.2rem; background: #fafafa; }
    button { width: 100%; padding: .75rem; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }
    button:disabled { opacity: .6; cursor: not-allowed; }
    #results { margin-top: 1.8rem; display: none; }
    .score-bar { display: flex; align-items: center; gap: .8rem; margin-bottom: .5rem; }
    .score-bar span:first-child { width: 120px; font-size: .85rem; color: #555; }
    .bar-track { flex: 1; background: #e5e7eb; border-radius: 99px; height: 10px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 99px; background: #2563eb; transition: width .4s; }
    .overall { font-size: 2.5rem; font-weight: 700; color: #2563eb; text-align: center; margin-bottom: 1rem; }
    .section-title { font-weight: 700; margin: 1.2rem 0 .5rem; font-size: 1rem; }
    ul { padding-left: 1.2rem; }
    li { margin-bottom: .3rem; font-size: .9rem; color: #444; }
    .roast { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 8px; font-size: .9rem; line-height: 1.6; white-space: pre-wrap; }
    #roast-audio { width: 100%; margin-top: .8rem; }
    .error { color: #dc2626; margin-top: 1rem; font-size: .9rem; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: .75rem 1rem; display: none; }
    .error.visible { display: block; }
    #spinner { display: none; text-align: center; margin-top: 1rem; color: #555; }

    .templates-label { font-weight: 600; margin-bottom: .6rem; }
    .templates-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin-bottom: 1.2rem; }
    .tpl-card { border: 2px solid #e5e7eb; border-radius: 10px; padding: .85rem 1rem; cursor: pointer; transition: border-color .15s, background .15s; background: #fafafa; }
    .tpl-card:hover { border-color: #93c5fd; background: #eff6ff; }
    .tpl-card.selected { border-color: #2563eb; background: #eff6ff; }
    .tpl-card .tpl-title { font-weight: 700; font-size: .9rem; margin-bottom: .2rem; }
    .tpl-card .tpl-sub { font-size: .78rem; color: #6b7280; }
    .divider { display: flex; align-items: center; gap: .75rem; margin-bottom: 1.2rem; color: #9ca3af; font-size: .85rem; }
    .divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #e5e7eb; }
    #upload-section { transition: opacity .2s; }
    #upload-section.hidden { opacity: .35; pointer-events: none; }
  </style>
</head>
<body>
  <div class="card">
    <h1>CV Grader</h1>
    <form id="form">
      <label for="industry">Industry</label>
      <select id="industry" name="industry">
        <option value="Finance">Finance</option>
        <option value="Tech">Tech</option>
        <option value="Data Science">Data Science</option>
        <option value="Marketing">Marketing</option>
        <option value="Consulting">Consulting</option>
      </select>

      <div class="templates-label">Try a template CV</div>
      <div class="templates-grid">
        <div class="tpl-card" data-id="overconfident">
          <div class="tpl-title">The Overconfident Graduate</div>
          <div class="tpl-sub">Finance &middot; buzzwords, zero substance</div>
        </div>
        <div class="tpl-card" data-id="underdog">
          <div class="tpl-title">The Underdog</div>
          <div class="tpl-sub">Tech &middot; real skills, terrible formatting</div>
        </div>
        <div class="tpl-card" data-id="career-changer">
          <div class="tpl-title">The Career Changer</div>
          <div class="tpl-sub">Marketing &middot; irrelevance, poorly reframed</div>
        </div>
        <div class="tpl-card" data-id="solid">
          <div class="tpl-title">The Solid Candidate</div>
          <div class="tpl-sub">Data Science &middot; metrics, structure, clarity</div>
        </div>
      </div>

      <div class="divider">or upload your own</div>

      <div id="upload-section">
        <label for="cv">Upload CV (PDF)</label>
        <input type="file" id="cv" name="cv" accept=".pdf">
      </div>

      <button type="submit" id="submit-btn" style="margin-top:1.2rem">Grade my CV</button>
    </form>
    <div id="spinner">Analysing your CV...</div>
    <div id="error" class="error"></div>
    <div id="results">
      <div class="overall" id="overall-score"></div>
      <div class="section-title">Section Scores</div>
      <div id="section-scores"></div>
      <div class="section-title">Issues</div>
      <ul id="issues"></ul>
      <div class="section-title">Priority Fixes</div>
      <ul id="priority-fixes"></ul>
      <div class="section-title">Roast</div>
      <div class="roast" id="roast"></div>
      <audio id="roast-audio" controls autoplay style="display:none"></audio>
    </div>
  </div>

  <script>
    const TEMPLATES = {
      overconfident: {
        industry: "Finance",
        text: `Maximilian Blackwood
max.blackwood@gmail.com | 07700 123456 | London | LinkedIn: linkedin.com/in/maxblackwood

PROFILE
Dynamic, results-driven visionary with a passion for leveraging synergistic financial paradigms to deliver stakeholder value. Entrepreneurial mindset with strong leadership DNA and a proven track record of excellence.

EDUCATION
BSc Economics, University of Surrey, 2024 (Predicted 2:1)
Relevant modules: Introduction to Finance, Microeconomics, Excel for Business

EXPERIENCE
Investment Banking Intern (Virtual), Goldman Sachs Forage Programme, June 2023 (5 days)
- Completed online modules about M&A transactions
- Built a basic DCF model using provided template
- Learned about financial modelling best practices

Brand Ambassador, Red Bull, Oct 2022 – Mar 2023
- Distributed 200+ cans at university events
- Managed social media stories for campus campaign

Treasurer, Economics Society, 2022–2023
- Tracked society expenses using Excel
- Organised one networking event with 30 attendees

SKILLS
Excel (pivot tables), PowerPoint, Bloomberg (aware of), Python (beginner), Leadership, Teamwork, Communication, Attention to detail, Fast learner

ACHIEVEMENTS
- Completed Goldman Sachs Virtual Internship with Distinction
- Dean's List (one semester)
- Captain of 5-a-side football team`
      },
      underdog: {
        industry: "Tech",
        text: `jane doe
janedoe92@hotmail.com
07711 000000

about me
i am a software developer who likes coding. i know lots of programming languages and i am a hard worker. looking for a job in tech.

skills
python, javascript, react, node.js, postgresql, docker, kubernetes, aws, terraform, git, ci/cd, graphql, redis, fastapi, linux

work
freelance developer 2021-now
   did lots of projects for clients. built websites. fixed bugs. made apis.

tesco, shelf stacker, 2019-2021
   stacked shelves. worked in a team.

education
bsc computer science, university of kent, 2:1, 2019

projects
- built a full-stack e-commerce platform from scratch with react frontend, node backend, postgresql database, stripe payments, deployed on aws with terraform — handles 500 concurrent users
- created open source python library for parsing financial data, 200+ github stars, used by 3 fintech startups
- built real-time collaborative coding tool using websockets and operational transforms

references available on request`
      },
      "career-changer": {
        industry: "Marketing",
        text: `Sandra Hutchins
sandra.hutchins@yahoo.co.uk | 07800 555123 | Birmingham

OBJECTIVE
Seeking to transition my 8 years of primary school teaching experience into a dynamic marketing role where I can utilise my communication skills.

WORK EXPERIENCE
Year 4 Primary School Teacher, St. Joseph's C of E, 2016–2024
- Delivered lessons to 30 students daily (transferable to presenting to stakeholders)
- Organised parents' evenings (transferable to client communication)
- Managed classroom budget of £500/year (transferable to budget management)
- Created displays for the classroom (transferable to visual content creation)
- Wrote end-of-year reports (transferable to copywriting)
- Used a SMART board (transferable to digital tools)

Teaching Assistant, Greenfield Primary, 2014–2016
- Supported lead teacher
- Helped children with reading

EDUCATION
BA English Literature, Coventry University, 2:2, 2013
PGCE Primary Education, 2014

SKILLS
Microsoft Word, PowerPoint, Email, Facebook (personal use), Creative thinking, Public speaking, Patience

INTERESTS
Baking, Reading, Yoga, Following marketing influencers on Instagram`
      },
      solid: {
        industry: "Data Science",
        text: `Priya Nair
priya.nair@gmail.com | 07900 234567 | London | github.com/priyanair

EDUCATION
MEng Computer Science with Data Science, University of Edinburgh, First Class, 2024
Dissertation: "Predicting hospital readmission rates using ensemble methods" — 94% AUC on held-out test set

EXPERIENCE
Data Science Intern, Monzo Bank, Jun–Sep 2023
- Built a customer churn prediction model (XGBoost) reducing churn by 12% over 3 months
- Automated reporting pipeline in Python/Airflow, saving 8 analyst hours per week
- A/B tested two onboarding flows; analysed results for 45,000 users using bootstrapped confidence intervals

Research Assistant, Edinburgh NLP Group, Jan–May 2023
- Fine-tuned BERT on domain-specific corpus, improving F1 by 6 points over baseline
- Co-authored workshop paper accepted at EMNLP 2023

PROJECTS
Spotify Recommendation Engine — Collaborative filtering + content-based hybrid; 40% improvement in NDCG vs. baseline
UK Road Safety Dashboard — Streamlit app analysing 1.2M accident records; featured on /r/dataisbeautiful (2.4k upvotes)

SKILLS
Python (pandas, scikit-learn, PyTorch), SQL, R, Spark, dbt, Airflow, Docker, AWS (S3, SageMaker), Git

AWARDS
Best Dissertation Prize, School of Informatics 2024
Lloyds Banking Group Data Science Scholarship 2022`
      }
    };

    let selectedTemplateId = null;

    document.querySelectorAll('.tpl-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.dataset.id;
        if (selectedTemplateId === id) {
          selectedTemplateId = null;
          card.classList.remove('selected');
          document.getElementById('upload-section').classList.remove('hidden');
        } else {
          document.querySelectorAll('.tpl-card').forEach(c => c.classList.remove('selected'));
          card.classList.add('selected');
          selectedTemplateId = id;
          document.getElementById('industry').value = TEMPLATES[id].industry;
          document.getElementById('upload-section').classList.add('hidden');
        }
      });
    });

    document.getElementById('form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('submit-btn');
      const spinner = document.getElementById('spinner');
      const errorEl = document.getElementById('error');
      const results = document.getElementById('results');

      btn.disabled = true;
      spinner.style.display = 'block';
      errorEl.textContent = '';
      errorEl.classList.remove('visible');
      results.style.display = 'none';

      const industry = document.getElementById('industry').value;

      let res;
      try {
        if (selectedTemplateId) {
          const fd = new FormData();
          fd.append('cv_text', TEMPLATES[selectedTemplateId].text);
          fd.append('industry', industry);
          res = await fetch('/grade-text', { method: 'POST', body: fd });
        } else {
          const fileInput = document.getElementById('cv');
          if (!fileInput.files.length) {
            throw new Error('Please select a PDF or choose a template.');
          }
          const fd = new FormData();
          fd.append('file', fileInput.files[0]);
          fd.append('industry', industry);
          res = await fetch('/grade', { method: 'POST', body: fd });
        }

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
          throw new Error(err.detail || res.statusText);
        }
        const data = await res.json();

        document.getElementById('overall-score').textContent =
          `Overall: ${data.overall_score.toFixed(1)} / 10`;

        const scoresEl = document.getElementById('section-scores');
        scoresEl.innerHTML = '';
        for (const [key, val] of Object.entries(data.section_scores)) {
          const label = key.replace(/_/g, ' ');
          scoresEl.innerHTML += `
            <div class="score-bar">
              <span>${label}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${val * 10}%"></div></div>
              <span>${val}/10</span>
            </div>`;
        }

        document.getElementById('issues').innerHTML =
          data.issues.map(i => `<li>${i}</li>`).join('');
        document.getElementById('priority-fixes').innerHTML =
          data.priority_fixes.map(f => `<li>${f}</li>`).join('');

        document.getElementById('roast').textContent = data.roast;

        const audio = document.getElementById('roast-audio');
        audio.src = '/static/roast.mp3?t=' + Date.now();
        audio.style.display = 'block';
        audio.load();
        audio.play().catch(() => {});

        results.style.display = 'block';
      } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.add('visible');
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    });
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


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
