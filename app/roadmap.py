"""Deterministic, prerequisite-aware learning roadmap.

Hours are rough planning estimates for reaching a working, interview-ready level,
not a promise of mastery.
"""
import math
from datetime import date

DEFAULT_HOURS_PER_DAY = 2.0
FALLBACK_HOURS = 10

ROADMAP_DATA: dict[str, dict] = {
    "Python": {
        "prerequisites": [],
        "topics": ["Syntax, data types", "Lists, dicts, sets, comprehensions", "Functions & modules",
                   "Exceptions & file I/O", "Virtual environments & pip"],
        "exercise": "Write a CLI that reads a CSV of expenses and prints monthly totals.",
        "hours": 15,
        "resources": ["https://docs.python.org/3/tutorial/"],
    },
    "Java": {
        "prerequisites": [],
        "topics": ["Syntax & types", "Classes, interfaces, inheritance", "Collections framework",
                   "Exceptions", "Streams & lambdas"],
        "exercise": "Build a console library-management system using classes and collections.",
        "hours": 20,
        "resources": ["https://dev.java/learn/"],
    },
    "JavaScript": {
        "prerequisites": [],
        "topics": ["Types, scope, closures", "Arrays & objects", "Promises & async/await",
                   "DOM & fetch", "ES modules"],
        "exercise": "Build a to-do app that saves items in localStorage.",
        "hours": 15,
        "resources": ["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"],
    },
    "TypeScript": {
        "prerequisites": ["JavaScript"],
        "topics": ["Basic & union types", "Interfaces & type aliases", "Generics", "tsconfig & compiling"],
        "exercise": "Convert an existing small JavaScript project to TypeScript with strict mode.",
        "hours": 8,
        "resources": ["https://www.typescriptlang.org/docs/"],
    },
    "SQL": {
        "prerequisites": [],
        "topics": ["SELECT, WHERE, ORDER BY", "JOINs", "GROUP BY & aggregates", "Subqueries",
                   "Indexes & normalisation"],
        "exercise": "Design a schema for a college-events app and write 10 queries against it.",
        "hours": 10,
        "resources": ["https://www.postgresql.org/docs/current/tutorial-sql.html"],
    },
    "PostgreSQL": {
        "prerequisites": ["SQL"],
        "topics": ["Install & psql", "Data types & constraints", "Transactions", "Indexes & EXPLAIN"],
        "exercise": "Back a small REST API with PostgreSQL instead of an in-memory list.",
        "hours": 6,
        "resources": ["https://www.postgresql.org/docs/current/tutorial.html"],
    },
    "MySQL": {
        "prerequisites": ["SQL"],
        "topics": ["Install & client", "Data types & constraints", "Transactions", "Indexes"],
        "exercise": "Back a small REST API with MySQL instead of an in-memory list.",
        "hours": 6,
        "resources": ["https://dev.mysql.com/doc/"],
    },
    "MongoDB": {
        "prerequisites": [],
        "topics": ["Documents & collections", "CRUD", "Indexes", "Aggregation pipeline", "Schema design"],
        "exercise": "Store and query blog posts with comments using the aggregation pipeline.",
        "hours": 8,
        "resources": ["https://www.mongodb.com/docs/manual/"],
    },
    "REST APIs": {
        "prerequisites": [],
        "topics": ["HTTP methods & status codes", "Resource naming", "JSON request/response",
                   "Validation & error format", "Pagination & auth basics"],
        "exercise": "Design and document a CRUD API for a notes app (endpoints + status codes).",
        "hours": 6,
        "resources": ["https://developer.mozilla.org/en-US/docs/Web/HTTP"],
    },
    "Node.js": {
        "prerequisites": ["JavaScript"],
        "topics": ["Event loop", "Modules & npm", "fs & path", "Async patterns"],
        "exercise": "Write a script that watches a folder and logs file changes.",
        "hours": 8,
        "resources": ["https://nodejs.org/en/learn"],
    },
    "Express.js": {
        "prerequisites": ["Node.js", "REST APIs"],
        "topics": ["Routing", "Middleware", "Error handling", "Validation"],
        "exercise": "Build a notes REST API with Express and proper error middleware.",
        "hours": 8,
        "resources": ["https://expressjs.com/"],
    },
    "FastAPI": {
        "prerequisites": ["Python", "REST APIs"],
        "topics": ["Path & query parameters", "Pydantic models", "Validation & HTTPException",
                   "Dependency injection", "Testing with TestClient"],
        "exercise": "Build a validated notes REST API with tests.",
        "hours": 10,
        "resources": ["https://fastapi.tiangolo.com/tutorial/"],
    },
    "Django": {
        "prerequisites": ["Python", "REST APIs"],
        "topics": ["Project/app structure", "Models & ORM", "Views & URLs", "Admin", "Django REST Framework"],
        "exercise": "Build a blog with an admin panel and a JSON API.",
        "hours": 15,
        "resources": ["https://docs.djangoproject.com/en/stable/intro/tutorial01/"],
    },
    "Flask": {
        "prerequisites": ["Python"],
        "topics": ["Routes", "Templates", "Request handling", "Blueprints"],
        "exercise": "Build a URL shortener with Flask.",
        "hours": 8,
        "resources": ["https://flask.palletsprojects.com/"],
    },
    "Spring Boot": {
        "prerequisites": ["Java", "REST APIs"],
        "topics": ["Starters & auto-config", "Controllers", "Spring Data JPA", "Validation", "Testing"],
        "exercise": "Build a CRUD REST API with Spring Boot and an H2/PostgreSQL database.",
        "hours": 20,
        "resources": ["https://spring.io/guides"],
    },
    "HTML": {
        "prerequisites": [],
        "topics": ["Semantic elements", "Forms", "Accessibility basics"],
        "exercise": "Build an accessible multi-section portfolio page.",
        "hours": 4,
        "resources": ["https://developer.mozilla.org/en-US/docs/Learn"],
    },
    "CSS": {
        "prerequisites": ["HTML"],
        "topics": ["Box model", "Flexbox", "Grid", "Responsive design & media queries"],
        "exercise": "Make the portfolio page responsive for mobile and desktop.",
        "hours": 8,
        "resources": ["https://developer.mozilla.org/en-US/docs/Learn"],
    },
    "React": {
        "prerequisites": ["JavaScript", "HTML", "CSS"],
        "topics": ["Components & JSX", "Props & state", "Effects", "Lists & forms", "Fetching data"],
        "exercise": "Build a movie-search app that calls a public API.",
        "hours": 15,
        "resources": ["https://react.dev/learn"],
    },
    "Next.js": {
        "prerequisites": ["React"],
        "topics": ["App router", "Server vs client components", "Data fetching", "Deployment"],
        "exercise": "Rebuild the movie-search app with Next.js routing.",
        "hours": 10,
        "resources": ["https://nextjs.org/docs"],
    },
    "Git": {
        "prerequisites": [],
        "topics": ["Commits & branches", "Merging & conflicts", "Remotes & pull requests"],
        "exercise": "Contribute a change to your own repo via a feature branch and pull request.",
        "hours": 4,
        "resources": ["https://git-scm.com/book/en/v2"],
    },
    "Linux": {
        "prerequisites": [],
        "topics": ["Filesystem & permissions", "Processes", "Pipes & grep", "Shell scripts"],
        "exercise": "Write a bash script that backs up a folder and logs the result.",
        "hours": 8,
        "resources": ["https://ubuntu.com/tutorials/command-line-for-beginners"],
    },
    "Docker": {
        "prerequisites": ["Linux"],
        "topics": ["Images vs containers", "Dockerfile", "Volumes & ports", "docker compose"],
        "exercise": "Containerise one of your APIs with a Dockerfile and docker compose.",
        "hours": 8,
        "resources": ["https://docs.docker.com/get-started/"],
    },
    "Kubernetes": {
        "prerequisites": ["Docker"],
        "topics": ["Pods & deployments", "Services", "ConfigMaps & secrets", "kubectl"],
        "exercise": "Deploy your containerised API to a local cluster (minikube or kind).",
        "hours": 15,
        "resources": ["https://kubernetes.io/docs/tutorials/kubernetes-basics/"],
    },
    "AWS": {
        "prerequisites": ["Linux"],
        "topics": ["IAM", "EC2", "S3", "RDS basics", "Free-tier cost safety"],
        "exercise": "Host a static site on S3 and an API on EC2 (watch free-tier limits).",
        "hours": 15,
        "resources": ["https://aws.amazon.com/getting-started/"],
    },
    "CI/CD": {
        "prerequisites": ["Git"],
        "topics": ["Pipelines & triggers", "Running tests in CI", "Build artifacts", "Deploy steps"],
        "exercise": "Add a GitHub Actions workflow that runs your tests on every push.",
        "hours": 5,
        "resources": ["https://docs.github.com/en/actions"],
    },
    "Unit Testing": {
        "prerequisites": [],
        "topics": ["Arrange-act-assert", "Fixtures", "Mocking", "Edge cases & coverage"],
        "exercise": "Write tests for every function in one of your projects.",
        "hours": 5,
        "resources": ["https://docs.pytest.org/"],
    },
    "Data Structures": {
        "prerequisites": [],
        "topics": ["Arrays & strings", "Linked lists, stacks, queues", "Hash maps", "Trees & heaps", "Graphs"],
        "exercise": "Solve 5 problems per topic on a practice platform.",
        "hours": 30,
        "resources": ["https://cp-algorithms.com/"],
    },
    "Algorithms": {
        "prerequisites": ["Data Structures"],
        "topics": ["Sorting & searching", "Two pointers & sliding window", "Recursion & backtracking",
                   "Dynamic programming", "Graph traversal"],
        "exercise": "Solve 5 problems per topic and write the time complexity for each.",
        "hours": 30,
        "resources": ["https://cp-algorithms.com/"],
    },
    "DBMS": {
        "prerequisites": ["SQL"],
        "topics": ["ER model", "Normalisation", "Transactions & ACID", "Indexing", "Concurrency control"],
        "exercise": "Normalise a messy spreadsheet into 3NF tables and explain each step.",
        "hours": 8,
        "resources": ["https://www.postgresql.org/docs/current/tutorial.html"],
    },
    "System Design": {
        "prerequisites": ["DBMS", "REST APIs"],
        "topics": ["Scalability basics", "Caching", "Load balancing", "Database scaling", "Queues"],
        "exercise": "Design a URL shortener on paper: APIs, schema, scaling plan.",
        "hours": 15,
        "resources": ["https://github.com/donnemartin/system-design-primer"],
    },
    "Machine Learning": {
        "prerequisites": ["Python", "NumPy", "Pandas"],
        "topics": ["Supervised vs unsupervised", "Train/test split", "Regression & classification",
                   "Evaluation metrics", "Overfitting"],
        "exercise": "Train and evaluate a classifier on a public dataset.",
        "hours": 20,
        "resources": ["https://scikit-learn.org/stable/user_guide.html"],
    },
    "NumPy": {
        "prerequisites": ["Python"],
        "topics": ["Arrays", "Vectorised operations", "Broadcasting", "Indexing"],
        "exercise": "Implement mean/std/normalisation of a dataset without loops.",
        "hours": 4,
        "resources": ["https://numpy.org/doc/stable/user/absolute_beginners.html"],
    },
    "Pandas": {
        "prerequisites": ["Python"],
        "topics": ["Series & DataFrames", "Filtering", "groupby", "Merging", "Missing data"],
        "exercise": "Clean and summarise a public CSV dataset.",
        "hours": 6,
        "resources": ["https://pandas.pydata.org/docs/user_guide/index.html"],
    },
    "scikit-learn": {
        "prerequisites": ["Machine Learning"],
        "topics": ["Estimator API", "Pipelines", "Cross-validation", "Text features (TF-IDF)"],
        "exercise": "Build a pipeline that classifies short texts with TF-IDF + logistic regression.",
        "hours": 8,
        "resources": ["https://scikit-learn.org/stable/user_guide.html"],
    },
    "Statistics": {
        "prerequisites": [],
        "topics": ["Descriptive statistics", "Probability & distributions", "Hypothesis testing",
                   "Correlation & regression"],
        "exercise": "Run an A/B test analysis on a public dataset and explain the p-value.",
        "hours": 12,
        "resources": ["https://www.khanacademy.org/math/statistics-probability"],
    },
    "Excel": {
        "prerequisites": [],
        "topics": ["Formulas & lookups (XLOOKUP)", "Pivot tables", "Charts", "Data cleaning"],
        "exercise": "Build a pivot-table sales summary with a chart from a sample dataset.",
        "hours": 6,
        "resources": ["https://support.microsoft.com/excel"],
    },
    "Data Visualization": {
        "prerequisites": [],
        "topics": ["Choosing the right chart", "Labels & colour", "Dashboards that answer one question"],
        "exercise": "Redesign one cluttered chart into a clear one and explain the changes.",
        "hours": 4,
        "resources": ["https://matplotlib.org/stable/tutorials/index.html"],
    },
    "Power BI": {
        "prerequisites": ["Excel", "Data Visualization"],
        "topics": ["Power Query", "Data modelling", "DAX basics", "Reports & dashboards"],
        "exercise": "Build a one-page sales dashboard with slicers.",
        "hours": 10,
        "resources": ["https://learn.microsoft.com/en-us/power-bi/fundamentals/"],
    },
    "Tableau": {
        "prerequisites": ["Data Visualization"],
        "topics": ["Connecting data", "Dimensions & measures", "Calculated fields", "Dashboards"],
        "exercise": "Publish a dashboard on Tableau Public from a public dataset.",
        "hours": 10,
        "resources": ["https://www.tableau.com/learn/training"],
    },
    "Kafka": {
        "prerequisites": ["Docker"],
        "topics": ["Topics & partitions", "Producers & consumers", "Consumer groups", "Delivery guarantees"],
        "exercise": "Run Kafka in Docker and build a producer/consumer for order events.",
        "hours": 10,
        "resources": ["https://kafka.apache.org/documentation/"],
    },
}

