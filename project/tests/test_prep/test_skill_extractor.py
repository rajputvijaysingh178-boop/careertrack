from app.ai.skill_extractor import extract_skills


def test_extract():
    assert extract_skills("Need Python and FastAPI", ["Python", "FastAPI", "Java"]) == ["Python", "FastAPI"]
