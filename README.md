---
title: CoTeach
emoji: 🍎
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# CoTeach

CoTeach is a minimal AI professional growth coach for teachers in Kazakhstan — a structured alternative to CritiSabaq. A teacher pastes a lesson plan, presentation text, transcript, or student work (or uploads a `.txt`, `.docx`, or `.pdf`). CoTeach returns card-based feedback in Kazakh, Russian, or English: a summary, rubric scores with evidence, strengths, prioritized improvements, micro-actions for the next lesson, a two-week development plan, and a progress note that remembers earlier analyses.

## Features

- Single-page app (FastAPI + HTML/JS, no build step) with a full UI in `kk` / `ru` / `en`
- SQLite storage by default; PostgreSQL (e.g. free Neon or Supabase) when `DATABASE_URL` is set
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
- **Growth Program** (Программа роста / Даму бағдарламасы): a 2–8 week coaching cycle
  - the teacher picks 1–2 focus criteria (or lets the coach choose them from the latest analysis) and an optional personal goal
  - the coach writes a week-by-week plan: focus, one concrete practice task, and what evidence to submit
  - every week the teacher submits materials (text or several `.txt` / `.docx` / `.pdf` / `.pptx` files) plus a short reflection
  - the coach checks whether the week's task was done, scores the full rubric, gives strengths, 1–2 improvements, micro-actions, and an adjusted task for next week, using the whole program history
  - the dashboard shows a timeline (done / current / upcoming), the current task, focus-score chart, and per-week feedback
  - after the last week there is a printable final report: growth summary, before/after on the focus criteria (numbers come from the stored scores), achievements, and recommendations

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
| `DATABASE_URL` | Optional `postgresql://...` URL. When set, CoTeach uses PostgreSQL (psycopg 3) instead of SQLite and creates its tables on startup. Use this for persistent data on Render's free plan, for example with Neon or Supabase. |
| `DB_PATH` | Optional SQLite file path. Defaults to `data/teachercoach.db` locally, or `/tmp/coteach.db` (or `/data/coteach.db` if writable) in Docker / Spaces |

If the key for the chosen provider is missing, CoTeach runs in **demo mode** and returns deterministic sample feedback. The UI shows a demo-mode banner.

## File layout

```
teachercoach/
  app/
    main.py          # FastAPI routes and static serving
    coach.py         # Gemini/OpenAI client, prompts, mock mode, JSON validation
    program.py       # Growth Program: plan, weekly review, final report (+ mock mode)
    db.py            # SQLite / PostgreSQL helpers
    schemas.py       # Pydantic feedback, program, and report schemas
    extract.py       # .txt / .docx / .pdf / .pptx text extraction
  static/            # Single-page UI (index.html, styles.css, app.js, program.js)
  brand/             # Logo and hero images (served at /brand/...)
  samples/           # Sample lesson plans (Russian and Kazakh)
  screenshots/       # Captured UI screenshots
  data/              # SQLite database created at runtime
  requirements.txt
  Dockerfile
  .dockerignore
  deploy_hf.py
  .env.example
  SETUP.md
  README.md
```

Sample materials:

- `samples/lesson_plan_ru.txt` — Grade 6 mathematics (percentages), Russian
- `samples/lesson_plan_kk.txt` — Grade 6 Kazakh language (synonyms), Kazakh

## API (for checks and integrations)

- `GET /api/config` — `{ demo_mode, provider, model, db }`
- `POST /api/analyze` — JSON or `multipart/form-data` with `teacher_name`, `language` (`kk`/`ru`/`en`), `subject`, `grade`, `material_type`, `text`, optional `file`
- `GET /api/progress?teacher_name=...` — history and rubric scores
- `GET /api/analyses/{id}` — one saved analysis
- `GET /api/health`
- `GET /api/rubric` — rubric criteria ids and labels in all languages
- `POST /api/programs` — JSON `{teacher_name, language, subject, grade, weeks (2-8), focus_criteria ([] = coach chooses), goal}`
- `GET /api/programs?teacher_name=...` — the teacher's programs
- `GET /api/programs/{id}` — program with timeline, current task, chart data, submissions, and report
- `POST /api/programs/{id}/weeks` — `multipart/form-data` with `text`, `reflection`, and any number of `files`
- `POST /api/programs/{id}/report` — (re)generate the final report once every week is submitted

## Deploy

### Hugging Face Spaces (recommended for a public demo link)

This repo is ready to run as a Docker Space (`sdk: docker`, port `7860`).

1. Create a public Space named `coteach` (Docker SDK) at https://huggingface.co/new-space
2. In the Space settings, add a **secret** `GEMINI_API_KEY` and a **variable** `LLM_MODEL=gemini-3.5-flash`
3. Push this folder to the Space, or run:

```bash
pip install huggingface_hub
export HF_TOKEN=...          # a token with write access, from https://huggingface.co/settings/tokens
export GEMINI_API_KEY=...    # same key used locally
python deploy_hf.py
```

The script prints the Space URL (`https://huggingface.co/spaces/<user>/coteach`) and the direct app URL (`https://<user>-coteach.hf.space`). SQLite is stored at `/tmp/coteach.db` inside the container (`DB_PATH`); history does not persist across rebuilds unless you attach persistent storage at `/data` and set `DB_PATH=/data/coteach.db`.

### Render or Railway

Set the same environment variables on [Render](https://render.com) or [Railway](https://railway.app). Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

A `Procfile` is included for platforms that use one. Persist the `data/` directory if you want history to survive restarts.

## What you need to provide

For real (non-demo) feedback, a **Gemini API key** as `GEMINI_API_KEY` (see [SETUP.md](SETUP.md)). An OpenAI key is optional and used only if you switch `LLM_PROVIDER=openai`.
