---
title: SkillBridge AI
emoji: 🧭
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
short_description: Find missing skills for a job and get an ordered learning plan
---

# SkillBridge AI: Resume-to-Job Skill Gap Analyzer

Upload your resume and a job description (PDF or .txt). SkillBridge AI shows which skills the job needs that your resume doesn't, and gives a short learning plan that puts prerequisites first.

## Features
- **Resume and job description input:** text-based PDF or .txt, up to 5 MB each. The job description can also be pasted.
- **Skill gap:** required vs nice-to-have skills that are missing, skills you have (with the resume line as evidence), and "uncertain" matches to double-check.
- **Accepted alternatives:** for "FastAPI **or** Django", having Django is enough.
- **Semantic requirement match:** each job requirement is paired with the most similar line in your resume, using a sentence-embedding model. This works even when the two share no keywords.
- **Learning plan:** missing skills in order, with prerequisites first (DFS topological sort). Each step has topics, a practice task, estimated hours, and an official docs link. The plan fits your hours per day and deadline.
- **Explainable score:** `70% required-skill coverage + 30% semantic match`. It is a heuristic, not an ATS score or a hiring probability.

## Tech stack
Python · FastAPI · Pydantic · PyMuPDF · Sentence-Transformers (`all-MiniLM-L6-v2`, PyTorch) · HTML/CSS/JavaScript · pytest · Docker · Hugging Face Spaces

## How it works
```text
Browser (frontend/)  --FormData-->  POST /analyze  (app/main.py)
  file_reader.py      PDF/TXT -> clean text (magic-byte check, 5 MB limit, no files saved)
  skill_extractor.py  skill dictionary + whole-word regex; Required / Nice-to-have sections;
                      "X or Y" alternatives; eligibility lines
  matcher.py          matched / missing / uncertain + required & preferred coverage
  semantic.py         embeddings: each JD requirement -> closest resume line (cosine similarity)
  roadmap.py          prerequisite-first ordering, hours, deadline check
  analyzer.py         runs the pipeline (no web code, so it is easy to test)
```

**Why a hybrid?** I tested pure embedding matching on skill names. It rated *MySQL vs PostgreSQL* (0.55) as more similar than *ML vs Machine Learning* (0.37), so it can't reliably decide which skills you have. The dictionary decides named skills exactly. Embeddings handle what keywords can't: requirement sentences like "experience building backend services".

## Run locally (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. API docs are at http://127.0.0.1:8000/docs. The first run downloads the model (~90 MB).

Try it with the fictional files in `samples/` (5 resumes and 5 job descriptions, mixed PDF and .txt). `python try_samples.py` scores every resume against every job.

## Tests
```powershell
python -m pytest -q
```
45 tests cover file reading, skill extraction (aliases, no substring false positives, required vs preferred, "or" alternatives that let you learn just one), scoring, semantic search, roadmap ordering and deadlines, and API errors.

On the 5 sample resume/job pairs, every resume scored highest on the job it was written for. That is a sanity check on 5 hand-made pairs, not a measured accuracy figure.

## Limitations
- Only skills in the curated dictionary are detected as named skills.
- A skill not found is "not evidenced", not proof that you lack it.
- Embedding similarity is not proof of skill, and scores for true and false matches can overlap.
- Scanned (image-only) PDFs aren't supported (no OCR).

## Future enhancements
- Suggest resume changes (rewritten bullets, missing keywords) to improve fit for a specific opening.
- LLM-assisted skill extraction, kept behind the same interface with the dictionary as a fallback.
- Evaluation on a larger hand-labelled set to tune the weights and thresholds.
- Saved profiles and progress tracking.
