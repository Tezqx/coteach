"""FastAPI application: API + single-page frontend."""

from __future__ import annotations

import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

# Load .env before importing db so DB_PATH (if set there) is visible.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from . import coach, db, program as growth
from .extract import ExtractionError, extract_text
from .schemas import RUBRIC_CRITERIA, AnalyzeRequest, ProgramStartRequest

STATIC = ROOT / "static"
BRAND = ROOT / "brand"

db.init_db()

app = FastAPI(
    title="CoTeach",
    description="AI professional growth coach for teachers in Kazakhstan",
    version="0.1.0",
)


def resolve_logo() -> Path | None:
    path = BRAND / "logo.jpg"
    return path if path.is_file() else None


@app.get("/brand/logo")
def brand_logo() -> FileResponse:
    path = resolve_logo()
    if path is None:
        raise HTTPException(status_code=404, detail="Logo not found.")
    return FileResponse(path)


if BRAND.exists():
    app.mount("/brand", StaticFiles(directory=BRAND), name="brand")
if STATIC.exists():
    app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, **coach.config_public()}


@app.get("/api/config")
def config() -> dict:
    return {**coach.config_public(), "db": db.backend_name()}


@app.get("/api/rubric")
def rubric() -> list[dict]:
    return RUBRIC_CRITERIA


@app.post("/api/analyze")
async def analyze(request: Request):
    try:
        payload, filename = await _parse_analyze_request(request)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    text = payload.text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Please paste lesson text or upload a .txt, .docx, .pdf, or .pptx file.",
        )

    teacher = db.get_or_create_teacher(payload.teacher_name)
    history = db.get_recent_analyses(teacher["id"], limit=3)
    try:
        feedback = coach.analyze_material(
            teacher_name=teacher["name"],
            language=payload.language,
            subject=payload.subject,
            grade=payload.grade,
            material_type=payload.material_type,
            text=text,
            history=history,
        )
    except Exception as exc:
        # Do not leak secrets from provider errors.
        message = str(exc)
        lowered = message.lower()
        if "api key" in lowered or "api_key" in lowered:
            message = "The language model rejected the API key. Check GEMINI_API_KEY or OPENAI_API_KEY."
        raise HTTPException(
            status_code=502,
            detail=f"Analysis failed: {message}",
        ) from exc

    material_id = db.insert_material(
        teacher_id=teacher["id"],
        material_type=payload.material_type,
        subject=payload.subject,
        grade=payload.grade,
        language=payload.language,
        text=text,
        filename=filename,
    )
    analysis_id = db.insert_analysis(
        teacher_id=teacher["id"],
        material_id=material_id,
        language=payload.language,
        feedback=feedback,
    )
    return {
        "id": analysis_id,
        "demo_mode": coach.is_demo_mode(),
        "teacher": teacher,
        "material_id": material_id,
        "filename": filename,
        "created_at": db.get_analysis(analysis_id)["created_at"],
        "language": payload.language,
        "subject": payload.subject,
        "grade": payload.grade,
        "material_type": payload.material_type,
        "average_score": feedback.average_score(),
        "scores": feedback.scores_dict(),
        "feedback": feedback.model_dump(),
    }


