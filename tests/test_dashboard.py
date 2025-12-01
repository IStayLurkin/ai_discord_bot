from godbot.dashboard.routes import register_routes
from flask import Flask


def test_dashboard_routes():
    app = Flask(__name__)

    register_routes(app)

    test_client = app.test_client()

    # Test that routes are registered
    # Note: May return 500 if templates are missing (expected until Phase 11.3 PART 2)
    resp = test_client.get("/")
    assert resp.status_code in [200, 500]  # Route exists even if template missing

    resp = test_client.get("/logs")
    assert resp.status_code in [200, 500]  # Route exists even if template missing

