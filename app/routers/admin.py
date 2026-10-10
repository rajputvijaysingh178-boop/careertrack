"""OWNER: M1 - admin dashboard, reports and user management (ADMIN only)"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.schemas.user import AdminUserCreate, RoleChange, StatusChangeUser, UserOut
from app.services.admin_service import AdminService
from app.services.job_service import JobService
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping():
    return {"module": "admin", "status": "ok"}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Total jobs, active jobs, applications, users, interviews tracked, offers recorded ..."""
    return AdminService(db).dashboard()


@router.get("/reports")
def reports(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return AdminService(db).reports()


@router.get("/users")
def list_users(q: Optional[str] = None, role: Optional[str] = None, status: Optional[str] = None,
               skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db), admin=Depends(require_admin)):
    items, total = UserService(db).admin_list(q, role, status, skip, limit)
    return {"items": [UserOut.model_validate(u).model_dump(mode="json") for u in items],
            "total": total, "skip": skip, "limit": limit}


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(data: AdminUserCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Create a USER or another ADMIN."""
    return UserService(db).admin_create(data)


@router.put("/users/{user_id}/status", response_model=UserOut)
def set_user_status(user_id: int, body: StatusChangeUser, db: Session = Depends(get_db),
                    admin=Depends(require_admin)):
    """Block / unblock an account."""
    return UserService(db).set_status(admin, user_id, body.status)


@router.put("/users/{user_id}/role", response_model=UserOut)
def set_user_role(user_id: int, body: RoleChange, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return UserService(db).set_role(admin, user_id, body.role)


@router.post("/jobs/run-maintenance")
def run_job_maintenance(db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Run the expiry task right now (normally it runs every hour)."""
    return JobService(db).run_maintenance()
