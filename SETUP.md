# CoTeach setup

Follow these steps to run CoTeach with live AI feedback. Until a key is set, the app still works in **demo mode**.

## 1. Get a Gemini API key (default)

1. Open [Google AI Studio — API keys](https://aistudio.google.com/apikey) and sign in with a Google account.
2. Create an API key and copy it.
3. Gemini’s free tier is enough to try the prototype. If you later hit quota limits, check usage in AI Studio.

## 2. Add the key to a `.env` file

From the `teachercoach` folder:

```bash
cp .env.example .env
```

Edit `.env`:

```
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash
GEMINI_API_KEY=your-key-here
```

Do not commit `.env` or share the key.

## 3. Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000, enter your name, choose a language, paste a lesson (or use `samples/lesson_plan_ru.txt` / `samples/lesson_plan_kk.txt`), and submit.

## Optional: OpenAI instead of Gemini

1. Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). OpenAI requires billing credit for live requests.
2. In `.env` set:

```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your-key-here
```

## Deploy (Render / Railway)

A simple deploy works with the same code:

- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Env vars:** set `LLM_PROVIDER`, `LLM_MODEL`, and `GEMINI_API_KEY` (or `OPENAI_API_KEY`) in the service dashboard. A `Procfile` is included.

Persist the `data/` folder (SQLite) if you want teacher progress to survive redeploys. This prototype uses a local file database; it is not a multi-instance production setup.
