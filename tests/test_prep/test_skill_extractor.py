from app.ai.skill_extractor import canonical_key, extract_skills, topics_for


def test_extract_in_order_of_appearance():
    assert extract_skills("Need Python and FastAPI", ["Python", "FastAPI", "Java"]) == ["Python", "FastAPI"]


def test_aliases_and_symbols():
    found = extract_skills("Experience with k8s, CI/CD pipelines and Node.js")
    assert "Kubernetes" in found and "CI/CD" in found and "Node.js" in found


def test_java_does_not_match_javascript():
    assert extract_skills("We use JavaScript daily") == ["JavaScript"]


def test_canonical_key():
    assert canonical_key("K8s") == "kubernetes"
    assert canonical_key("fast api") == "fastapi"
    assert canonical_key("SomethingNew") == "somethingnew"


def test_topics_for():
    assert "Decorators" in topics_for("python")
    assert topics_for("unknown-skill") == []


def test_db_skill_names_are_merged():
    assert "Cypress" in extract_skills("Looking for Cypress experience", ["Cypress"])
