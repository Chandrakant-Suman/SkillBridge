"""Find known skills in text using a curated taxonomy + alias regexes.

No ML here on purpose: dictionary matching is predictable, explainable and testable.
"""
import re
from dataclasses import dataclass, field

# canonical skill name -> (category, aliases). Aliases are matched case-insensitively
# as whole terms, so "java" does NOT match inside "javascript".
SKILL_TAXONOMY: dict[str, tuple[str, list[str]]] = {
    # Programming languages
    "Python": ("Programming Languages", ["python", "python3"]),
    "Java": ("Programming Languages", ["java"]),
    "C++": ("Programming Languages", ["c++", "cpp"]),
    "C#": ("Programming Languages", ["c#", "csharp"]),
    "JavaScript": ("Programming Languages", ["javascript", "js", "es6", "ecmascript"]),
    "TypeScript": ("Programming Languages", ["typescript", "ts"]),
    "Go": ("Programming Languages", ["golang", "Go"]),
    "Kotlin": ("Programming Languages", ["kotlin"]),
    "Rust": ("Programming Languages", ["rust"]),
    "SQL": ("Databases", ["sql"]),
    # CS fundamentals
    "Data Structures": ("CS Fundamentals", ["data structures", "dsa"]),
    "Algorithms": ("CS Fundamentals", ["algorithms", "algorithm design"]),
    "OOP": ("CS Fundamentals", ["oop", "oops", "object oriented programming",
                                "object-oriented programming", "object-oriented design"]),
    "Operating Systems": ("CS Fundamentals", ["operating systems", "operating system"]),
    "Computer Networks": ("CS Fundamentals", ["computer networks", "networking", "tcp/ip"]),
    "DBMS": ("CS Fundamentals", ["dbms", "database management systems"]),
    "System Design": ("CS Fundamentals", ["system design", "low level design",
                                          "high level design", "lld", "hld"]),
    # Backend
    "Node.js": ("Backend", ["node.js", "nodejs", "Node"]),
    "Express.js": ("Backend", ["express.js", "expressjs", "Express"]),
    "FastAPI": ("Backend", ["fastapi"]),
    "Django": ("Backend", ["django"]),
    "Flask": ("Backend", ["flask"]),
    "Spring Boot": ("Backend", ["spring boot", "springboot", "Spring"]),
    "REST APIs": ("Backend", ["rest api", "rest apis", "restful", "restful api",
                              "restful apis", "rest"]),
    "GraphQL": ("Backend", ["graphql"]),
    "Microservices": ("Backend", ["microservices", "microservice"]),
    # Frontend / web
    "HTML": ("Web", ["html", "html5"]),
    "CSS": ("Web", ["css", "css3"]),
    "React": ("Web", ["react", "react.js", "reactjs"]),
    "Angular": ("Web", ["angular"]),
    "Next.js": ("Web", ["next.js", "nextjs"]),
    "Tailwind CSS": ("Web", ["tailwind", "tailwind css", "tailwindcss"]),
    # Databases
    "MySQL": ("Databases", ["mysql"]),
    "PostgreSQL": ("Databases", ["postgresql", "postgres"]),
    "MongoDB": ("Databases", ["mongodb", "mongo"]),
    "Redis": ("Databases", ["redis"]),
    # Cloud / DevOps
    "AWS": ("Cloud & DevOps", ["aws", "amazon web services"]),
    "Azure": ("Cloud & DevOps", ["azure"]),
    "GCP": ("Cloud & DevOps", ["gcp", "google cloud"]),
    "Docker": ("Cloud & DevOps", ["docker", "containerization"]),
    "Kubernetes": ("Cloud & DevOps", ["kubernetes", "k8s"]),
    "CI/CD": ("Cloud & DevOps", ["ci/cd", "continuous integration", "github actions", "jenkins"]),
    "Linux": ("Cloud & DevOps", ["linux", "unix", "bash", "shell scripting"]),
    # Tools / testing
    "Git": ("Tools & Testing", ["git", "github", "gitlab", "version control"]),
    "Unit Testing": ("Tools & Testing", ["unit testing", "unit tests", "pytest", "jest", "junit"]),
    "Maven": ("Tools & Testing", ["maven"]),
    "Hibernate": ("Backend", ["hibernate", "jpa"]),
    # Data / ML
    "Pandas": ("Data & ML", ["pandas"]),
    "NumPy": ("Data & ML", ["numpy"]),
    "scikit-learn": ("Data & ML", ["scikit-learn", "sklearn", "scikit learn"]),
    "Machine Learning": ("Data & ML", ["machine learning", "ml"]),
    "Statistics": ("Data & ML", ["statistics", "statistical analysis", "hypothesis testing"]),
    "Excel": ("Data & ML", ["excel", "ms excel", "microsoft excel", "advanced excel"]),
    "Power BI": ("Data & ML", ["power bi", "powerbi"]),
    "Tableau": ("Data & ML", ["tableau"]),
    "Data Visualization": ("Data & ML", ["data visualization", "data visualisation", "matplotlib",
                                         "seaborn", "dashboards", "dashboard"]),
    # Messaging
    "Kafka": ("Backend", ["kafka", "apache kafka"]),
    # Practices
    "Agile": ("Practices", ["agile", "scrum"]),
}

