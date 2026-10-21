"""OWNER: M1
Responsibility: study materials (links or uploaded files) attached to a job / skill / company / role / round,
plus user bookmarks of materials.
"""
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.config import settings
from app.models.material import Material
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.skill_repository import SkillRepository
from app.schemas.material import MATERIAL_TYPES, MaterialCreate, MaterialUpdate

UPLOAD_DIR = Path(settings.MATERIAL_UPLOAD_DIR)
ALLOWED_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".md"}
MAX_BYTES = settings.MAX_MATERIAL_UPLOAD_BYTES


class MaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MaterialRepository(db)
        self.jobs = JobRepository(db)
        self.companies = CompanyRepository(db)
        self.skills = SkillRepository(db)

    def _check_refs(self, skill_id=None, job_id=None, company_id=None) -> None:
        if skill_id is not None and not self.skills.get(skill_id):
            raise HTTPException(400, f"Skill {skill_id} does not exist")
        if job_id is not None and not self.jobs.get(job_id):
            raise HTTPException(400, f"Job {job_id} does not exist")
        if company_id is not None and not self.companies.get(company_id):
            raise HTTPException(400, f"Company {company_id} does not exist")

    # ---------------------------------------------------------------- admin write
    def create(self, admin, data: MaterialCreate) -> Material:
        self._check_refs(data.skill_id, data.job_id, data.company_id)
        return self.repo.add(Material(**data.model_dump(), created_by=admin.id))

    def upload(self, admin, filename: str, content: bytes, *, title: str, description: Optional[str],
               type_: Optional[str], skill_id, job_id, company_id, role, interview_round) -> Material:
        ext = Path(filename or "").suffix.lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(400, f"File type not allowed. Use: {', '.join(sorted(ALLOWED_EXT))}")
        if not content:
            raise HTTPException(400, "The file is empty")
        if len(content) > MAX_BYTES:
            raise HTTPException(413, "File is larger than 10 MB")
        type_ = (type_ or ("PDF" if ext == ".pdf" else "DOCUMENT")).strip().upper()
        if type_ not in MATERIAL_TYPES:
            raise HTTPException(400, f"type must be one of {', '.join(MATERIAL_TYPES)}")
        self._check_refs(skill_id, job_id, company_id)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        path = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        path.write_bytes(content)
        return self.repo.add(Material(title=title, description=description, type=type_, file_url=path.as_posix(),
                                      skill_id=skill_id, job_id=job_id, company_id=company_id, role=role,
                                      interview_round=interview_round, created_by=admin.id))

    def update(self, material_id: int, data: MaterialUpdate) -> Material:
        material = self.get(material_id)
        fields = data.model_dump(exclude_unset=True)
        for key in ("title", "type", "file_url"):               # NOT NULL columns
            if key in fields and fields[key] is None:
                fields.pop(key)
        self._check_refs(fields.get("skill_id"), fields.get("job_id"), fields.get("company_id"))
        for key, value in fields.items():
            setattr(material, key, value)
        self.repo.commit()
        self.repo.refresh(material)
        return material

    def delete(self, material_id: int) -> None:
        material = self.get(material_id)
        path = Path(material.file_url)
        if path.parent == UPLOAD_DIR:                           # only remove files WE stored
            path.unlink(missing_ok=True)
        self.repo.delete(material)

    # ---------------------------------------------------------------- read
    def get(self, material_id: int) -> Material:
        material = self.repo.get(material_id)
        if not material:
            raise NotFoundError("Material")
        return material

    def list(self, **filters):
        return self.repo.search(**filters)

    def for_job(self, job_id: int) -> list:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("Job")
        return self.repo.for_job(job.id, job.company_id, self.jobs.skill_ids(job.id))

    def local_file(self, material_id: int) -> Optional[Path]:
        """Path of an uploaded file, or None when the material is an external link."""
        material = self.get(material_id)
        path = Path(material.file_url)
        if path.parent != UPLOAD_DIR:
            return None
        resolved = path.resolve()
        if not resolved.is_file() or UPLOAD_DIR.resolve() not in resolved.parents:
            raise NotFoundError("File")
        return resolved

    # ---------------------------------------------------------------- bookmarks
    def bookmark(self, user, material_id: int) -> None:
        self.repo.add_bookmark(user.id, self.get(material_id).id)

    def unbookmark(self, user, material_id: int) -> None:
        obj = self.repo.get_bookmark(user.id, material_id)
        if not obj:
            raise NotFoundError("Bookmark")
        self.repo.remove_bookmark(obj)

    def bookmarked(self, user, skip: int, limit: int):
        return self.repo.bookmarked(user.id, skip, limit)
