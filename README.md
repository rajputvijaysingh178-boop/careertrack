# CareerTrack

Job Application & Interview Preparation Platform (FastAPI).
Architecture: **Router -> Service -> Repository -> Database**

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs  (every module has a `/ping` endpoint)

Run tests: `pytest`

## Frontend
The job board, application tracker, M3 preparation tools, and admin workspace are
served at `/tracker/`.

## Environment and deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for required and optional settings, Neon PostgreSQL
configuration, CORS, file storage, AI configuration, and same-origin/split-host deployment notes.

## Application tracker database upgrade
Before using the M2 tracker APIs with an
older database created from the original placeholder models, run
`python -m scripts.migrate_m2_schema --apply` against a local SQLite copy first.
The migration is additive and refuses non-empty placeholder tracker tables; it
does not delete tables or records. Remote databases require the explicit
`--allow-remote` flag after a backup and target review.
Automatic schema creation is enabled by default only for SQLite. PostgreSQL deployments require an
explicit reviewed schema upgrade before tracker APIs are used; app startup will not alter PostgreSQL.

## Ownership
| Member | Scope |
|---|---|
| M1 | Auth, admin, companies, jobs, skills, search, blogs, materials, job expiry |
| M2 | Bookmarks, Apply & Track, state machine, timeline, interviews, notes, reminders, kanban, analytics |
| M3 | Interview questions, recommendations, JD analyzer, resume match, prep plan, skill gap |

Every file starts with an `OWNER:` line in its docstring.

## Git workflow
Branches `feature/m1-*`, `feature/m2-*`, `feature/m3-*` -> PR into `develop`.
M1 pushes core models (users, companies, jobs, skills) first.
