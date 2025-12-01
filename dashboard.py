# dashboard.py
import os
import threading
import queue
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Try to import waitress for production server, fallback to development if not available
try:
    from waitress import serve
    WAITRESS_AVAILABLE = True
except ImportError:
    WAITRESS_AVAILABLE = False
    print("WARNING: waitress not installed. Using development server. Install with: pip install waitress")

LOG_QUEUE = queue.Queue()
MODEL_CACHE = []

def start_dashboard(bot, port=5000):
    app = Flask(__name__, static_folder="dashboard/ui")
    CORS(app)

    # Expose bot inside dashboard routes
    app.bot = bot

    # Get the directory where this file is located
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UI_DIR = os.path.join(BASE_DIR, "dashboard", "ui")

    # -----------------------------
    # INDEX HTML
    # -----------------------------
    @app.route("/")
    def index():
        return send_from_directory(UI_DIR, "index.html")

    # -----------------------------
    # STATIC FILES
    # -----------------------------
    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory(UI_DIR, filename)

    # -----------------------------
    # MODEL LIST + SWITCH
    # -----------------------------
    @app.route("/models", methods=["GET"])
    def list_models():
        import requests
        try:
            r = requests.get("http://localhost:11434/api/tags")
            data = r.json().get("models", [])
            names = [m["name"] for m in data]
            return jsonify(names)
        except:
            return jsonify([])

    @app.route("/set_model", methods=["POST"])
    def set_model():
        model = request.json.get("model")
        app.bot.current_model = model
        return jsonify({"status": "ok", "new_model": model})

    # -----------------------------
    # MEMORY VIEWER
    # -----------------------------
    @app.route("/memory", methods=["GET"])
    def view_memory():
        from main import load_memory
        mem = load_memory()
        return jsonify(mem)

    @app.route("/memory", methods=["POST"])
    def update_memory():
        from main import save_memory
        new_mem = request.json
        save_memory(new_mem)
        return jsonify({"status": "saved"})

    # -----------------------------
    # LONG MEMORY (DB)
    # -----------------------------
    @app.route("/long_memory", methods=["GET"])
    def long_memory():
        user = request.args.get("user")
        if not user:
            return jsonify({})
        rows = app.bot.long_memory.get_recent(user, limit=50)
        return jsonify(rows)

    # -----------------------------
    # PLUGIN MANAGER
    # -----------------------------
    @app.route("/plugins", methods=["GET"])
    def plugins_list():
        out = []
        for name, plugin in app.bot.plugins.plugins.items():
            out.append({
                "name": name,
                "folder": plugin.folder,
                "behavior": plugin.behavior_injection or "None",
                "loaded": True,
            })
        return jsonify(out)

    @app.route("/plugins/reload", methods=["POST"])
    def plugin_reload():
        name = request.json.get("name")
        if name in app.bot.plugins.plugins:
            app.bot.plugins.reload_plugin(app.bot.plugins.plugins[name])
            return jsonify({"status": "reloaded"})
        return jsonify({"error": "not found"})

    # -----------------------------
    # AGENT MANAGER
    # -----------------------------
    @app.route("/agents", methods=["GET"])
    def list_agents():
        agent_list = app.bot.agent_manager.list()
        # Format as objects with name and model
        out = []
        for name in agent_list:
            agent = app.bot.agent_manager.agents.get(name)
            if agent:
                out.append({
                    "name": agent.name,
                    "model": agent.model
                })
        return jsonify(out)

    @app.route("/agents/create", methods=["POST"])
    def create_agent():
        data = request.json
        app.bot.agent_manager.create(data["name"], data["model"])
        return jsonify({"status": "spawned"})

    @app.route("/agents/kill", methods=["POST"])
    def kill_agent():
        data = request.json
        app.bot.agent_manager.kill(data["name"])
        return jsonify({"status": "killed"})

    # -----------------------------
    # VOICE CONTROLS
    # -----------------------------
    @app.route("/voice/enable", methods=["POST"])
    def voice_enable():
        app.bot.voice_agent.enabled = True
        return jsonify({"status": "voice_on"})

    @app.route("/voice/disable", methods=["POST"])
    def voice_disable():
        app.bot.voice_agent.enabled = False
        return jsonify({"status": "voice_off"})

    @app.route("/voice/status", methods=["GET"])
    def voice_status():
        return jsonify({
            "enabled": app.bot.voice_agent.enabled,
            "listening": getattr(app.bot.voice_agent, "listening", False)
        })

    # -----------------------------
    # LIVE LOG STREAM
    # -----------------------------
    @app.route("/logs", methods=["GET"])
    def stream_logs():
        try:
            logs = []
            while not LOG_QUEUE.empty():
                logs.append(LOG_QUEUE.get())
            return jsonify(logs)
        except:
            return jsonify([])

    # -----------------------------
    # STATUS
    # -----------------------------
    @app.route("/status", methods=["GET"])
    def status():
        return jsonify({
            "status": "ok",
            "model": app.bot.current_model,
            "voice_enabled": app.bot.voice_agent.enabled
        })

    # Background Flask thread
    def run():
        if WAITRESS_AVAILABLE:
            serve(app, host="0.0.0.0", port=port, threads=4, channel_timeout=120)
        else:
            app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"Dashboard running on http://localhost:{port} ({'Production server (waitress)' if WAITRESS_AVAILABLE else 'Development server'})")
    return app
