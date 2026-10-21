"""OWNER: M1 - master skills list (everyone reads, admin writes)"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas.skill import SkillBulk, SkillCreate, SkillOut, SkillUpdate
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/ping")
def ping():
    return {"module": "skills", "status": "ok"}


@router.get("", response_model=List[SkillOut])
def list_skills(q: Optional[str] = None, category: Optional[str] = None, skip: int = Query(0, ge=0),
                limit: int = Query(200, ge=1, le=500), db: Session = Depends(get_db)):
    items, _ = SkillService(db).list(q, category, skip, limit)
    return items


@router.get("/categories", response_model=List[str])
def skill_categories(db: Session = Depends(get_db)):
    return SkillService(db).categories()


@router.post("", response_model=SkillOut, status_code=201)
def create_skill(data: SkillCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return SkillService(db).create(data)


@router.post("/bulk")
def bulk_create_skills(data: SkillBulk, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return SkillService(db).bulk_create(data)


@router.put("/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: int, data: SkillUpdate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return SkillService(db).update(skill_id, data)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    SkillService(db).delete(skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