# Aliases that are ordinary English words. They are matched case-sensitively
# ("Go" but not "go"), and a skill found ONLY through one of them is marked uncertain.
AMBIGUOUS_ALIASES = {"Go", "Node", "Express", "Spring", "rest", "ts", "ml"}
CASE_SENSITIVE_ALIASES = {"Go", "Node", "Express", "Spring"}


def _build_pattern(alias: str) -> re.Pattern:
    # Whole-term match. Characters like + # . count as part of a term, so
    # "js" won't match inside "node.js" and "c" won't match inside "c++".
    escaped = re.escape(alias)
    flags = 0 if alias in CASE_SENSITIVE_ALIASES else re.IGNORECASE
    return re.compile(rf"(?<![A-Za-z0-9+#.]){escaped}(?![A-Za-z0-9+#])", flags)


# Compile once at import time: list of (canonical, alias, pattern)
_PATTERNS = [
    (skill, alias, _build_pattern(alias))
    for skill, (_, aliases) in SKILL_TAXONOMY.items()
    for alias in aliases
]


@dataclass
class SkillMention:
    skill: str
    category: str
    aliases_found: set[str] = field(default_factory=set)
    sections: set[str] = field(default_factory=set)
    excerpt: str = ""

    @property
    def uncertain(self) -> bool:
        return all(a in AMBIGUOUS_ALIASES for a in self.aliases_found)


def _excerpt(line: str, start: int, end: int, width: int = 60) -> str:
    left = max(0, start - width)
    right = min(len(line), end + width)
    snippet = line[left:right].strip()
    return ("…" if left > 0 else "") + snippet + ("…" if right < len(line) else "")


def find_skills_in_line(line: str) -> list[tuple[str, str, int, int]]:
    """Return (skill, alias, start, end) for every alias match in one line."""
    hits = []
    for skill, alias, pattern in _PATTERNS:
        for m in pattern.finditer(line):
            hits.append((skill, alias, m.start(), m.end()))
    return hits


# ---------- section detection ----------

RESUME_SECTIONS = {
    "skills": r"skills|technical skills|technologies|tech stack",
    "projects": r"projects?|personal projects|academic projects",
    "experience": r"experience|work experience|internships?|employment",
    "education": r"education|academics",
    "certifications": r"certifications?|courses|achievements|awards",
}

JD_SECTIONS = {
    # Order matters: "preferred qualifications" must be checked before "qualifications".
    "preferred": r"preferred|nice[- ]to[- ]have|good[- ]to[- ]have|bonus|desired|plus",
    "required": r"requirements?|required|must[- ]have|qualifications|what you(?:'ll| will)? need"
                r"|who you are|eligibility|skills",
    "responsibilities": r"responsibilit|what you(?:'ll| will) do|duties|the role|role overview",
}

PREFERRED_LINE_SIGNAL = re.compile(
    r"preferred|nice[- ]to[- ]have|good[- ]to[- ]have|is a plus|\ba plus\b|bonus|desirable",
    re.IGNORECASE,
)

_BULLET = re.compile(r"^\s*[-*•●▪◦·>]\s*|^\s*\d+[.)]\s+")


def detect_heading(line: str, sections: dict[str, str]) -> str | None:
    """Return the section key if this line looks like a heading, else None."""
    if _BULLET.match(line):
        return None
    cleaned = line.strip().strip("#:*").strip()
    if not cleaned or len(cleaned.split()) > 5:
        return None
    if find_skills_in_line(cleaned):  # "Python is a plus" is a sentence, not a heading
        return None
    for key, pattern in sections.items():
        if re.search(pattern, cleaned, re.IGNORECASE):
            return key
    return None


# ---------- resume ----------

