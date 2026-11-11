from __future__ import annotations

import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from . import coach, db
from .extract import ExtractionError, extract_text
from .schemas import AnalyzeRequest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
BRAND = ROOT / "brand"

load_dotenv(ROOT / ".env")
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
    return coach.config_public()


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
            detail="Please paste lesson text or upload a .txt, .docx, or .pdf file.",
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
