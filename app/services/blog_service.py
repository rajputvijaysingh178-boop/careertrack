"""OWNER: M1
Responsibility: blogs (slug generation, publish, public vs admin visibility).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.dependencies import is_admin
from app.core.exceptions import DuplicateError, NotFoundError
from app.core.text_utils import slugify, unique_slug
from app.models.blog import Blog
from app.repositories.blog_repository import BlogRepository
from app.schemas.blog import BlogCreate, BlogUpdate


def _clean_tags(tags) -> list:
    seen, out = set(), []
    for t in tags or []:
        t = str(t).strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


class BlogService:
    def __init__(self, db: Session):
        self.repo = BlogRepository(db)

    def list(self, user, q: Optional[str], category: Optional[str], tag: Optional[str],
             status: Optional[str], skip: int, limit: int):
        admin = is_admin(user)
        return self.repo.search(published_only=not admin, q=q, category=category, tag=tag,
                                status=status.upper() if (admin and status) else None, skip=skip, limit=limit)

    def get_by_slug(self, user, slug: str) -> Blog:
        blog = self.repo.get_by_slug(slug)
        if not blog or (blog.status != "PUBLISHED" and not is_admin(user)):
            raise NotFoundError("Blog")
        return blog

    def create(self, author, data: BlogCreate) -> Blog:
        if data.slug:
            slug = slugify(data.slug)
            if self.repo.slug_exists(slug):
                raise DuplicateError("This slug is already used")
        else:
            slug = unique_slug(slugify(data.title), self.repo.slug_exists)
        return self.repo.add(Blog(
            title=data.title.strip(), slug=slug, content=data.content, author_id=author.id,
            category=data.category, tags=_clean_tags(data.tags), status=data.status,
            published_at=datetime.now() if data.status == "PUBLISHED" else None))

    def update(self, blog_id: int, data: BlogUpdate) -> Blog:
        blog = self.repo.get(blog_id)
        if not blog:
            raise NotFoundError("Blog")
        fields = data.model_dump(exclude_unset=True)
        for key in ("title", "content", "status"):          # NOT NULL columns
            if key in fields and fields[key] is None:
                fields.pop(key)
        if "tags" in fields:
            fields["tags"] = _clean_tags(fields["tags"])
        if fields.get("status") == "PUBLISHED" and blog.published_at is None:
            blog.published_at = datetime.now()
        for key, value in fields.items():
            setattr(blog, key, value)
        self.repo.commit()
        self.repo.refresh(blog)
        return blog

    def delete(self, blog_id: int) -> None:
        blog = self.repo.get(blog_id)
        if not blog:
            raise NotFoundError("Blog")
        self.repo.delete(blog)
