"""Tests for the analysis engine: skills, alternatives, scoring, semantic search, roadmap."""
from datetime import date

from app import matcher, semantic
from app.analyzer import run_analysis
from app.roadmap import build_roadmap
from app.skill_extractor import extract_job_requirements, extract_resume_skills, find_skills_in_line
from tests.conftest import SAMPLE_JD, SAMPLE_RESUME


def skills_in(text):
    return {s for s, *_ in find_skills_in_line(text)}


# ---------- skill extraction ----------

def test_aliases_map_to_canonical_names():
    assert skills_in("Worked with Postgres and JS") == {"PostgreSQL", "JavaScript"}
    assert "REST APIs" in skills_in("Designed RESTful APIs")


def test_no_substring_false_positives():
    assert "Java" not in skills_in("I write JavaScript")
    assert "SQL" not in skills_in("Used MySQL and PostgreSQL")
    assert "JavaScript" not in skills_in("Built with Node.js")


def test_special_character_skills():
    assert {"C++", "C#"} <= skills_in("Languages: C++, C#")


def test_ambiguous_word_is_uncertain():
    assert extract_resume_skills("Experience\nEvery weekend I Go hiking")["Go"].uncertain
    assert not extract_resume_skills("Skills\nGolang")["Go"].uncertain


def test_duplicates_are_merged():
    assert list(extract_resume_skills("Skills\nPython, python3, PYTHON")) == ["Python"]


def test_resume_sections_recorded():
    found = extract_resume_skills(SAMPLE_RESUME)
    assert "projects" in found["Node.js"].sections
    assert found["Python"].sections == {"skills"}


def test_jd_required_vs_preferred():
    skills, constraints, clear = extract_job_requirements(SAMPLE_JD)
    by_name = {s.skill: s for s in skills}
    assert clear
    assert by_name["Python"].importance == "required" and not by_name["Python"].inferred
    assert by_name["Kubernetes"].importance == "preferred"
    assert any("Bachelor" in c for c in constraints)


def test_inline_preferred_signal():
    skills, _, _ = extract_job_requirements("Requirements\n- Java\n- Experience with Redis is a plus")
    by_name = {s.skill: s for s in skills}
    assert by_name["Java"].importance == "required"
    assert by_name["Redis"].importance == "preferred"


def test_jd_without_headings_is_inferred_required():
    skills, _, clear = extract_job_requirements("We want someone who knows Python and Docker well.")
    assert not clear
    assert all(s.importance == "required" and s.inferred for s in skills)


# ---------- "X or Y" alternatives ----------

def test_or_lines_become_alternatives():
    skills, _, _ = extract_job_requirements(
        "Requirements\nExperience with FastAPI or Django.\nCode in one of Java, C++ or Python.\nPython scripting."
    )
    alt = {s.skill: s.alternatives for s in skills}
    assert alt["FastAPI"] == ["Django"]
    assert alt["Java"] == ["C++", "Python"]
    assert alt["Python"] == []  # also asked for on its own, so it stays a hard requirement


def test_alternative_counts_as_matched():
    result = run_analysis(SAMPLE_RESUME.replace("Python,", "Python, Django,"), SAMPLE_JD)
    fastapi = next(r for r in result["matched"] if r["skill"] == "FastAPI")
    assert fastapi["evidence"] == "alternative" and "Django" in fastapi["reason"]


def test_roadmap_learns_only_one_of_the_alternatives():
    result = run_analysis("Skills\nC++ and Linux experience on several projects.",
                          "Requirements\nGood knowledge of MySQL or PostgreSQL.\nStrong C++.")
    missing = {r["skill"] for r in result["missing_required"]}
    planned = [s["skill"] for s in result["roadmap"]["steps"]]
    assert missing == {"MySQL", "PostgreSQL"}         # both reported as gaps...
    assert ("MySQL" in planned) != ("PostgreSQL" in planned)  # ...but only one is in the plan
    step = next(s for s in result["roadmap"]["steps"] if s["skill"] in ("MySQL", "PostgreSQL"))
    assert "instead" in step["reason"]


