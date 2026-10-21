from app.ai.jd_parser import analyze_jd

JD = """GenAI QA Engineer - Cognizant

Responsibilities:
- Design and maintain automated tests using Playwright and Python
- Validate LLM outputs and build API testing suites

Requirements:
- 1-3 years of experience in test automation
- Strong Python, Playwright, Selenium and API testing skills

Preferred Skills:
- Docker
- AWS exposure is a plus
"""


def test_skills_and_importance():
    r = analyze_jd(JD)
    imp = {s["name"]: s["importance"] for s in r["skills"]}
    assert imp["Python"] == "REQUIRED"
    assert imp["Playwright"] == "REQUIRED"
    assert imp["Docker"] == "PREFERRED"
    assert imp["AWS"] == "PREFERRED"
    assert "LLM" in imp


def test_experience_and_responsibilities():
    r = analyze_jd(JD)
    assert r["experience"]["min"] == 1 and r["experience"]["max"] == 3
    assert len(r["responsibilities"]) == 2


def test_scores_ranked_and_topics():
    r = analyze_jd(JD)
    scores = [s["score"] for s in r["skills"]]
    assert scores == sorted(scores, reverse=True) and scores[0] == 100
    assert any(t["skill"] == "Python" for t in r["interview_topics"])
    assert "Playwright" in r["tools"]


def test_single_paragraph_jd():
    r = analyze_jd("Looking for Python developer with FastAPI, PostgreSQL and Docker experience. "
                   "AWS knowledge is preferred.")
    imp = {s["name"]: s["importance"] for s in r["skills"]}
    assert imp["FastAPI"] == "REQUIRED" and imp["PostgreSQL"] == "REQUIRED"
    assert imp["AWS"] == "PREFERRED"


def test_empty_text():
    r = analyze_jd("")
    assert r["skills"] == [] and r["experience"] is None
