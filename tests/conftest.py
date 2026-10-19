import pymupdf
import pytest

SAMPLE_RESUME = """Chandrakant Sharma
Skills
Python, JavaScript, SQL, Git, HTML, CSS
Projects
Built a REST API with Node.js and Express.js backed by MongoDB.
Created a portfolio website using React.
Education
B.Tech in Computer Science, CGPA 8.1
"""

SAMPLE_JD = """Backend Developer Intern
Responsibilities
Build and maintain backend services.
Requirements
Strong knowledge of Python and SQL.
Experience with FastAPI or Django.
Familiarity with Docker and Git.
Bachelor's degree in Computer Science.
Nice to have
Kubernetes, AWS
"""


def make_pdf(text: str) -> bytes:
    """Create a real text-based PDF in memory for tests."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def resume_pdf() -> bytes:
    return make_pdf(SAMPLE_RESUME)
