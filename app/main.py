"""FastAPI app: HTTP layer only. All analysis logic lives in other modules."""
import logging
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.analyzer import run_analysis
from app.file_reader import MAX_FILE_SIZE_BYTES, DocumentError, normalize_text, read_document
from app.schemas import AnalysisResponse
from app.semantic import get_model

logger = logging.getLogger("skillbridge")
MAX_TEXT_CHARS = 20_000
MIN_RESUME_CHARS = 10  # "Python, SQL" is enough when only skills are typed
MIN_JD_CHARS = 50


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model()  # load the embedding model once at startup, not on the first request
    yield


app = FastAPI(title="SkillBridge AI", version="1.0.0", lifespan=lifespan,
              description="Find the skills a job needs that your resume doesn't show, "
                          "and get an ordered learning plan.")


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    # Log the type only, never resume contents. Never leak stack traces to users.
    logger.error("Unhandled error: %s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/health")
def health():
    return {"status": "ok"}


async def read_upload(upload: UploadFile) -> str:
    data = await upload.read(MAX_FILE_SIZE_BYTES + 1)  # one extra byte detects oversize
    await upload.close()
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(413, f"{upload.filename} is larger than the 5 MB limit.")
    try:
        return read_document(data, upload.filename or "file")
    except DocumentError as exc:
        raise HTTPException(400, str(exc))


async def combine(upload: UploadFile | None, typed: str | None, typed_heading: str = "") -> str:
    """Text from the uploaded file and/or the text box. Either one alone is enough."""
    parts = []
    if upload is not None and upload.filename:
        parts.append(await read_upload(upload))
    if typed and typed.strip():
        # An optional heading line tells the section detector what the typed text is.
        parts.append(f"{typed_heading}\n{normalize_text(typed)}".strip())
    return "\n\n".join(parts)


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    resume: UploadFile | None = File(None, description="Resume: text-based PDF or .txt, max 5 MB"),
    resume_text: str | None = Form(None, max_length=MAX_TEXT_CHARS,
                                   description="...and/or technical skills typed as text"),
    job_file: UploadFile | None = File(None, description="Job description as PDF or .txt"),
    job_text: str | None = Form(None, max_length=MAX_TEXT_CHARS, description="...and/or pasted text"),
    hours_per_day: float | None = Form(None, gt=0, le=16),
    deadline: date | None = Form(None),
):
    if deadline is not None and deadline <= date.today():
        raise HTTPException(422, "Deadline must be a future date.")

    candidate = await combine(resume, resume_text, "Technical Skills")
    if len(candidate.strip()) < MIN_RESUME_CHARS:
        raise HTTPException(422, "Upload your resume or type your technical skills.")
    job_description = await combine(job_file, job_text)
    if len(job_description.strip()) < MIN_JD_CHARS:
        raise HTTPException(422, f"Upload a job description file or paste at least {MIN_JD_CHARS} characters.")

    return run_analysis(candidate, job_description, hours_per_day, deadline)


# Serve the website at "/". Mounted LAST so it doesn't shadow the API routes.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
