"""LLM coaching layer: Gemini (default) or OpenAI, plus deterministic mock mode."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from .schemas import CRITERION_IDS, CRITERION_LABELS, RUBRIC_CRITERIA, Feedback

T = TypeVar("T")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MAX_MATERIAL_CHARS = 24000
# gemini-2.5-flash is retired for new AI Studio keys (404). gemini-3.5-flash
# is a current Flash model that works with the OpenAI-compatible endpoint.
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"

LANGUAGE_NAMES = {"kk": "Kazakh", "ru": "Russian", "en": "English"}


def provider_name() -> str:
    return (os.getenv("LLM_PROVIDER") or "gemini").strip().lower()


def api_key() -> str:
    if provider_name() == "openai":
        return (os.getenv("OPENAI_API_KEY") or "").strip()
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def is_demo_mode() -> bool:
    return not bool(api_key())


def model_name() -> str:
    explicit = (os.getenv("LLM_MODEL") or "").strip()
    if explicit:
        return explicit
    if provider_name() == "openai":
        return (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    return DEFAULT_GEMINI_MODEL


def config_public() -> dict[str, Any]:
    return {
        "demo_mode": is_demo_mode(),
        "provider": provider_name(),
        "model": model_name(),
    }


def get_client() -> OpenAI:
    key = api_key()
    if provider_name() == "openai":
        return OpenAI(api_key=key, timeout=120.0)
    return OpenAI(api_key=key, base_url=GEMINI_BASE_URL, timeout=120.0)


def analyze_material(
    *,
    teacher_name: str,
    language: str,
    subject: str,
    grade: str,
    material_type: str,
    text: str,
    history: list[dict[str, Any]],
) -> Feedback:
    if is_demo_mode():
        return localize_labels(_mock_feedback(language, text, history), language)

    messages = _build_messages(
        teacher_name=teacher_name,
        language=language,
        subject=subject,
        grade=grade,
        material_type=material_type,
        text=text,
        history=history,
    )
    feedback = complete_validated(messages, _parse_feedback)
    return localize_labels(feedback, language)


def complete_validated(messages: list[dict[str, str]], parse: Callable[[str], T]) -> T:
    """Call the LLM in JSON mode, parse/validate, and ask once for a repair on failure."""
    raw = _complete(messages, use_json_format=True)
    try:
        return parse(raw)
    except (ValueError, ValidationError) as first_error:
        repair = messages + [
            {"role": "assistant", "content": raw[:8000]},
            {
                "role": "user",
                "content": (
                    "Your previous reply was not valid JSON matching the required schema. "
                    f"Error: {str(first_error)[:1500]}\n"
                    "Return ONLY a single valid JSON object. No markdown, no commentary."
                ),
            },
        ]
        raw = _complete(repair, use_json_format=True)
        return parse(raw)


def localize_labels(feedback, language: str):
    lang = language if language in {"kk", "ru", "en"} else "en"
    for item in feedback.rubric:
        item.label = CRITERION_LABELS[item.id][lang]
    return feedback


def _complete(messages: list[dict[str, str]], use_json_format: bool) -> str:
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": model_name(),
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    if use_json_format:
        kwargs["response_format"] = {"type": "json_object"}
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.chat.completions.create(**kwargs)
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            if use_json_format and _is_format_unsupported(exc):
                return _complete(messages, use_json_format=False)
            if _is_transient(exc) and attempt < 3:
                import time as _time
                _time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(_friendly_llm_error(exc)) from exc
    if last_error is not None:
        raise RuntimeError(_friendly_llm_error(last_error)) from last_error
    choice = response.choices[0].message
    content = choice.content
    if not content and getattr(choice, "refusal", None):
        raise ValueError(f"Model refused to respond: {choice.refusal}")
    if not content:
        raise ValueError("Model returned an empty response.")
    return content


def _friendly_llm_error(exc: Exception) -> str:
    """Surface a safe, key-free message from a provider error."""
    status = getattr(exc, "status_code", None)
    body = ""
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            body = response.text or ""
        except Exception:
            body = ""
    message = body or str(exc)
    if _is_html_error(exc):
        message = "The language model service returned a temporary error page. Please try again in a minute."
    # Never include credentials if a library leaked them.
    import re as _re
    message = _re.sub(r"AIza[0-9A-Za-z_-]{8,}", "[REDACTED]", message)
    message = _re.sub(r"(key=)[^&\s]+", r"\1[REDACTED]", message, flags=_re.I)
    # Prefer the provider's JSON error message when present.
    try:
        try:
            parsed = json.loads(message)
        except json.JSONDecodeError:
            parsed = json.loads(message[message.find("{"):] if "{" in message else message)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if isinstance(parsed, dict):
            err = parsed.get("error") or parsed
            if isinstance(err, dict) and err.get("message"):
                message = str(err["message"])
    except Exception:
        pass
    if _is_daily_quota(exc):
        message = (
            "The free Gemini API daily request limit has been reached. "
            "It resets automatically within 24 hours. " + message.split("\n")[0]
        )
    prefix = f"HTTP {status}: " if status else ""
    return (prefix + message).strip()[:800]


def _is_daily_quota(exc: Exception) -> bool:
    text = (_response_text(exc) or str(exc)).lower()
    return getattr(exc, "status_code", None) == 429 and ("per day" in text or "perday" in text)


def _response_text(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    try:
        return (response.text or "") if response is not None else ""
    except Exception:
        return ""


def _is_html_error(exc: Exception) -> bool:
    body = _response_text(exc).lstrip().lower()
    return body.startswith("<!doctype html") or body.startswith("<html")


def _is_transient(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if _is_daily_quota(exc):
        return False  # retrying cannot help until the quota resets
    if status in {429, 500, 502, 503, 504}:
        return True
    # Google's edge occasionally answers with an HTML 403 page; a retry succeeds.
    if status == 403 and _is_html_error(exc):
        return True
    msg = str(exc).lower()
    return "high demand" in msg or "unavailable" in msg or "try again later" in msg or "429" in msg


def _is_format_unsupported(exc: Exception) -> bool:
    msg = str(exc).lower()
    tokens = (
        "response_format",
        "json_object",
        "unknown field",
        "not supported",
        "unsupported",
        "invalid argument",
        "invalid_request",
    )
    auth_tokens = ("api key", "unauthorized", "permission", "401", "403", "invalid_api_key")
    if any(token in msg for token in auth_tokens) and "response_format" not in msg:
        return False
    return any(token in msg for token in tokens)


def _parse_feedback(raw: str) -> Feedback:
    payload = extract_json_object(raw)
    data = json.loads(payload)
    if isinstance(data, dict) and "feedback" in data and isinstance(data["feedback"], dict):
        data = data["feedback"]
    return Feedback.model_validate(data)


def extract_json_object(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty model output.")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output.")
    try:
        obj, _end = json.JSONDecoder().raw_decode(text[start:])
        return json.dumps(obj, ensure_ascii=False)
    except json.JSONDecodeError as exc:
        end = text.rfind("}")
        if end <= start:
            raise ValueError("No JSON object found in model output.") from exc
        return text[start : end + 1]


def _build_messages(
    *,
    teacher_name: str,
    language: str,
    subject: str,
    grade: str,
    material_type: str,
    text: str,
    history: list[dict[str, Any]],
) -> list[dict[str, str]]:
    lang_name = LANGUAGE_NAMES.get(language, "English")
    rubric_lines = [
        f"- {c['id']}: {c['en']} / {c['ru']} / {c['kk']}" for c in RUBRIC_CRITERIA
    ]
    material = text.strip()
    if len(material) > MAX_MATERIAL_CHARS:
        material = material[:MAX_MATERIAL_CHARS] + "\n[...truncated...]"

    system = (
        "You are an experienced, supportive instructional coach for school teachers "
        "in Kazakhstan. You give structured, evidence-based feedback aligned loosely "
        "with the updated curriculum content (жаңартылған білім мазмұны) and "
        "criteria-based assessment (критериалды бағалау / критериальное оценивание). "
        "Be specific, kind, and practical. Do not invent evidence — quote or closely "
        "paraphrase the submitted material. "
        f"Write EVERY text field in {lang_name} ({language}) only. "
        "Return ONLY a single JSON object. No markdown fences, no preamble."
    )
    schema = """
{
  "summary": "string, 3-6 sentences",
  "rubric": [
    {"id": "objectives", "label": "string", "score": 1-4, "evidence": "string with a short quote"},
    {"id": "structure_pacing", "label": "string", "score": 1-4, "evidence": "string"},
    {"id": "explanation_practice", "label": "string", "score": 1-4, "evidence": "string"},
    {"id": "differentiation", "label": "string", "score": 1-4, "evidence": "string"},
    {"id": "engagement", "label": "string", "score": 1-4, "evidence": "string"},
    {"id": "language_clarity", "label": "string", "score": 1-4, "evidence": "string"}
  ],
  "strengths": [{"text": "string", "evidence": "optional quote"}],
  "improvements": [{"text": "string", "priority": "high|medium|low", "evidence": "optional quote"}],
  "micro_actions": ["1-2 concrete actions for the NEXT lesson, each one small and observable"],
  "development_plan": {
    "week1": {"focus": "string", "actions": ["string", "string"]},
    "week2": {"focus": "string", "actions": ["string", "string"]}
  },
  "progress_note": "string comparing with previous analyses, or a baseline welcome if this is the first"
}
""".strip()

    user = (
        f"Teacher name: {teacher_name}\n"
        f"Subject: {subject}\n"
        f"Grade: {grade}\n"
        f"Material type: {material_type}\n"
        f"Interface / response language: {lang_name} ({language})\n\n"
        f"Rubric criteria (score each 1-4, include evidence):\n"
        + "\n".join(rubric_lines)
        + "\n\nScore meaning: 1 = not visible / weak, 2 = emerging, "
        "3 = solid / consistent, 4 = strong exemplar.\n\n"
        "Previous coaching memory (most recent last; use this in progress_note "
        "and follow up on earlier micro-actions):\n"
        f"{_format_history(history)}\n\n"
        "Submitted material:\n---\n"
        f"{material}\n---\n\n"
        f"Required JSON schema:\n{schema}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _format_history(history: list[dict[str, Any]]) -> str:
    if not history:
        return (
            "This is the teacher's first analysis. Set a supportive baseline. "
            "In progress_note, welcome the teacher and describe the starting point. "
            "Do not invent prior results."
        )
    # history is most recent first; present chronological for the model.
    blocks: list[str] = []
    for row in reversed(history):
        try:
            result = json.loads(row["result_json"])
        except (KeyError, TypeError, json.JSONDecodeError):
            result = {}
        try:
            scores = json.loads(row["scores_json"]) if isinstance(row.get("scores_json"), str) else row.get("scores_json") or {}
        except json.JSONDecodeError:
            scores = {}
        score_bits = ", ".join(f"{cid} {scores.get(cid, '?')}/4" for cid in CRITERION_IDS)
        actions = result.get("micro_actions") or []
        if isinstance(actions, list):
            action_text = "; ".join(str(a) for a in actions) or "(none recorded)"
        else:
            action_text = str(actions)
        blocks.append(
            f"- {row.get('created_at')} | {row.get('subject')}, grade {row.get('grade')}, "
            f"{row.get('material_type')}. Average {row.get('average_score')}/4. "
            f"Scores: {score_bits}. Prior micro-actions: {action_text}"
        )
    return "\n".join(blocks)


def _snippet(text: str, fallback: str) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if len(ln.strip()) > 30]
    if lines:
        return lines[min(1, len(lines) - 1)][:180]
    compact = " ".join((text or "").split())
    return (compact[:180] if compact else fallback)


def _mock_feedback(language: str, text: str, history: list[dict[str, Any]]) -> Feedback:
    quote = _snippet(text, "—")
    first = not history
    bump = 1 if not first else 0

    def cap(n: int) -> int:
        return min(4, n + bump)

    scores = {
        "objectives": cap(3),
        "structure_pacing": cap(2),
        "explanation_practice": cap(2),
        "differentiation": 2,
        "engagement": cap(3),
        "language_clarity": cap(3),
    }

    packs = {
        "en": {
            "summary": (
                "This is a clearly organised lesson with stated objectives and a recognisable "
                "beginning–middle–end shape. Student thinking is invited, but practice time and "
                "support for different levels are still thinner than the explanation. "
                "The comments below are sample coaching notes (demo mode) to show how CoTeach works."
            ),
            "evidence": {
                "objectives": f"Objectives are written down, e.g.: “{quote}”",
                "structure_pacing": "Stages are listed, but transitions and timing for practice are only partly specified.",
                "explanation_practice": "Teacher explanation still occupies more of the plan than independent or paired student work.",
                "differentiation": "Tasks appear largely the same for all students; stretch and support are mentioned only lightly.",
                "engagement": "There are moments that can involve students (questions, short tasks), but routines could be more varied.",
                "language_clarity": "The wording is generally understandable; dual-language support (Kazakh/Russian) could be more explicit.",
            },
            "strengths": [
                {
                    "text": "Learning goals are visible and give the lesson a clear direction.",
                    "evidence": quote,
                },
                {
                    "text": "The plan has a familiar lesson flow that students can follow.",
                    "evidence": "Beginning, main part and closing/reflection are present.",
                },
            ],
            "improvements": [
                {
                    "text": "Build in a short formative check before moving on, and use the results to adjust the next task.",
                    "priority": "high",
                    "evidence": "Success criteria and mid-lesson checks are not fully operationalised.",
                },
                {
                    "text": "Prepare one support version and one stretch version of the core task for different levels.",
                    "priority": "high",
                    "evidence": "Differentiation is not yet visible as concrete tasks.",
                },
                {
                    "text": "Shift a few minutes from teacher explanation to student practice or talk.",
                    "priority": "medium",
                    "evidence": "The balance of talk vs practice can be tightened.",
                },
            ],
            "micro_actions": [
                "Before the next lesson, write two success-criteria sentences students can self-check in the last 5 minutes.",
                "Prepare one simplified prompt and one extension question for the main task.",
            ],
            "week1_focus": "Make learning intentions and success criteria visible to students",
            "week1_actions": [
                "Post the objective in student-friendly language and read it with the class.",
                "End one lesson with a 3-question exit ticket and sort the responses the same day.",
            ],
            "week2_focus": "Differentiate the core task and rebalance talk/practice",
            "week2_actions": [
                "Offer a support scaffold (word bank, worked example) and a stretch challenge.",
                "Time a 7-minute pair-practice block and keep teacher talk to a short model first.",
            ],
            "progress_first": (
                "This is your first saved analysis, so it is a baseline. We will look especially "
                "at formative checks and differentiation in the next lesson you share."
            ),
            "progress_next": (
                "Compared with your previous analysis, keep the clear objectives and follow through "
                "on the last micro-actions: visible success criteria and a support/stretch pair for "
                "the main task. Demo mode shows a modest upward shift to illustrate progress tracking."
            ),
        },
        "ru": {
            "summary": (
                "Урок выстроен логично: цели обозначены, есть привычная структура «начало — основная часть — завершение». "
                "Учеников уже приглашают к размышлению, но времени на практику и поддержки разных уровней пока меньше, "
                "чем объяснения учителя. Ниже — демонстрационная обратная связь (демо-режим), чтобы показать работу сервиса."
            ),
            "evidence": {
                "objectives": f"Цели зафиксированы, например: «{quote}»",
                "structure_pacing": "Этапы урока названы, но переходы и время на практику прописаны лишь частично.",
                "explanation_practice": "Объяснение учителя занимает больше места, чем самостоятельная или парная работа.",
                "differentiation": "Задания в основном общие для всего класса; поддержка и усложнение обозначены слабо.",
                "engagement": "Есть вопросы и короткие задания, но приёмы вовлечения можно разнообразить.",
                "language_clarity": "Формулировки в целом понятны; двуязычную поддержку (казахский/русский) можно сделать явнее.",
            },
            "strengths": [
                {
                    "text": "Учебные цели видны и задают уроку понятное направление.",
                    "evidence": quote,
                },
                {
                    "text": "Есть узнаваемая структура урока, по которой удобно двигаться классу.",
                    "evidence": "Присутствуют начало, основная часть и завершение/рефлексия.",
                },
            ],
            "improvements": [
                {
                    "text": "Добавьте короткое формирующее оценивание до перехода к следующему этапу и используйте результат для корректировки задания.",
                    "priority": "high",
                    "evidence": "Критерии успеха и промежуточная проверка ещё не стали рабочим инструментом.",
                },
                {
                    "text": "Подготовьте поддерживающий и усложнённый варианты основного задания.",
                    "priority": "high",
                    "evidence": "Дифференциация пока не выражена в конкретных задачах.",
                },
                {
                    "text": "Перенесите несколько минут с объяснения учителя на практику или учебный разговор учеников.",
                    "priority": "medium",
                    "evidence": "Баланс «объяснение / практика» можно усилить в пользу учеников.",
                },
            ],
            "micro_actions": [
                "К следующему уроку напишите два критерия успеха, по которым ученики проверят себя в последние 5 минут.",
                "Подготовьте упрощённую подсказку и один вопрос на углубление к основному заданию.",
            ],
            "week1_focus": "Сделать цели и критерии успеха видимыми для учеников",
            "week1_actions": [
                "Запишите цель простым языком и проговорите её вместе с классом.",
                "Завершите один урок мини-билетом из 3 вопросов и в тот же день разберите ответы.",
            ],
            "week2_focus": "Дифференцировать основное задание и перераспределить время",
            "week2_actions": [
                "Дайте опору (банк слов, образец) и задание-вызов.",
                "Засеките 7 минут парной практики после короткого образца учителя.",
            ],
            "progress_first": (
                "Это ваш первый сохранённый разбор — отправная точка. В следующем материале "
                "особое внимание уделим формирующему оцениванию и дифференциации."
            ),
            "progress_next": (
                "По сравнению с предыдущим разбором сохраните ясные цели и закройте прошлые микродействия: "
                "видимые критерии успеха и пара «поддержка / усложнение» к основному заданию. "
                "В демо-режиме оценки немного повышены, чтобы показать отслеживание прогресса."
            ),
        },
        "kk": {
            "summary": (
                "Сабақ қисынды құрылған: мақсаттар көрсетілген, «басталуы — негізгі бөлім — қорытынды» құрылымы бар. "
                "Оқушыларды ойлауға шақыру бар, бірақ практика мен деңгейлік қолдауға бөлінген уақыт әзірге мұғалім "
                "түсіндірмесінен аз. Төменде сервисті көрсету үшін демо-режимдегі үлгілік кері байланыс берілген."
            ),
            "evidence": {
                "objectives": f"Мақсаттар жазылған, мысалы: «{quote}»",
                "structure_pacing": "Кезеңдер аталады, бірақ өткелдер мен практика уақыты толық нақтыланбаған.",
                "explanation_practice": "Мұғалімнің түсіндіруі өздік не жұптық жұмыстан көбірек орын алады.",
                "differentiation": "Тапсырмалар негізінен бүкіл сыныпқа ортақ; қолдау мен күрделендіру әлсіз көрсетілген.",
                "engagement": "Сұрақтар мен қысқа тапсырмалар бар, бірақ тартқыштық тәсілдерін әртараптандыруға болады.",
                "language_clarity": "Тұжырымдар жалпы түсінікті; қазақ/орыс тілдеріндегі қолдауды айқынырақ етуге болады.",
            },
            "strengths": [
                {
                    "text": "Оқу мақсаттары көрінеді және сабаққа айқын бағыт береді.",
                    "evidence": quote,
                },
                {
                    "text": "Сыныпқа ыңғайлы, таныс сабақ құрылымы бар.",
                    "evidence": "Басталуы, негізгі бөлім және қорытынды/рефлексия бар.",
                },
            ],
            "improvements": [
                {
                    "text": "Келесі кезеңге өтпес бұрын қысқа қалыптастырушы бағалау енгізіп, нәтижені тапсырманы түзетуге пайдаланыңыз.",
                    "priority": "high",
                    "evidence": "Табыс критерийлері мен аралық тексеру әлі толық жұмыс құралы емес.",
                },
                {
                    "text": "Негізгі тапсырманың қолдау және күрделендірілген нұсқасын дайындаңыз.",
                    "priority": "high",
                    "evidence": "Деңгейлеп оқыту нақты тапсырмалар түрінде әлі көрінбейді.",
                },
                {
                    "text": "Мұғалім түсіндірмесінің бірнеше минутын оқушы практикасына немесе оқу әңгімесіне беріңіз.",
                    "priority": "medium",
                    "evidence": "«Түсіндіру / практика» теңгерімін оқушы пайдасына күшейтуге болады.",
                },
            ],
            "micro_actions": [
                "Келесі сабаққа дейін оқушылар соңғы 5 минутта өзін тексеретін екі табыс критерийін жазыңыз.",
                "Негізгі тапсырмаға жеңілдетілген тірек және бір тереңдететін сұрақ дайындаңыз.",
            ],
            "week1_focus": "Оқу мақсаты мен табыс критерийлерін оқушыға көрінетін ету",
            "week1_actions": [
                "Мақсатты қарапайым тілмен жазып, сыныппен бірге оқыңыз.",
                "Бір сабақты 3 сұрақтық шығу билетімен аяқтап, жауаптарды сол күні іріктеңіз.",
            ],
            "week2_focus": "Негізгі тапсырманы деңгейлеу және уақытты қайта бөлу",
            "week2_actions": [
                "Тірек (сөз банкі, үлгі) және күрделі тапсырма ұсыныңыз.",
                "Қысқа мұғалім үлгісінен кейін 7 минуттық жұптық практиканы өлшеп өткізіңіз.",
            ],
            "progress_first": (
                "Бұл — сіздің алғашқы сақталған талдауыңыз, бастапқы нүкте. Келесі материалда "
                "қалыптастырушы бағалау мен деңгейлеп оқытуға ерекше назар аударамыз."
            ),
            "progress_next": (
                "Алдыңғы талдаумен салыстырғанда айқын мақсаттарды сақтап, өткен микроәрекеттерді жабыңыз: "
                "көрінетін табыс критерийлері және негізгі тапсырмаға «қолдау / күрделендіру» жұбы. "
                "Демо-режимде прогресті көрсету үшін ұпайлар сәл көтерілген."
            ),
        },
    }
    pack = packs.get(language, packs["en"])
    rubric = [
        {
            "id": cid,
            "label": CRITERION_LABELS[cid].get(language, CRITERION_LABELS[cid]["en"]),
            "score": scores[cid],
            "evidence": pack["evidence"][cid],
        }
        for cid in CRITERION_IDS
    ]
    return Feedback.model_validate(
        {
            "summary": pack["summary"],
            "rubric": rubric,
            "strengths": pack["strengths"],
            "improvements": pack["improvements"],
            "micro_actions": pack["micro_actions"],
            "development_plan": {
                "week1": {"focus": pack["week1_focus"], "actions": pack["week1_actions"]},
                "week2": {"focus": pack["week2_focus"], "actions": pack["week2_actions"]},
            },
            "progress_note": pack["progress_first"] if first else pack["progress_next"],
        }
    )
