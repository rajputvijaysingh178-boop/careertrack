"""OWNER: M1 - rule-based duplicate job detection. Pure python, no DB.

Two jobs of the SAME company are duplicates when:
  - titles are (nearly) identical AND the descriptions are similar, or
  - the descriptions are almost identical even though the titles differ, or
  - the titles are identical and one of the descriptions is empty.
"""
import re
from difflib import SequenceMatcher

_STOP = {"the", "a", "an", "and", "for", "of", "at", "in", "to", "with", "is", "are", "we", "you", "our", "will",
         "be", "or", "on", "as", "by", "this", "that", "from", "have", "has", "your"}


def normalize_title(title: str) -> str:
    words = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).split()
    return " ".join(w for w in words if w not in _STOP)


def title_similarity(a: str, b: str) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _tokens(text: str) -> set:
    return {w for w in re.sub(r"[^a-z0-9+#.]+", " ", (text or "").lower()).split()
            if len(w) > 2 and w not in _STOP}


def text_similarity(a: str, b: str) -> float:
    """Jaccard similarity of the word sets (0..1)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def compare(title_a: str, jd_a: str, title_b: str, jd_b: str) -> dict:
    ts, js = title_similarity(title_a, title_b), text_similarity(jd_a, jd_b)
    no_jd = not _tokens(jd_a) or not _tokens(jd_b)
    duplicate = ((ts >= 0.85 and js >= 0.5) or js >= 0.85 or (ts >= 0.99 and no_jd))
    return {"duplicate": duplicate, "title_similarity": round(ts, 2), "description_similarity": round(js, 2),
            "score": round(0.5 * ts + 0.5 * js, 2)}
