"""Semantic search with a pre-trained sentence-embedding model (deep learning, no training).

For every requirement line in the job description we find the most similar line in the
resume. This catches meaning that shares no keywords, e.g.
"experience building backend services"  ->  "Built a REST API with Node.js and Express".

We do NOT use embeddings to decide which named skills you have: in testing, the model
rated "MySQL" vs "PostgreSQL" as more similar than "ML" vs "Machine Learning", so the
dictionary in skill_extractor.py stays in charge of skill names.

The model runs on ONNX Runtime (via fastembed) instead of PyTorch: same model and same
similarity scores, but ~250 MB of RAM instead of ~550 MB, so it fits free 512 MB hosts.
"""
import os
import re
from functools import lru_cache

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
STRONG_MATCH = 0.50   # >= this: requirement clearly shown in the resume
WEAK_MATCH = 0.30     # <  this: requirement not shown in the resume
MIN_WORDS = 3         # ignore headings and fragments shorter than this

_BULLET = re.compile(r"^\s*[-*>\N{BULLET}\N{BLACK CIRCLE}\N{MIDDLE DOT}]\s*|^\s*\d+[.)]\s+")


@lru_cache(maxsize=1)
def get_model():
    """Load the model once per process (about 90 MB, a few seconds)."""
    from fastembed import TextEmbedding  # heavy import, done lazily
    # MODEL_CACHE_DIR lets the Docker image ship the model instead of downloading it at startup.
    return TextEmbedding(MODEL_NAME, cache_dir=os.environ.get("MODEL_CACHE_DIR"))


def embed(lines: list[str]) -> np.ndarray:
    """One unit-length vector per line, so a dot product equals cosine similarity."""
    vectors = np.array(list(get_model().embed(lines)))
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def split_lines(text: str) -> list[str]:
    """Meaningful lines only: strip bullets, re-join wrapped sentences, drop short fragments."""
    merged: list[str] = []
    for raw in text.splitlines():
        line = _BULLET.sub("", raw).strip()
        if not line:
            continue
        if merged and line[0].islower():  # PDFs wrap long sentences onto a new line
            merged[-1] += " " + line
        else:
            merged.append(line)
    return [line for line in merged if len(line.split()) >= MIN_WORDS]


def label(score: float) -> str:
    if score >= STRONG_MATCH:
        return "strong"
    if score >= WEAK_MATCH:
        return "partial"
    return "not shown"


def match_requirements(requirement_lines: list[str], resume_text: str) -> list[dict]:
    """For each requirement, the closest resume line and its cosine similarity."""
    resume_lines = split_lines(resume_text)
    if not requirement_lines or not resume_lines:
        return []
    scores = embed(requirement_lines) @ embed(resume_lines).T  # matrix: requirements x resume lines

    results = []
    for i, requirement in enumerate(requirement_lines):
        j = int(scores[i].argmax())
        score = float(scores[i][j])
        results.append({
            "requirement": requirement,
            "closest_resume_line": resume_lines[j],
            "similarity": round(score, 2),
            "match": label(score),
        })
    return results


def semantic_score(matches: list[dict]) -> float:
    """Average best-match similarity over all requirements, clipped to [0, 1]."""
    if not matches:
        return 0.0
    return max(0.0, min(1.0, sum(m["similarity"] for m in matches) / len(matches)))
