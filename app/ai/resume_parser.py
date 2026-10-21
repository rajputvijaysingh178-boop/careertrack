"""OWNER: M3 - turn an uploaded resume (pdf / docx / txt / md) into plain text."""
import html
import io
import re
import zipfile


def extract_text(filename: str, content: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader  # imported lazily so the module loads without pypdf
        reader = PdfReader(io.BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if name.endswith(".docx"):
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        return html.unescape(re.sub(r"<[^>]+>", "", xml)).strip()
    if name.endswith((".txt", ".md", ".text")) or not name:
        return content.decode("utf-8", errors="ignore").strip()
    raise ValueError("Unsupported resume format. Upload a PDF, DOCX or TXT file.")
