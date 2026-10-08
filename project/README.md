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
