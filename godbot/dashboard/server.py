"""
Dashboard Server (Phase 11.3)
------------------------------
Runs a Flask dashboard accessible via:
    http://localhost:8798
"""

from __future__ import annotations

import os
from flask import Flask
from waitress import serve

from godbot.dashboard.routes import register_routes
from godbot.core.logging import get_logger

log = get_logger(__name__)


def run_dashboard():
    """Start the Flask dashboard."""
    # Get the directory where this file is located
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(dashboard_dir, "templates")
    
    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=templates_dir,
    )

    register_routes(app)

    log.info("Starting Dashboard at http://localhost:8798")

    serve(app, host="0.0.0.0", port=8798)


if __name__ == "__main__":
    run_dashboard()

