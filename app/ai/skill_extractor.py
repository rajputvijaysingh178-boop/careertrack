"""OWNER: M3 - rule-based extractor (works without AI). Match JD text against the skills table."""


def extract_skills(jd_text: str, known_skills: list[str]) -> list[str]:
    text = jd_text.lower()
    return [s for s in known_skills if s.lower() in text]
