"""
Dashboard Routes (Phase 11.3)
------------------------------
Defines all Flask routes for GodBot dashboard.
"""

from __future__ import annotations

import os
from flask import render_template, request

from godbot.core.logging import get_logger
from godbot.plugins.loader import plugin_manager
from godbot.generation.engine import generation_engine

log = get_logger(__name__)


def read_logs():
    if not os.path.exists("logs/bot.log"):
        return ["No logs found."]
    with open("logs/bot.log", "r", encoding="utf-8") as f:
        return f.read().splitlines()


def register_routes(app):
    # Serve generated files from output directory
    @app.route("/output/<path:filename>")
    def serve_output(filename):
        from flask import send_from_directory
        return send_from_directory("output", filename)
    
    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/status")
    def status():
        return render_template("status.html")

    @app.route("/logs")
    def logs():
        data = read_logs()
        return render_template("logs.html", logs=data)

    @app.route("/plugins")
    def plugins():
        loaded = plugin_manager.list_plugins()
        discovered = plugin_manager.discover_plugins()
        return render_template("plugins.html", loaded=loaded, discovered=discovered)

    @app.route("/commands")
    def commands():
        return render_template("commands.html")

    @app.route("/llm")
    def llm():
        return render_template("llm.html")

    @app.route("/generation", methods=["GET", "POST"])
    def generation():
        if request.method == "POST":
            prompt = request.form.get("prompt", "")
            seed = request.form.get("seed", "")
            mode = request.form.get("mode", "image")

            seed = int(seed) if seed.isdigit() else None

            if mode == "image":
                out = generation_engine.generate_image(prompt, seed=seed)
            else:
                out = generation_engine.generate_video(prompt, seed=seed)

            return render_template("generation.html", output=out, prompt=prompt)

        return render_template("generation.html")

