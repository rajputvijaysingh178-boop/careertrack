"""OWNER: M2 (Application Tracker)
Pydantic request/response schemas for documents."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from urllib.parse import urlsplit


class DocumentCreate(BaseModel):
    application_id: int
    name: str = Field(min_length=1, max_length=255)
    file_url: str = Field(min_length=1, max_length=1000)
    doc_type: str | None = Field(None, max_length=50)

    @field_validator("file_url")
    @classmethod
    def safe_document_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "http"} and not value.startswith("/uploads/"):
            raise ValueError("file_url must be an HTTP(S) link or an /uploads/ path")
        if parsed.scheme in {"http", "https"} and not parsed.netloc:
            raise ValueError("file_url must include a host")
        return value


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    application_id: int
    name: str
    file_url: str
    doc_type: str | None
    created_at: datetime
