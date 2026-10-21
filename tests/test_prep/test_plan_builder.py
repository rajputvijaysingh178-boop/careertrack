from app.ai.plan_builder import build_plan

SKILLS = [{"name": "Python", "importance": "REQUIRED"}, {"name": "Playwright", "importance": "REQUIRED"},
          {"name": "API Testing", "importance": "REQUIRED"}, {"name": "SQL", "importance": "PREFERRED"},
          {"name": "GenAI", "importance": "REQUIRED"}]


def test_seven_days_last_is_mock():
    plan = build_plan(SKILLS, 7)
    assert len(plan) == 7
    assert [d["day"] for d in plan] == list(range(1, 8))
    assert "Mock interview" in plan[-1]["title"]


def test_required_skills_come_before_preferred():
    plan = build_plan(SKILLS, 7)
    titles = " ".join(d["title"] for d in plan[:-1])
    assert titles.index("Python") < titles.index("SQL")


def test_few_skills_are_split_into_parts():
    plan = build_plan([{"name": "Python", "importance": "REQUIRED"}], 5)
    assert len(plan) == 5
    assert any("part" in d["title"] for d in plan)


def test_many_skills_are_grouped():
    skills = [{"name": n, "importance": "REQUIRED"} for n in
              ["Python", "Java", "SQL", "Docker", "AWS", "Git", "Linux", "React", "Django", "Flask"]]
    plan = build_plan(skills, 4)
    assert len(plan) == 4
    assert "&" in plan[0]["title"]


def test_no_skills_gives_generic_plan_and_days_clamped():
    plan = build_plan([], 1)
    assert len(plan) == 3


def test_known_skills_get_light_revision():
    plan = build_plan([{"name": "Python", "importance": "REQUIRED"}], 3, known=["python"])
    assert plan[0]["tasks"][0].startswith("Quick revision")
