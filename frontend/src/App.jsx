import { useState, useEffect, useRef } from 'react'

const API = 'http://78.141.247.63:8000'

// ─── Template CVs ──────────────────────────────────────────────────────────

const TEMPLATES = {
  junior_react: {
    industry: 'Tech',
    label: 'Junior React Dev',
    cv_text:
`jane doe
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

references available on request`,
  },
  mid_ai: {
    industry: 'Data Science',
    label: 'Mid AI Researcher',
    cv_text:
`Priya Nair
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
Lloyds Banking Group Data Science Scholarship 2022`,
  },
}

// ─── Industry options ───────────────────────────────────────────────────────

const INDUSTRIES = [
  { id: 'software', label: 'Software Engineering', icon: '💻' },
  { id: 'data',     label: 'Data Science',         icon: '📊' },
  { id: 'cs',       label: 'Computer Science',     icon: '🖥️' },
  { id: 'ai',       label: 'AI Engineering',       icon: '🤖' },
]

// ─── Helpers ────────────────────────────────────────────────────────────────

function scoreMessage(s) {
  if (s < 30)  return "Build some more projects"
  if (s < 60)  return "Keep grinding..."
  if (s <= 76) return "You're going to maybe make it?"
  return "You're gonna make it!"
}

// SVG semicircle gauge — flat edge at bottom, orange arc from left to right
function Gauge({ score }) {
  // M 20 100 A 80 80 0 0 0 180 100  →  CCW arc over the top, total length = π×80
  const arcLen = Math.PI * 80
  const filled = (Math.min(100, Math.max(0, score)) / 100) * arcLen
  return (
    <svg viewBox="0 0 200 105" style={{ width: '100%', maxWidth: 200 }}>
      <path
        d="M 20 100 A 80 80 0 0 0 180 100"
        strokeWidth={16}
        stroke="var(--border)"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M 20 100 A 80 80 0 0 0 180 100"
        strokeWidth={16}
        stroke="#f59e0b"
        fill="none"
        strokeLinecap="round"
        strokeDasharray={`${filled} ${arcLen}`}
      />
    </svg>
  )
}

// ─── Shared header ──────────────────────────────────────────────────────────

function Header({ onReset, theme, onToggleTheme }) {
  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0.9rem 1.25rem',
      borderBottom: '1px solid var(--border)',
    }}>
      <button onClick={onReset} style={{
        background: 'none', border: 'none', cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: '0.35rem',
        fontSize: '1rem', fontWeight: 700, color: 'var(--text)',
      }}>
        <img src="/logo.png" alt="AI GMI" style={{ height: '40px', width: 'auto' }} />
      </button>
      <button onClick={onToggleTheme} style={{
        background: 'none', border: '1px solid var(--border)',
        borderRadius: 999, padding: '0.28rem 0.65rem',
        cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text)',
      }}>
        {theme === 'light' ? '🌙' : '☀️'}
      </button>
    </header>
  )
}

