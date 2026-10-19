"""Compare resume skills with job requirements and compute the heuristic score.

This module knows nothing about FastAPI, so it can be unit-tested on its own.
"""
from app.skill_extractor import JobSkill, SkillMention

# Configurable heuristic weights (NOT empirically optimised — documented as such).
SKILL_WEIGHT = 0.7
SEMANTIC_WEIGHT = 0.3
UNCERTAIN_CREDIT = 0.5  # an uncertain match counts as half a match

STRONG_SECTIONS = {"projects", "experience"}


def compare_skills(
    resume_skills: dict[str, SkillMention], job_skills: list[JobSkill]
) -> list[dict]:
    """One result row per job skill with a status and a human-readable reason."""
    rows = []
    for js in job_skills:
        mention = resume_skills.get(js.skill)
        # "FastAPI or Django": if you have Django, FastAPI isn't a gap.
        substitute = None
        if mention is None:
            substitute = next((resume_skills[a] for a in js.alternatives
                               if a in resume_skills and not resume_skills[a].uncertain), None)
        row = {
            "skill": js.skill,
            "category": js.category,
            "importance": js.importance,
            "jd_source": js.source,
            "inferred_importance": js.inferred,
            "jd_excerpt": js.excerpt,
            "alternatives": js.alternatives,
            "resume_excerpt": None,
            "evidence": None,
        }
        if js.uncertain:
            row["status"] = "uncertain"
            row["reason"] = "Matched in the job description only through an ambiguous word; please verify."
        elif substitute is not None:
            row["status"] = "matched"
            row["evidence"] = "alternative"
            row["resume_excerpt"] = substitute.excerpt
            row["reason"] = (f"The job accepts any of {', '.join([js.skill, *js.alternatives])}; "
                             f"your resume shows {substitute.skill}.")
        elif mention is None:
            row["status"] = "missing"
            row["reason"] = "Not evidenced in the resume (this does not prove you lack the skill)."
        else:
            row["resume_excerpt"] = mention.excerpt
            row["evidence"] = ("project/experience" if mention.sections & STRONG_SECTIONS
                               else "listed only")
            if mention.uncertain:
                row["status"] = "uncertain"
                row["reason"] = ("Found in the resume only through an ambiguous word "
                                 f"({', '.join(sorted(mention.aliases_found))}); please confirm.")
            else:
                row["status"] = "matched"
                row["reason"] = (
                    "Used in a project or experience entry." if row["evidence"] == "project/experience"
                    else "Listed in the resume, but no project/experience evidence was found."
                )
        rows.append(row)
    return rows


def coverage(rows: list[dict], importance: str) -> float | None:
    """Fraction of (non-uncertain-in-JD) skills of this importance that the resume covers."""
    relevant = [r for r in rows if r["importance"] == importance
                and not (r["status"] == "uncertain" and r["resume_excerpt"] is None)]
    if not relevant:
        return None
    credit = sum(1.0 if r["status"] == "matched" else
                 UNCERTAIN_CREDIT if r["status"] == "uncertain" else 0.0
                 for r in relevant)
    return credit / len(relevant)


def overall_score(required_coverage: float | None, semantic: float) -> float:
    """0-100. 70% required-skill coverage + 30% semantic match (semantic only if no skills found)."""
    if required_coverage is None:
        return round(semantic * 100, 1)
    return round((SKILL_WEIGHT * required_coverage + SEMANTIC_WEIGHT * semantic) * 100, 1)