# ---------- matching & scoring ----------

def test_matched_and_missing():
    result = run_analysis(SAMPLE_RESUME, SAMPLE_JD)
    matched = {r["skill"] for r in result["matched"]}
    missing = {r["skill"] for r in result["missing_required"]}
    assert {"Python", "SQL", "Git"} <= matched
    assert {"FastAPI", "Django", "Docker"} <= missing
    assert {r["skill"] for r in result["missing_preferred"]} == {"Kubernetes", "AWS"}


def test_coverage_math():
    rows = [
        {"importance": "required", "status": "matched", "resume_excerpt": "x"},
        {"importance": "required", "status": "missing", "resume_excerpt": None},
        {"importance": "required", "status": "uncertain", "resume_excerpt": "x"},   # half credit
        {"importance": "required", "status": "uncertain", "resume_excerpt": None},  # excluded
    ]
    assert matcher.coverage(rows, "required") == 0.5
    assert matcher.coverage(rows, "preferred") is None


def test_overall_score_formula():
    assert matcher.overall_score(1.0, 0.0) == 70.0
    assert matcher.overall_score(0.5, 0.5) == 50.0
    assert matcher.overall_score(None, 0.4) == 40.0


# ---------- semantic search ----------

def test_split_lines_rejoins_wrapped_sentences():
    text = "Projects\n- Built a REST API with Node.js and\nExpress.js for orders\nwith JWT auth."
    assert semantic.split_lines(text) == [
        "Built a REST API with Node.js and",
        "Express.js for orders with JWT auth.",
    ]


def test_semantic_finds_meaning_without_shared_keywords():
    resume = ("Built a REST API with Node.js and Express backed by MongoDB.\n"
              "Won second prize in a college painting competition.")
    [m] = semantic.match_requirements(["Experience developing server-side web applications"], resume)
    assert m["closest_resume_line"].startswith("Built a REST API")


def test_semantic_score_bounds():
    assert semantic.semantic_score([]) == 0.0
    assert semantic.match_requirements([], "some resume text here") == []
    assert semantic.label(0.9) == "strong" and semantic.label(0.1) == "not shown"


def test_exact_skill_match_overrides_weak_semantic_label():
    result = run_analysis(SAMPLE_RESUME, "Requirements\nVersion control with Git.\nStrong SQL skills needed.")
    git = next(m for m in result["requirement_matches"] if "Git" in m["requirement"])
    assert git["match"] == "strong" and git["skills_found"] == ["Git"]


# ---------- roadmap ----------

def test_roadmap_puts_prerequisites_first():
    plan = build_roadmap([{"skill": "FastAPI", "importance": "required"}], known_skills=set())
    order = [s["skill"] for s in plan["steps"]]
    assert order.index("Python") < order.index("FastAPI")
    assert order.index("REST APIs") < order.index("FastAPI")


def test_roadmap_skips_known_prerequisites():
    plan = build_roadmap([{"skill": "FastAPI", "importance": "required"}],
                         known_skills={"Python", "REST APIs"})
    assert [s["skill"] for s in plan["steps"]] == ["FastAPI"]


def test_required_before_preferred():
    missing = [{"skill": "AWS", "importance": "preferred"}, {"skill": "Git", "importance": "required"}]
    plan = build_roadmap(missing, known_skills={"Linux"})
    assert [s["skill"] for s in plan["steps"]] == ["Git", "AWS"]


def test_deadline_defers_overflow():
    plan = build_roadmap([{"skill": "Kubernetes", "importance": "required"}],
                         known_skills={"Linux", "Docker"}, hours_per_day=2,
                         deadline=date(2026, 1, 3), today=date(2026, 1, 1))
    assert plan["days_available"] == 2
    assert plan["deferred_skills"] == ["Kubernetes"]


def test_unknown_skill_gets_fallback():
    step = build_roadmap([{"skill": "GraphQL", "importance": "required"}], set())["steps"][0]
    assert not step["curated"] and step["resources"] == []
