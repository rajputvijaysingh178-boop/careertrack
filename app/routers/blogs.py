"""OWNER: M1 - blogs (everyone reads PUBLISHED posts, admin writes and sees drafts)"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_optional_user, require_admin
from app.schemas.blog import BlogCreate, BlogOut, BlogPage, BlogUpdate
from app.services.blog_service import BlogService

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("/ping")
def ping():
    return {"module": "blogs", "status": "ok"}


@router.get("", response_model=BlogPage)
def list_blogs(q: Optional[str] = None, category: Optional[str] = None, tag: Optional[str] = None,
               status: Optional[str] = Query(None, description="admin only: DRAFT / PUBLISHED"),
               skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db), user=Depends(get_optional_user)):
    items, total = BlogService(db).list(user, q, category, tag, status, skip, limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=BlogOut, status_code=201)
def create_blog(data: BlogCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return BlogService(db).create(admin, data)


@router.get("/{slug}", response_model=BlogOut)
def get_blog(slug: str, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    return BlogService(db).get_by_slug(user, slug)


@router.put("/{blog_id}", response_model=BlogOut)
def update_blog(blog_id: int, data: BlogUpdate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return BlogService(db).update(blog_id, data)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(blog_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    BlogService(db).delete(blog_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