@app.get("/api/progress")
def progress(teacher_name: str) -> dict:
    name = (teacher_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="teacher_name is required")
    result = db.get_progress(name)
    if result is None:
        raise HTTPException(status_code=404, detail="No teacher found with that name.")
    return result


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: int) -> dict:
    row = db.get_analysis(analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return row


# ---------------------------------------------------------------------------
# Growth Program
# ---------------------------------------------------------------------------


def _llm_error(exc: Exception) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if "api key" in lowered or "api_key" in lowered:
        message = "The language model rejected the API key. Check GEMINI_API_KEY or OPENAI_API_KEY."
    return HTTPException(status_code=502, detail=f"Coach request failed: {message}")


def _program_view(program: dict) -> dict:
    """Program plus a merged week timeline, current task, and chart series."""
    subs = {s["week_number"]: s for s in program.get("submissions") or []}
    done = len(subs)
    completed = program["status"] == "completed" or done >= program["weeks"]
    current_week = None if completed else done + 1
    plan_weeks = program["plan"].get("weeks") or []
    timeline = []
    for n in range(1, program["weeks"] + 1):
        if n in subs:
            task = subs[n]["task"]
            status = "done"
        else:
            task = growth.current_task(program, n) if n == current_week else {
                **(plan_weeks[n - 1] if n <= len(plan_weeks) else {}), "adjusted": False
            }
            status = "current" if n == current_week else "upcoming"
        timeline.append({"week": n, "status": status, "task": task, "submission": subs.get(n)})

    baseline = program.get("baseline") or {}
    labels, series = [], {cid: [] for cid in program["focus_criteria"]}
    averages = []
    if baseline.get("scores"):
        labels.append("baseline")
        for cid in series:
            series[cid].append(baseline["scores"].get(cid))
        averages.append(baseline.get("average_score"))
    for n in sorted(subs):
        labels.append(f"week{n}")
        for cid in series:
            series[cid].append(subs[n]["scores"].get(cid))
        averages.append(subs[n]["average_score"])
    view = dict(program)
    view.update(
        {
            "submitted": done,
            "current_week": current_week,
            "current_task": growth.current_task(program, current_week) if current_week else None,
            "timeline": timeline,
            "chart": {"labels": labels, "series": series, "average": averages},
            "before_after": growth.before_after(program) if done else {},
            "demo_mode": coach.is_demo_mode(),
        }
    )
    return view


@app.post("/api/programs")
async def start_program(request: Request):
    try:
        payload = ProgramStartRequest.model_validate(await request.json())
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    teacher = db.get_or_create_teacher(payload.teacher_name)
    latest = db.get_latest_analysis(teacher["id"])
    focus = list(payload.focus_criteria)
    focus_source = "teacher" if focus else "coach"
    try:
        plan = growth.generate_plan(
            teacher_name=teacher["name"],
            language=payload.language,
            subject=payload.subject,
            grade=payload.grade,
            weeks=payload.weeks,
            focus_criteria=focus,
            goal=payload.goal.strip(),
            latest_analysis=latest,
        )
    except Exception as exc:
        raise _llm_error(exc) from exc

    baseline = None
    if latest:
        baseline = {
            "analysis_id": latest["id"],
            "created_at": latest["created_at"],
            "scores": latest["scores"],
            "average_score": latest["average_score"],
        }
    program_id = db.insert_program(
        teacher_id=teacher["id"],
        language=payload.language,
        subject=payload.subject,
        grade=payload.grade,
        weeks=payload.weeks,
        goal=payload.goal.strip(),
        focus=plan.focus_criteria,
        focus_source=focus_source,
        plan=plan.model_dump(),
        baseline=baseline,
    )
    return _program_view(db.get_program(program_id))


@app.get("/api/programs")
def list_programs(teacher_name: str) -> dict:
    name = (teacher_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="teacher_name is required")
    programs = db.list_programs(name)
    return {"programs": programs or []}


@app.get("/api/programs/{program_id}")
def get_program(program_id: int) -> dict:
    program = db.get_program(program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found.")
    return _program_view(program)


@app.post("/api/programs/{program_id}/weeks")
async def submit_week(program_id: int, request: Request):
    program = db.get_program(program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found.")
    week_number = len(program["submissions"]) + 1
    if program["status"] == "completed" or week_number > program["weeks"]:
        raise HTTPException(status_code=409, detail="This program is already complete.")

    try:
        text, reflection, filenames = await _parse_week_request(request)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Please paste this week's materials or upload a .txt, .docx, .pdf, or .pptx file.",
        )

    task = growth.current_task(program, week_number)
    try:
        feedback = growth.review_week(
            program=program,
            week_number=week_number,
            task=task,
            material=text,
            reflection=reflection,
        )
    except Exception as exc:
        raise _llm_error(exc) from exc

    try:
        db.insert_program_week(
            program_id=program_id,
            week_number=week_number,
            task=task,
            material_text=text,
            filenames=filenames,
            reflection=reflection,
            result=feedback.model_dump(),
            scores=feedback.scores_dict(),
            average_score=feedback.average_score(),
        )
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="This week was already submitted.") from exc
        raise

    report_error = None
    if week_number >= program["weeks"]:
        report_error = _build_report(program_id)
    view = _program_view(db.get_program(program_id))
    view["submitted_week"] = week_number
    view["report_error"] = report_error
    return view


@app.post("/api/programs/{program_id}/report")
def regenerate_report(program_id: int) -> dict:
    program = db.get_program(program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found.")
    if len(program["submissions"]) < program["weeks"]:
        raise HTTPException(status_code=409, detail="Submit every week before the final report.")
    error = _build_report(program_id)
    if error:
        raise HTTPException(status_code=502, detail=f"Coach request failed: {error}")
    return _program_view(db.get_program(program_id))


def _build_report(program_id: int) -> str | None:
    program = db.get_program(program_id)
    try:
        report = growth.final_report(program)
    except Exception as exc:
        traceback.print_exc()
        return _llm_error(exc).detail
    db.complete_program(program_id, report.model_dump())
    return None


async def _parse_week_request(request: Request) -> tuple[str, str, list[str]]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type and "application/x-www-form-urlencoded" not in content_type:
        try:
            body = await request.json()
        except Exception as exc:
            raise ExtractionError("Send this week's materials as form data or JSON.") from exc
        if not isinstance(body, dict):
            raise ExtractionError("Send this week's materials as form data or JSON.")
        return str(body.get("text") or ""), str(body.get("reflection") or "").strip()[:4000], []
    form = await request.form()
    parts = [str(form.get("text") or "").strip()]
    filenames: list[str] = []
    for upload in list(form.getlist("files")) + list(form.getlist("file")):
        if upload is None or not hasattr(upload, "read"):
            continue
        data = await upload.read()
        if not data:
            continue
        name = getattr(upload, "filename", None) or "upload"
        extracted = extract_text(name, data, getattr(upload, "content_type", None))
        parts.append(f"=== {name} ===\n{extracted}")
        filenames.append(name)
    text = "\n\n".join(p for p in parts if p)
    reflection = str(form.get("reflection") or "").strip()[:4000]
    return text, reflection, filenames


@app.exception_handler(Exception)
async def unhandled(_request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error."})


async def _parse_analyze_request(request: Request) -> tuple[AnalyzeRequest, str | None]:
    content_type = request.headers.get("content-type", "")
    filename: str | None = None
    if "multipart/form-data" in content_type:
        form = await request.form()
        pasted = str(form.get("text") or "").strip()
        file_text = ""
        upload = form.get("file")
        if upload is not None and hasattr(upload, "read"):
            data = await upload.read()
            name = getattr(upload, "filename", None) or "upload"
            if data:
                file_text = extract_text(
                    name, data, getattr(upload, "content_type", None)
                )
                filename = name
        text = "\n\n".join(part for part in (pasted, file_text) if part)
        payload = AnalyzeRequest(
            teacher_name=str(form.get("teacher_name") or ""),
            language=str(form.get("language") or "en"),
            subject=str(form.get("subject") or ""),
            grade=str(form.get("grade") or ""),
            material_type=str(form.get("material_type") or "lesson_plan"),
            text=text,
        )
        return payload, filename

    body = await request.json()
    payload = AnalyzeRequest.model_validate(body)
    return payload, None
