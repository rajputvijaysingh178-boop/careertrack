# Import every model so Base.metadata knows all tables (needed by Alembic / create_all)
from app.models.user import User  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.blog import Blog  # noqa: F401
from app.models.material import Material  # noqa: F401
from app.models.bookmark import Bookmark  # noqa: F401
from app.models.application import Application  # noqa: F401
from app.models.interview import Interview  # noqa: F401
from app.models.note import Note  # noqa: F401
from app.models.reminder import Reminder  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.interview_question import InterviewQuestion  # noqa: F401
from app.models.user_interview_question import UserInterviewQuestion  # noqa: F401
