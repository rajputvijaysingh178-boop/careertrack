from app.ai.matching import match_skills

JOB = [{"name": "Python", "importance": "REQUIRED"}, {"name": "FastAPI", "importance": "REQUIRED"},
       {"name": "PostgreSQL", "importance": "REQUIRED"}, {"name": "Docker", "importance": "REQUIRED"},
       {"name": "AWS", "importance": "PREFERRED"}]


def test_document_example_80_percent_style():
    r = match_skills(JOB, ["Python", "FastAPI", "PostgreSQL", "Docker"])
    # weights: required 4*3=12, preferred 2 -> 12/14 = 86%
    assert r["match_percent"] == 86
    assert [m["name"] for m in r["missing"]] == ["AWS"]
    assert r["label"] == "Strong match"


def test_alias_matching():
    r = match_skills([{"name": "Kubernetes", "importance": "REQUIRED"}], ["k8s"])
    assert r["match_percent"] == 100


def test_nothing_matches_and_tips():
    r = match_skills(JOB, ["Cobol"])
    assert r["match_percent"] == 0 and r["label"] == "Low match"
    assert any("Python" in t for t in r["recommendations"])
    assert r["extra_skills"] == ["Cobol"]


def test_empty_job_skills():
    assert match_skills([], ["Python"])["match_percent"] == 0
