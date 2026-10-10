import io
import zipfile

import pytest

from app.ai.resume_parser import extract_text


def test_txt():
    assert "Python" in extract_text("cv.txt", b"Skills: Python, SQL")


def test_docx():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:p><w:t>Python &amp; FastAPI</w:t></w:p></w:document>")
    assert "Python & FastAPI" in extract_text("cv.docx", buf.getvalue())


def test_unsupported():
    with pytest.raises(ValueError):
        extract_text("cv.exe", b"x")
