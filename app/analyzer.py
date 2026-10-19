"""Glue: runs the whole pipeline on plain text. No FastAPI, no files — easy to test."""
from datetime import date

from app import matcher, semantic
from app.roadmap import build_roadmap
from app.skill_extractor import (extract_job_requirements, extract_requirement_lines,
                                 extract_resume_skills, find_skills_in_line)

LIMITATIONS = [
    "Named skills are found with a curated dictionary; skills outside it are not detected.",
    "A skill not found in the resume is 'not evidenced', not proof that you lack it.",
    "Semantic matching uses a pre-trained embedding model; similarity is not proof of skill.",
    "The score is an internal heuristic, not an ATS score or a hiring probability.",
    "Scanned/image-only PDFs are not supported (no OCR).",
]


def run_analysis(
    resume_text: str,
    job_text: str,
    hours_per_day: float | None = None,
    deadline: date | None = None,
) -> dict:
    # 1. Named skills (dictionary + regex): exact and explainable.
    resume_skills = extract_resume_skills(resume_text)
    job_skills, constraints, clear_sections = extract_job_requirements(job_text)
    rows = matcher.compare_skills(resume_skills, job_skills)
    req_cov = matcher.coverage(rows, "required")
    pref_cov = matcher.coverage(rows, "preferred")

    # 2. Semantic search (embeddings): requirement sentence -> closest resume line.
    requirement_lines = semantic.split_lines("\n".join(extract_requirement_lines(job_text)))
    requirement_matches = semantic.match_requirements(requirement_lines, resume_text)
    sem = semantic.semantic_score(requirement_matches)

    # If every named skill in a requirement was matched exactly, trust that over a weak
    # embedding score (e.g. "Version control with Git" vs a comma-separated skills line).
    matched_skills = {r["skill"] for r in rows if r["status"] == "matched"}
    for m in requirement_matches:
        named = {s for s, *_ in find_skills_in_line(m["requirement"])}
        m["skills_found"] = sorted(named & matched_skills)
        if named and named <= matched_skills:
            m["match"] = "strong"

    # 3. Ordered learning plan for what's missing.
    missing = [r for r in rows if r["status"] == "missing"]
    # "MySQL or PostgreSQL" with neither on the resume: learn one, not both.
    to_learn, planned = [], set()
    for r in missing:
        if planned & set(r["alternatives"]):
            continue
        to_learn.append(r)
        planned.add(r["skill"])
    roadmap = build_roadmap(to_learn, set(resume_skills), hours_per_day, deadline)
    alternatives = {r["skill"]: r["alternatives"] for r in to_learn if r["alternatives"]}
    for step in roadmap["steps"]:
        if step["skill"] in alternatives:
            step["reason"] += f" (or learn {' / '.join(alternatives[step['skill']])} instead)"

    recommendations = []
    listed_only = [r["skill"] for r in rows if r["status"] == "matched" and r["evidence"] == "listed only"]
    if listed_only:
        recommendations.append(
            "Add project or experience bullets that show you used: " + ", ".join(listed_only) + "."
        )
    weak = [m["requirement"] for m in requirement_matches if m["match"] == "not shown"]
    if weak:
        recommendations.append(
            f"{len(weak)} job requirement(s) have no similar line in your resume; "
            "see 'Requirement match' below."
        )
    if any(r["status"] == "uncertain" for r in rows):
        recommendations.append("Check the 'uncertain' skills and write them explicitly if you have them.")
    if not clear_sections:
        recommendations.append(
            "The job description has no clear Required/Preferred headings, so all skills were "
            "treated as required (inferred)."
        )
    if constraints:
        recommendations.append("Review the eligibility lines manually; they are not scored.")

    return {
        "score": {
            "overall": matcher.overall_score(req_cov, sem),
            "required_coverage": None if req_cov is None else round(req_cov * 100, 1),
            "preferred_coverage": None if pref_cov is None else round(pref_cov * 100, 1),
            "semantic_match": round(sem * 100, 1),
            "formula": (f"{int(matcher.SKILL_WEIGHT * 100)}% required-skill coverage + "
                        f"{int(matcher.SEMANTIC_WEIGHT * 100)}% semantic match "
                        f"(uncertain skills count {matcher.UNCERTAIN_CREDIT})"),
            "disclaimer": "Internal heuristic only - not an ATS score or a hiring probability.",
        },
        "resume_skills": [
            {"skill": m.skill, "category": m.category, "sections": sorted(m.sections),
             "excerpt": m.excerpt, "uncertain": m.uncertain}
            for m in sorted(resume_skills.values(), key=lambda m: (m.category, m.skill))
        ],
        "matched": [r for r in rows if r["status"] == "matched"],
        "missing_required": [r for r in missing if r["importance"] == "required"],
        "missing_preferred": [r for r in missing if r["importance"] == "preferred"],
        "uncertain": [r for r in rows if r["status"] == "uncertain"],
        "requirement_matches": requirement_matches,
        "eligibility": constraints,
        "jd_has_clear_sections": clear_sections,
        "roadmap": roadmap,
        "recommendations": recommendations,
        "limitations": LIMITATIONS,
    }
