"""OWNER: M3 - prompt templates (plain str.replace so JSON braces are safe)."""

SYSTEM_JSON = "You are a careful assistant. Reply with ONE valid JSON object only, no markdown, no commentary."

_JD = """Analyze this job description. Return JSON exactly like:
{"skills":[{"name":"Python","importance":"REQUIRED"}],
 "experience":{"min":1,"max":3},
 "responsibilities":["..."],
 "tools":["..."],
 "interview_topics":[{"skill":"Python","topics":["Decorators"]}]}
importance must be REQUIRED, PREFERRED or OPTIONAL.

JOB DESCRIPTION:
<<JD>>"""

_PLAN = """Create a <<DAYS>>-day interview preparation plan for the role "<<ROLE>>".
Skills to cover (most important first): <<SKILLS>>.
The last day must be a mock interview. Return JSON exactly like:
{"days":[{"day":1,"title":"Python fundamentals","topics":["OOP","Decorators"],"tasks":["Revise OOP","Solve 5 questions"]}]}"""


def jd_analysis_prompt(jd: str) -> str:
    return _JD.replace("<<JD>>", jd[:8000])


def prep_plan_prompt(skills, days: int, role: str) -> str:
    return (_PLAN.replace("<<DAYS>>", str(days)).replace("<<ROLE>>", role or "the target role")
            .replace("<<SKILLS>>", ", ".join(skills)))