def extract_resume_skills(text: str) -> dict[str, SkillMention]:
    found: dict[str, SkillMention] = {}
    section = "other"
    for line in text.splitlines():
        heading = detect_heading(line, RESUME_SECTIONS)
        if heading:
            section = heading
            continue
        for skill, alias, start, end in find_skills_in_line(line):
            mention = found.setdefault(skill, SkillMention(skill, SKILL_TAXONOMY[skill][0]))
            mention.aliases_found.add(alias)
            mention.sections.add(section)
            # Prefer an excerpt from projects/experience: that's stronger evidence.
            if not mention.excerpt or section in ("projects", "experience"):
                mention.excerpt = _excerpt(line, start, end)
    return found


# ---------- job description ----------

@dataclass
class JobSkill:
    skill: str
    category: str
    importance: str          # "required" | "preferred"
    source: str              # which JD section it came from
    inferred: bool           # True when the JD didn't clearly say required/preferred
    uncertain: bool
    excerpt: str
    # Other skills that satisfy the same requirement ("FastAPI or Django"). Empty when the
    # skill is also asked for on its own somewhere in the JD.
    alternatives: list[str] = field(default_factory=list)


# "X or Y", "one of X, Y" and "X/Y" lines list interchangeable skills.
OR_SIGNAL = re.compile(r"\bor\b|\bone of\b|\beither\b|[A-Za-z+#]/[A-Za-z]", re.IGNORECASE)

_RANK = {"required": 3, "responsibilities": 2, "general": 1, "preferred": 0}

EXPERIENCE_PATTERN = re.compile(
    r"\b\d+\s*\+?\s*(?:-|to)?\s*\d*\s*\+?\s*(?:years?|yrs?)\b"
    r"|\b(?:b\.?\s?tech|b\.?e\.|bachelor'?s?|master'?s?|m\.?\s?tech|degree|cgpa|gpa|graduat\w*"
    r"|batch|backlogs?)\b",
    re.IGNORECASE,
)


def extract_requirement_lines(text: str) -> list[str]:
    """JD lines under Requirements / Responsibilities / Preferred headings (all lines if
    the JD has no headings). Eligibility lines (degree, years, CGPA) are left out."""
    picked, everything, section, saw_heading = [], [], "general", False
    for line in text.splitlines():
        heading = detect_heading(line, JD_SECTIONS)
        if heading:
            section, saw_heading = heading, True
            continue
        clean = _BULLET.sub("", line).strip()
        if not clean or EXPERIENCE_PATTERN.search(clean):
            continue
        everything.append(clean)
        if section != "general":
            picked.append(clean)
    return picked if saw_heading else everything


def extract_job_requirements(text: str) -> tuple[list[JobSkill], list[str], bool]:
    """Return (skills, experience/eligibility lines, has_clear_sections)."""
    best: dict[str, tuple[str, set[str], str]] = {}  # skill -> (context, aliases, excerpt)
    section = "general"
    saw_heading = False
    constraints: list[str] = []
    alternatives: dict[str, set[str]] = {}  # skill -> skills it can be swapped with
    asked_alone: set[str] = set()           # skills that appear on a line without "or"

    for line in text.splitlines():
        heading = detect_heading(line, JD_SECTIONS)
        if heading:
            section, saw_heading = heading, True
            continue
        if EXPERIENCE_PATTERN.search(line) and len(constraints) < 10:
            constraints.append(_BULLET.sub("", line).strip()[:200])

        context = "preferred" if PREFERRED_LINE_SIGNAL.search(line) else section
        hits = find_skills_in_line(line)
        names = {h[0] for h in hits}
        if len(names) >= 2 and OR_SIGNAL.search(line):
            for name in names:
                alternatives.setdefault(name, set()).update(names - {name})
        else:
            asked_alone.update(names)
        for skill, alias, start, end in hits:
            prev = best.get(skill)
            if prev is None:
                best[skill] = (context, {alias}, _excerpt(line, start, end))
            else:
                prev[1].add(alias)
                if _RANK[context] > _RANK[prev[0]]:
                    best[skill] = (context, prev[1], _excerpt(line, start, end))

    skills = []
    for skill, (context, aliases, excerpt) in best.items():
        importance = "preferred" if context == "preferred" else "required"
        # "required" from an explicit Requirements section is certain; anything else is inferred.
        inferred = context != "required" and context != "preferred"
        skills.append(JobSkill(
            skill=skill,
            category=SKILL_TAXONOMY[skill][0],
            importance=importance,
            source=context,
            inferred=inferred,
            uncertain=all(a in AMBIGUOUS_ALIASES for a in aliases),
            excerpt=excerpt,
            alternatives=[] if skill in asked_alone else sorted(alternatives.get(skill, ())),
        ))
    return skills, constraints, saw_heading
