from app.core.dependencies import require_admin
from app.routers import blogs, interview_questions, materials, skills


def test_admin_content_write_routes_require_backend_admin_dependency():
    expected = {
        ("/skills", "POST"), ("/skills/{skill_id}", "PUT"), ("/skills/{skill_id}", "DELETE"),
        ("/interview-questions", "POST"), ("/interview-questions/{question_id}", "PUT"),
        ("/interview-questions/{question_id}", "DELETE"),
        ("/materials", "POST"), ("/materials/upload", "POST"),
        ("/materials/{material_id}", "PUT"), ("/materials/{material_id}", "DELETE"),
        ("/blogs", "POST"), ("/blogs/{blog_id}", "PUT"), ("/blogs/{blog_id}", "DELETE"),
    }
    routers = (skills.router, interview_questions.router, materials.router, blogs.router)
    routes = {(route.path, method): route for router in routers for route in router.routes
              if hasattr(route, "dependant") for method in route.methods}

    assert expected <= routes.keys()
    for key in expected:
        route = routes[key]
        assert any(dependency.call is require_admin for dependency in route.dependant.dependencies), key
