# CoTeach

CoTeach is a minimal AI professional growth coach for teachers in Kazakhstan — a structured alternative to CritiSabaq. A teacher pastes a lesson plan, presentation text, transcript, or student work (or uploads a `.txt`, `.docx`, or `.pdf`). CoTeach returns card-based feedback in Kazakh, Russian, or English: a summary, rubric scores with evidence, strengths, prioritized improvements, micro-actions for the next lesson, a two-week development plan, and a progress note that remembers earlier analyses.

## Features

- Single-page app (FastAPI + HTML/JS, no build step) with a full UI in `kk` / `ru` / `en`
- SQLite storage for teachers, materials, and analyses
- Rubric (scores 1–4, with evidence), loosely aligned with Kazakhstan’s updated-content and criteria-based assessment approach:
  - clarity of learning objectives
  - structure, pacing and attention management
  - balance of explanation vs student practice / active learning
  - differentiation / support for different levels
  - engagement techniques
  - language clarity (Kazakh and Russian support)
- Memory: the last 3 analyses (scores + prior micro-actions) are sent with the next prompt
- Live mode uses Google Gemini by default (OpenAI-compatible endpoint) or OpenAI
- Mock / demo mode when no API key is set, so the app is fully clickable
- Progress view with a Chart.js score trend

## How to run

```bash
cd teachercoach
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your key — see SETUP.md
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000

On Debian/Ubuntu, a virtual environment is required (`pip` will refuse a system-wide install). If you already have the packages in an environment, `pip install -r requirements.txt` followed by the `uvicorn` command is enough.

## Environment variables

| Variable | Meaning |
| --- | --- |
| `LLM_PROVIDER` | `gemini` (default) or `openai` |
| `LLM_MODEL` | Defaults to `gemini-3.5-flash` (Gemini) or `gpt-4o-mini` (OpenAI). New Google AI Studio keys no longer serve `gemini-2.5-flash`; set `LLM_MODEL` if you want another current Flash model (for example `gemini-3.8-flash`). |
| `GEMINI_API_KEY` | Required for live Gemini requests. Get a key at https://aistudio.google.com/apikey |
| `OPENAI_API_KEY` | Required only if `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | Optional fallback model name when using OpenAI and `LLM_MODEL` is unset |

If the key for the chosen provider is missing, CoTeach runs in **demo mode** and returns deterministic sample feedback. The UI shows a demo-mode banner.

## File layout

```
teachercoach/
  app/
    main.py          # FastAPI routes and static serving
    coach.py         # Gemini/OpenAI client, prompts, mock mode, JSON validation
    db.py            # SQLite helpers
    schemas.py       # Pydantic feedback schema
    extract.py       # .txt / .docx / .pdf text extraction
  static/            # Single-page UI (index.html, styles.css, app.js)
  brand/             # Logo and hero images (served at /brand/...)
  samples/           # Sample lesson plans (Russian and Kazakh)
  screenshots/       # Captured UI screenshots
  data/              # SQLite database created at runtime
  requirements.txt
  .env.example
  SETUP.md
  README.md
```

Sample materials:

- `samples/lesson_plan_ru.txt` — Grade 6 mathematics (percentages), Russian
- `samples/lesson_plan_kk.txt` — Grade 6 Kazakh language (synonyms), Kazakh

## API (for checks and integrations)

- `GET /api/config` — `{ demo_mode, provider, model }`
- `POST /api/analyze` — JSON or `multipart/form-data` with `teacher_name`, `language` (`kk`/`ru`/`en`), `subject`, `grade`, `material_type`, `text`, optional `file`
- `GET /api/progress?teacher_name=...` — history and rubric scores
- `GET /api/analyses/{id}` — one saved analysis
- `GET /api/health`

## Deploy

Set the same environment variables on [Render](https://render.com) or [Railway](https://railway.app). Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

A `Procfile` is included for platforms that use one. Persist the `data/` directory if you want history to survive restarts.

## What you need to provide

For real (non-demo) feedback, a **Gemini API key** as `GEMINI_API_KEY` (see [SETUP.md](SETUP.md)). An OpenAI key is optional and used only if you switch `LLM_PROVIDER=openai`.
