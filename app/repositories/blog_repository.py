"""OWNER: M1 - DB access for blogs"""
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.blog import Blog


class BlogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, blog_id: int) -> Optional[Blog]:
        return self.db.get(Blog, blog_id)

    def get_by_slug(self, slug: str) -> Optional[Blog]:
        return self.db.query(Blog).filter(Blog.slug == slug).first()

    def slug_exists(self, slug: str) -> bool:
        return self.db.query(Blog.id).filter(Blog.slug == slug).first() is not None

    def add(self, obj: Blog) -> Blog:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj) -> None:
        self.db.refresh(obj)

    def delete(self, obj: Blog) -> None:
        self.db.delete(obj)
        self.db.commit()

    def search(self, *, published_only: bool, q: Optional[str] = None, category: Optional[str] = None,
               tag: Optional[str] = None, status: Optional[str] = None, skip: int = 0,
               limit: int = 20) -> Tuple[List[Blog], int]:
        query = self.db.query(Blog)
        if published_only:
            query = query.filter(Blog.status == "PUBLISHED")
        elif status:
            query = query.filter(Blog.status == status)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Blog.title.ilike(like), Blog.content.ilike(like)))
        if category:
            query = query.filter(func.lower(Blog.category) == category.lower())
        query = query.order_by(Blog.published_at.desc(), Blog.id.desc())
        if tag:   # tags are a JSON list, so filter in python (blog volumes are small)
            wanted = tag.strip().lower()
            rows = [b for b in query.all() if wanted in [str(t).lower() for t in (b.tags or [])]]
            return rows[skip:skip + limit], len(rows)
        return query.offset(skip).limit(limit).all(), query.count()
