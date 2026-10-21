"""OWNER: M1 - study materials (logged-in users read + bookmark, admin writes)"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.schemas.material import MaterialCreate, MaterialOut, MaterialPage, MaterialUpdate
from app.services.material_service import MAX_BYTES, MaterialService

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/ping")
def ping():
    return {"module": "materials", "status": "ok"}


@router.get("", response_model=MaterialPage)
def list_materials(q: Optional[str] = None, type: Optional[str] = None, skill_id: Optional[int] = None,
                   job_id: Optional[int] = None, company_id: Optional[int] = None, role: Optional[str] = None,
                   interview_round: Optional[str] = None, skip: int = Query(0, ge=0),
                   limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    items, total = MaterialService(db).list(q=q, type_=type.upper() if type else None, skill_id=skill_id,
                                            job_id=job_id, company_id=company_id, role=role,
                                            interview_round=interview_round, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/bookmarked", response_model=MaterialPage)
def my_bookmarked(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    items, total = MaterialService(db).bookmarked(user, skip, limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=MaterialOut, status_code=201)
def create_material(data: MaterialCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Attach an external link (or any URL) as study material."""
    return MaterialService(db).create(admin, data)


@router.post("/upload", response_model=MaterialOut, status_code=201)
async def upload_material(file: UploadFile = File(...), title: str = Form(...),
                          description: Optional[str] = Form(None), type: Optional[str] = Form(None),
                          skill_id: Optional[int] = Form(None), job_id: Optional[int] = Form(None),
                          company_id: Optional[int] = Form(None), role: Optional[str] = Form(None),
                          interview_round: Optional[str] = Form(None),
                          db: Session = Depends(get_db), admin=Depends(require_admin)):
    content = await file.read(MAX_BYTES + 1)
    return MaterialService(db).upload(admin, file.filename or "", content, title=title, description=description,
                                      type_=type, skill_id=skill_id, job_id=job_id, company_id=company_id,
                                      role=role, interview_round=interview_round)


@router.get("/{material_id}", response_model=MaterialOut)
def get_material(material_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return MaterialService(db).get(material_id)


@router.get("/{material_id}/download")
def download_material(material_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service = MaterialService(db)
    path = service.local_file(material_id)
    if path is None:                                  # external link -> send the browser there
        return RedirectResponse(service.get(material_id).file_url)
    return FileResponse(path, filename=service.get(material_id).title + path.suffix)


@router.put("/{material_id}", response_model=MaterialOut)
def update_material(material_id: int, data: MaterialUpdate, db: Session = Depends(get_db),
                    admin=Depends(require_admin)):
    return MaterialService(db).update(material_id, data)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(material_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    MaterialService(db).delete(material_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{material_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def bookmark_material(material_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    MaterialService(db).bookmark(user, material_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{material_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def unbookmark_material(material_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    MaterialService(db).unbookmark(user, material_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