// ─── App ────────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage]         = useState(1)
  const [fading, setFading]     = useState(false)
  const [theme, setTheme]       = useState(() => localStorage.getItem('theme') || 'light')
  const [industry, setIndustry] = useState(null)   // selected id
  const [result, setResult]     = useState(null)   // API response
  const [error, setError]       = useState(null)
  const [audioTs, setAudioTs]   = useState(null)
  const audioRef                = useRef(null)

  // Apply theme to <html>
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  // Splash: fade at 3s, switch page at 3.5s
  useEffect(() => {
    if (page !== 1) return
    const t1 = setTimeout(() => setFading(true), 3000)
    const t2 = setTimeout(() => setPage(2), 3500)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [page])

  const reset = () => {
    setPage(2); setIndustry(null); setResult(null)
    setError(null); setAudioTs(null)
  }

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  // ── API submit ──────────────────────────────────────────────────────────

  const submit = async (fd) => {
    setPage(4)
    setError(null)
    try {
      const endpoint = fd.has('file') ? `${API}/grade` : `${API}/grade-text`
      const res  = await fetch(endpoint, { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Something went wrong')
      setResult(data)
      setAudioTs(Date.now())
      setPage(5)
    } catch (e) {
      setError(e.message)
      setPage(3)
    }
  }

  const submitTemplate = (key) => {
    const tpl = TEMPLATES[key]
    const fd  = new FormData()
    fd.append('cv_text', tpl.cv_text)
    fd.append('industry', tpl.industry)
    submit(fd)
  }

  const submitFile = (file) => {
    const ind  = INDUSTRIES.find(i => i.id === industry)
    const fd   = new FormData()
    fd.append('file', file)
    fd.append('industry', ind?.label ?? 'Tech')
    submit(fd)
  }

  // ── Derived values for results page ────────────────────────────────────

  const score = result ? Math.round(result.overall_score * 10) : 0

  // ─────────────────────────────────────────────────────────────────────────

  return (
    <>
      <style>{`
        :root {
          --bg: #ffffff;
          --card: #ffffff;
          --text: #111111;
          --sub: #6b7280;
          --border: #e5e7eb;
          --accent: #6366f1;
          --roast-bg: #fff7ed;
          --feedback-bg: #eff6ff;
        }
        [data-theme="dark"] {
          --bg: #0f0f0f;
          --card: #1a1a1a;
          --text: #f0f0f0;
          --sub: #9ca3af;
          --border: #333333;
          --accent: #818cf8;
          --roast-bg: #1c1208;
          --feedback-bg: #0c1829;
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
          background: var(--bg);
          color: var(--text);
          font-family: system-ui, -apple-system, sans-serif;
          min-height: 100vh;
          transition: background 0.2s, color 0.2s;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(28px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.6; transform: scale(0.96); }
        }
      `}</style>

      <div style={{ maxWidth: 480, margin: '0 auto', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

        {/* ══ PAGE 1 — Splash ══════════════════════════════════════════════ */}
        {page === 1 && (
          <div style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            opacity: fading ? 0 : 1, transition: 'opacity 0.45s ease',
          }}>
            <img
              src="/logo.png"
              alt="AI GMI"
              style={{ height: '160px', width: 'auto', animation: 'slideUp 0.55s ease forwards' }}
            />
          </div>
        )}

        {/* ══ PAGES 2-5 ════════════════════════════════════════════════════ */}
        {page > 1 && (
          <>
            <Header onReset={reset} theme={theme} onToggleTheme={toggleTheme} />

            {/* ── PAGE 2 — Industry ──────────────────────────────────────── */}
            {page === 2 && (
              <div style={{ flex: 1, padding: '1.5rem 1.25rem', display: 'flex', flexDirection: 'column' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.2rem' }}>
                  Choose Your Industry
                </h1>
                <p style={{ color: 'var(--sub)', fontSize: '0.88rem', marginBottom: '1.4rem' }}>
                  Tell us how you want to be cooked
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.4rem' }}>
                  {INDUSTRIES.map(ind => {
                    const selected = industry === ind.id
                    return (
                      <div
                        key={ind.id}
                        onClick={() => setIndustry(ind.id)}
                        style={{
                          border: `2px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                          borderRadius: 14,
                          padding: '1rem',
                          cursor: 'pointer',
                          background: 'var(--card)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.55rem',
                          transition: 'border-color 0.15s',
                        }}
                      >
                        <span style={{
                          display: 'inline-flex',
                          background: 'var(--border)',
                          borderRadius: 999,
                          padding: '0.28rem 0.55rem',
                          fontSize: '1.1rem',
                          alignSelf: 'flex-start',
                        }}>
                          {ind.icon}
                        </span>
                        <span style={{ fontSize: '0.85rem', fontWeight: 600, flex: 1 }}>{ind.label}</span>
                        <div style={{
                          width: 18, height: 18, borderRadius: '50%',
                          border: `2px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                          background: selected ? 'var(--accent)' : 'transparent',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          alignSelf: 'flex-end',
                          transition: 'background 0.15s, border-color 0.15s',
                        }}>
                          {selected && <span style={{ color: '#fff', fontSize: '0.6rem', fontWeight: 900 }}>✓</span>}
                        </div>
                      </div>
                    )
                  })}
                </div>

                <button
                  disabled={!industry}
                  onClick={() => setPage(3)}
                  style={{
                    width: '100%', padding: '0.85rem',
                    background: industry ? 'var(--accent)' : 'var(--border)',
                    color: industry ? '#fff' : 'var(--sub)',
                    border: 'none', borderRadius: 999,
                    fontSize: '1rem', fontWeight: 600,
                    cursor: industry ? 'pointer' : 'not-allowed',
                    transition: 'background 0.15s, color 0.15s',
                  }}
                >
                  Continue
                </button>
              </div>
            )}

            {/* ── PAGE 3 — Upload ────────────────────────────────────────── */}
            {page === 3 && (
              <div style={{ flex: 1, padding: '1.5rem 1.25rem', display: 'flex', flexDirection: 'column' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.25rem' }}>
                  Upload or use trial CV
                </h1>

                {/* Template buttons */}
                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
                  {Object.entries(TEMPLATES).map(([key, tpl]) => (
                    <button
                      key={key}
                      onClick={() => submitTemplate(key)}
                      style={{
                        flex: 1, padding: '0.68rem 0.4rem',
                        background: 'none',
                        border: '2px solid var(--accent)',
                        color: 'var(--accent)',
                        borderRadius: 999,
                        fontSize: '0.82rem', fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {tpl.label}
                    </button>
                  ))}
                </div>

                {/* Upload box */}
                <div
                  onClick={() => document.getElementById('cv-file-input').click()}
                  style={{
                    flex: 1,
                    border: '2px dashed var(--border)',
                    borderRadius: 16,
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center',
                    gap: '0.6rem', padding: '3rem 1rem',
                    cursor: 'pointer',
                    minHeight: 180,
                  }}
                >
                  <span style={{ fontSize: '2.5rem' }}>☁️</span>
                  <span style={{ fontSize: '1rem', fontWeight: 600 }}>Upload CV</span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--sub)' }}>PDF only</span>
                </div>
                <input
                  id="cv-file-input"
                  type="file"
                  accept=".pdf"
                  style={{ display: 'none' }}
                  onChange={e => { if (e.target.files[0]) submitFile(e.target.files[0]) }}
                />

                {error && (
                  <div style={{
                    marginTop: '1rem',
                    background: '#fef2f2', border: '1px solid #fecaca',
                    borderRadius: 10, padding: '0.75rem 1rem',
                    color: '#dc2626', fontSize: '0.85rem',
                  }}>
                    {error}
                  </div>
                )}
              </div>
            )}

            {/* ── PAGE 4 — Loading ───────────────────────────────────────── */}
            {page === 4 && (
              <div style={{
                flex: 1, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: '2rem',
              }}>
                <img
                  src="/logo.png"
                  alt="AI GMI"
                  style={{ height: '80px', width: 'auto', animation: 'pulse 2s ease-in-out infinite' }}
                />
                <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>Generating...</h1>
                <img
                  src="https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif"
                  alt="loading"
                  style={{ width: 200, borderRadius: 16 }}
                />
              </div>
            )}

            {/* ── PAGE 5 — Results ───────────────────────────────────────── */}
            {page === 5 && result && (
              <div style={{
                flex: 1, padding: '1.5rem 1.25rem 2rem',
                display: 'flex', flexDirection: 'column', gap: '1rem',
                overflowY: 'auto',
              }}>

                {/* Score card */}
                <div style={{
                  background: 'var(--card)',
                  border: '1px solid var(--border)',
                  borderRadius: 16, padding: '1.25rem',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem',
                }}>
                  <Gauge score={score} />
                  <div style={{ fontSize: '1.35rem', fontWeight: 700, textAlign: 'center' }}>
                    {score}/100 - {scoreMessage(score)}
                  </div>
                </div>

                {/* Roast card */}
                <div style={{ background: 'var(--roast-bg)', borderRadius: 16, padding: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.7rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>THE ROAST 🔥</span>
                    <span style={{
                      background: '#f59e0b', color: '#fff',
                      fontSize: '0.75rem', fontWeight: 700,
                      borderRadius: 999, padding: '0.22rem 0.6rem',
                    }}>
                      ⭐ {score}/100
                    </span>
                  </div>
                  <p style={{ fontStyle: 'italic', fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text)' }}>
                    {result.roast}
                  </p>
                </div>

                {/* Feedback card */}
                <div style={{ background: 'var(--feedback-bg)', borderRadius: 16, padding: '1.25rem' }}>
                  <div style={{
                    fontSize: '0.68rem', fontWeight: 700,
                    letterSpacing: '0.1em', textTransform: 'uppercase',
                    color: 'var(--accent)', marginBottom: '0.55rem',
                  }}>
                    Constructive Feedback
                  </div>
                  <ul style={{ paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', listStyleType: 'disc' }}>
                    {Array.isArray(result.priority_fixes)
                      ? result.priority_fixes.map((fix, i) => (
                          <li key={i} style={{ fontSize: '0.9rem', lineHeight: 1.5, color: 'var(--text)' }}>
                            {fix}
                          </li>
                        ))
                      : <li>{result.priority_fixes}</li>
                    }
                  </ul>
                </div>

                {/* Audio controls */}
                {audioTs && (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.6rem' }}>
                      {[['▶', () => audioRef.current?.play().catch(() => {})],
                        ['⏸', () => audioRef.current?.pause()]].map(([icon, action]) => (
                        <button
                          key={icon}
                          onClick={action}
                          style={{
                            width: 44, height: 44, borderRadius: '50%',
                            border: '2px solid var(--accent)',
                            background: 'none', cursor: 'pointer',
                            fontSize: '1rem', color: 'var(--accent)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}
                        >
                          {icon}
                        </button>
                      ))}
                    </div>
                    <audio
                      ref={audioRef}
                      src={`${API}/static/roast.mp3?t=${audioTs}`}
                      autoPlay
                    />
                  </>
                )}

              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
