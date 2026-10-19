from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import SAMPLE_JD

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # "with" runs startup, which loads the model once
        yield c


def post(client, resume: bytes, resume_name="resume.pdf", job_text=SAMPLE_JD, job_file=None, **form):
    files = {"resume": (resume_name, resume, "application/octet-stream")}
    if job_file:
        files["job_file"] = job_file
    data = dict(form)
    if job_text is not None:
        data["job_text"] = job_text
    return client.post("/analyze", data=data, files=files)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_pdf_resume_with_pasted_jd(client, resume_pdf):
    deadline = (date.today() + timedelta(days=30)).isoformat()
    res = post(client, resume_pdf, hours_per_day="3", deadline=deadline)
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body["score"]["overall"] <= 100
    assert body["roadmap"]["steps"] and body["roadmap"]["hours_per_day"] == 3
    assert body["requirement_matches"]


def test_sample_files_txt_resume_and_pdf_jd(client):
    resume = (SAMPLES / "resume4_sneha_java_spring.txt").read_bytes()
    jd = ("jd1.pdf", (SAMPLES / "jd1_python_backend_sde.pdf").read_bytes(), "application/pdf")
    res = post(client, resume, resume_name="resume4.txt", job_text=None, job_file=jd)
    assert res.status_code == 200
    missing = {s["skill"] for s in res.json()["missing_required"]}
    assert "Python" in missing


def test_typed_skills_without_a_resume_file(client):
    res = client.post("/analyze", data={"resume_text": "Python, SQL, Git, Docker", "job_text": SAMPLE_JD})
    assert res.status_code == 200
    matched = {s["skill"] for s in res.json()["matched"]}
    assert {"Python", "SQL", "Git", "Docker"} <= matched


def test_typed_skills_are_added_to_the_resume_file(client, resume_pdf):
    without = post(client, resume_pdf).json()
    with_typed = post(client, resume_pdf, resume_text="Docker").json()
    assert "Docker" in {s["skill"] for s in without["missing_required"]}
    assert "Docker" in {s["skill"] for s in with_typed["matched"]}


def test_rejects_non_pdf(client):
    res = post(client, b"just some text, not a pdf at all" * 5, resume_name="resume.pdf")
    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]


def test_rejects_oversized_file(client):
    res = post(client, b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10))
    assert res.status_code == 413


def test_requires_a_job_description(client, resume_pdf):
    assert post(client, resume_pdf, job_text=None).status_code == 422
    assert post(client, resume_pdf, job_text="too short").status_code == 422


def test_rejects_missing_resume(client):
    assert client.post("/analyze", data={"job_text": SAMPLE_JD}).status_code == 422


def test_rejects_past_deadline(client, resume_pdf):
    assert post(client, resume_pdf, deadline="2020-01-01").status_code == 422


def test_rejects_bad_hours(client, resume_pdf):
    assert post(client, resume_pdf, hours_per_day="40").status_code == 422


def test_frontend_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "<h1>SkillBridge" in res.text