PRIORITY_LABEL ={"required": "High", "preferred": "Medium"}


def _order_skills(targets: list[tuple[str, str]], known: set[str]) -> list[dict]:
    """Depth-first: put missing prerequisites before the skill that needs them."""
    ordered: list[dict] = []
    placed: set[str] = set()

    def visit(skill: str, importance: str, reason: str, stack: tuple[str, ...]) -> None:
        if skill in placed or skill in stack:  # already scheduled, or a cycle
            return
        for prereq in ROADMAP_DATA.get(skill, {}).get("prerequisites", []):
            if prereq not in known:
                visit(prereq, importance, f"Prerequisite for {skill}", stack + (skill,))
        placed.add(skill)
        ordered.append({"skill": skill, "importance": importance, "reason": reason})

    for skill, importance in targets:
        reason = ("Explicitly required by the job description" if importance == "required"
                  else "Listed as preferred / nice-to-have")
        visit(skill, importance, reason, ())
    return ordered


def build_roadmap(
    missing: list[dict],
    known_skills: set[str],
    hours_per_day: float | None = None,
    deadline: date | None = None,
    today: date | None = None,
) -> dict:
    """missing: rows from matcher.compare_skills with status == 'missing'."""
    hours_per_day = hours_per_day or DEFAULT_HOURS_PER_DAY
    today = today or date.today()

    # Required first, preferred second; stable within each group.
    targets = sorted(((r["skill"], r["importance"]) for r in missing),
                     key=lambda t: 0 if t[1] == "required" else 1)
    ordered = _order_skills(targets, known_skills)

    days_available = (deadline - today).days if deadline else None
    budget = days_available * hours_per_day if days_available is not None else None

    steps, cumulative, deferred = [], 0.0, []
    for i, item in enumerate(ordered, start=1):
        data = ROADMAP_DATA.get(item["skill"])
        hours = data["hours"] if data else FALLBACK_HOURS
        start_day = math.floor(cumulative / hours_per_day) + 1
        cumulative += hours
        end_day = math.ceil(cumulative / hours_per_day)
        fits = budget is None or cumulative <= budget
        if not fits:
            deferred.append(item["skill"])
        steps.append({
            "order": i,
            "skill": item["skill"],
            "priority": PRIORITY_LABEL[item["importance"]],
            "reason": item["reason"],
            "prerequisites": data["prerequisites"] if data else [],
            "topics": data["topics"] if data else [],
            "exercise": (data["exercise"] if data else
                         f"No curated plan yet. Read the official {item['skill']} documentation "
                         "and build one small project that uses it."),
            "estimated_hours": hours,
            "day_range": f"Day {start_day}–{end_day}",
            "resources": data["resources"] if data else [],
            "curated": data is not None,
            "fits_deadline": fits,
        })

    return {
        "hours_per_day": hours_per_day,
        "total_hours": cumulative,
        "estimated_days": math.ceil(cumulative / hours_per_day) if cumulative else 0,
        "days_available": days_available,
        "deferred_skills": deferred,
        "steps": steps,
        "note": "Hours are rough planning estimates, not a guarantee of mastery.",
    }
