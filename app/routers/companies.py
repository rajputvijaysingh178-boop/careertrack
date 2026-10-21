"""OWNER: M1 - companies (everyone reads, admin writes)"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_optional_user, require_admin
from app.schemas.company import CompanyCreate, CompanyOut, CompanyPage, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/ping")
def ping():
    return {"module": "companies", "status": "ok"}


@router.get("", response_model=CompanyPage)
def list_companies(q: Optional[str] = None, industry: Optional[str] = None, location: Optional[str] = None,
                   status: Optional[str] = Query(None, description="admin only: ACTIVE / INACTIVE"),
                   skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                   db: Session = Depends(get_db), user=Depends(get_optional_user)):
    return CompanyService(db).list(user, q, industry, location, status, skip, limit)


@router.post("", response_model=CompanyOut, status_code=201)
def create_company(data: CompanyCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return CompanyService(db).create(data)


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    return CompanyService(db).get(company_id, user)


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db),
                   admin=Depends(require_admin)):
    return CompanyService(db).update(company_id, data)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    CompanyService(db).delete(company_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
