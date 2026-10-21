"""OWNER: M1 - small pure text helpers"""
import re
import unicodedata


def slugify(text: str, max_len: int = 80) -> str:
    """'Top 30 Python Interview Questions!' -> 'top-30-python-interview-questions'"""
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].strip("-") or "post"


def unique_slug(base: str, exists) -> str:
    """exists(slug) -> bool. Appends -2, -3 ... until the slug is free."""
    slug, n = base, 2
    while exists(slug):
        slug = f"{base}-{n}"
        n += 1
    return slug
