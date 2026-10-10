# Member 1 module: Job Board & Admin (the foundation)

## Install
Unzip INSIDE THE FOLDER THAT CONTAINS `careertrack/` (the zip root is `careertrack/`).
Files that are shared or already updated by others are NOT in this zip (`app/models/__init__.py`,
`app/core/database.py`, `app/core/exceptions.py`), so nothing of M2 / M3 gets overwritten.

1. `pip install -r requirements.txt`   (passlib was replaced by bcrypt; this file is updated)
2. Copy `.env.example` to `.env`, set SECRET_KEY, ADMIN_EMAIL and ADMIN_PASSWORD
3. DELETE the old `careertrack.db` file if you ran the empty scaffold before (tables changed)
4. `uvicorn app.main:app --reload`  then open http://127.0.0.1:8000/docs
5. Optional demo data (8 jobs, 5 companies, blogs, materials, 2 users):  `python -m scripts.seed_demo`

On startup the app creates the tables, fills the skills table, creates the admin from `.env`
and starts the scheduler (job expiry every hour; M2's reminders every minute once M2 is installed).

## Log in (Swagger)
POST /auth/login (username = email) or click "Authorize". Frontends can use POST /auth/login/json.

## Endpoints
| Area | Endpoints |
|---|---|
| Auth | POST /auth/register, /auth/login, /auth/login/json, GET /auth/me |
| Profile | GET/PUT /users/me, POST /users/me/password |
| Companies | GET /companies, /companies/{id} (public); POST/PUT/DELETE (admin) |
| Skills | GET /skills, /skills/categories; POST, POST /skills/bulk, PUT, DELETE (admin) |
| Jobs | GET /jobs (search + filters), GET /jobs/{id}; POST/PUT/DELETE, /publish, /unpublish, /expire, /close, /reopen, PUT /jobs/{id}/skills, POST /jobs/check-duplicate (admin); GET /jobs/{id}/materials |
| Blogs | GET /blogs, GET /blogs/{slug}; POST/PUT/DELETE (admin) |
| Materials | GET /materials, /materials/{id}, /materials/{id}/download, /materials/bookmarked; PUT/DELETE /materials/{id}/bookmark; POST, POST /materials/upload, PUT, DELETE (admin) |
| Admin | GET /admin/dashboard, /admin/reports, /admin/users; POST /admin/users; PUT /admin/users/{id}/status, /role; POST /admin/jobs/run-maintenance |

## Job search filters (GET /jobs)
q, location, work_mode, remote, experience (your years), salary_min / salary_max (LPA), employment_type,
job_type, company_id, skills (csv) + skills_match=any|all, posted_within_days, sort=newest|salary|expiring,
skip, limit. Visitors and users only see ACTIVE, non-expired jobs; admins see all and can filter by status.

## Rules implemented
- Job status: DRAFT -> ACTIVE (or PUBLISHED when posted_date is in the future) -> EXPIRED / CLOSED.
- Auto-expiry: `expiry_date < today` -> EXPIRED (hourly task + public search already hides expired jobs).
- Duplicate detection: same company + same title + similar JD returns 409 with `similar_jobs`; add `?force=true` to override.
- A job with applications cannot be deleted (409): close it; applications keep their own JD snapshot.
- Signup always creates a USER. Admins come from `.env`, `scripts/create_admin.py` or POST /admin/users.
- Unknown skill names used on a job are added to the skills table automatically.
- Salary is in LPA, experience in years.

## Contracts used by M2 and M3
Tables jobs, companies, skills, job_skills, materials, blogs and the columns named in `app/models/job.py`.
`get_current_user` / `require_admin` live in `app/core/dependencies.py`.
M3's `GET /jobs/{id}/interview-questions` is served as `GET /prep/jobs/{id}`.
