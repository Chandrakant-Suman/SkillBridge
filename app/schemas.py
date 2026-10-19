"""Pydantic models = the API contract between backend and frontend."""
from typing import Literal

from pydantic import BaseModel


class ResumeSkill(BaseModel):
    skill: str
    category: str
    sections: list[str]
    excerpt: str
    uncertain: bool


class SkillResult(BaseModel):
    skill: str
    category: str
    importance: Literal["required", "preferred"]
    jd_source: str
    inferred_importance: bool
    status: Literal["matched", "missing", "uncertain"]
    reason: str
    evidence: str | None
    jd_excerpt: str
    alternatives: list[str]
    resume_excerpt: str | None


class ScoreBreakdown(BaseModel):
    overall: float
    required_coverage: float | None
    preferred_coverage: float | None
    semantic_match: float
    formula: str
    disclaimer: str


class RoadmapStep(BaseModel):
    order: int
    skill: str
    priority: str
    reason: str
    prerequisites: list[str]
    topics: list[str]
    exercise: str
    estimated_hours: float
    day_range: str
    resources: list[str]
    curated: bool
    fits_deadline: bool


class RequirementMatch(BaseModel):
    requirement: str
    closest_resume_line: str
    similarity: float
    match: Literal["strong", "partial", "not shown"]
    skills_found: list[str]


class Roadmap(BaseModel):
    hours_per_day: float
    total_hours: float
    estimated_days: int
    days_available: int | None
    deferred_skills: list[str]
    steps: list[RoadmapStep]
    note: str


class AnalysisResponse(BaseModel):
    score: ScoreBreakdown
    resume_skills: list[ResumeSkill]
    matched: list[SkillResult]
    missing_required: list[SkillResult]
    missing_preferred: list[SkillResult]
    uncertain: list[SkillResult]
    requirement_matches: list[RequirementMatch]
    eligibility: list[str]
    jd_has_clear_sections: bool
    roadmap: Roadmap
    recommendations: list[str]
    limitations: list[str]
