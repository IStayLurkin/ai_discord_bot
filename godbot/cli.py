#!/usr/bin/env python3

"""
GodBot CLI — Phase 11.6
----------------------------------------------
Commands:
    godbot start
    godbot stop
    godbot dashboard
    godbot plugins
    godbot logs
    godbot llm-info
    godbot generate-image
    godbot generate-video
    godbot doctor
    godbot config
----------------------------------------------
Framework-level command interface for GodBot.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from godbot.core.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------
# Bot Runner
# ---------------------------------------------------------------

def cmd_start(args):
    """Start the Discord bot."""
    log.info("CLI: starting Discord bot")
    try:
        from godbot.bot import main as bot_main
        bot_main()
    except Exception as e:
        log.error(f"Failed to start: {e}", exc_info=True)
        print("Bot failed to start.")


def cmd_stop(args):
    """Stop the bot (no-op for now)."""
    print("There is no daemon-mode yet; use CTRL+C to stop the running bot.")


# ---------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------

def cmd_dashboard(args):
    """Run Flask dashboard."""
    log.info("CLI: launching dashboard")
    from godbot.dashboard.server import run_dashboard

    run_dashboard()


# ---------------------------------------------------------------
# Plugin System
# ---------------------------------------------------------------

def cmd_plugins(args):
    """Show discovered and loaded plugins."""
    from godbot.plugins.loader import plugin_manager

    discovered = plugin_manager.discover_plugins()
    loaded = plugin_manager.loaded_plugins.keys()

    print("Discovered Plugins:")
    for x in discovered:
        print("  -", x)

    print("\nLoaded Plugins:")
    for x in loaded:
        print("  -", x)


# ---------------------------------------------------------------
# Logs
# ---------------------------------------------------------------

def cmd_logs(args):
    """Print the latest log lines."""
    if not os.path.exists("logs/bot.log"):
        print("No logs found.")
        return

    with open("logs/bot.log", "r", encoding="utf-8") as f:
        lines = f.readlines()[-50:]

    print("".join(lines))


# ---------------------------------------------------------------
# LLM Info
# ---------------------------------------------------------------

def cmd_llm_info(args):
    from godbot.core.llm import llm
    info = llm.info()
    print(json.dumps(info, indent=4))


# ---------------------------------------------------------------
# Image / Video Generation Hooks
# (Implemented in Phase 11.9)
# ---------------------------------------------------------------

def cmd_generate_image(args):
    from godbot.generation.engine import generation_engine
    prompt = args.prompt
    out = generation_engine.generate_image(prompt)
    print("Generated:", out)


def cmd_generate_video(args):
    from godbot.generation.engine import generation_engine
    prompt = args.prompt
    out = generation_engine.generate_video(prompt)
    print("Generated:", out)


# ---------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------

def cmd_doctor(args):
    print("Running GodBot diagnostics...\n")
    print(f"Python: {sys.version}")
    print(f"Working Dir: {os.getcwd()}")
    print(f"Env file exists: {os.path.exists('.env')}")
    print("\nDone.")


# ---------------------------------------------------------------
# Config
# ---------------------------------------------------------------

def cmd_config(args):
    print("GodBot Configuration Paths:")
    print("--------------------------")
    print("Project root:", os.getcwd())
    print("Data:", os.path.abspath("data"))
    print("Wild Rift builds:", os.path.abspath("data/wild_rift_builds"))
    print("Logs:", os.path.abspath("logs"))
    print("Jobs:", os.path.abspath("jobs.json"))


# ---------------------------------------------------------------
# Main CLI Entry
# ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="godbot",
        description="GodBot CLI — Modular AI Discord Bot Platform",
    )

    sub = parser.add_subparsers(dest="command")

    # Bot
    sub.add_parser("start")
    sub.add_parser("stop")

    # Dashboard
    sub.add_parser("dashboard")

    # Plugins
    sub.add_parser("plugins")

    # Logs
    sub.add_parser("logs")

    # LLM
    sub.add_parser("llm-info")

    # Generation
    gen_i = sub.add_parser("generate-image")
    gen_i.add_argument("prompt")

    gen_v = sub.add_parser("generate-video")
    gen_v.add_argument("prompt")

    # Tools
    sub.add_parser("doctor")
    sub.add_parser("config")

    args = parser.parse_args()

    # 3.10 compatible routing
    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "plugins":
        cmd_plugins(args)
    elif args.command == "logs":
        cmd_logs(args)
    elif args.command == "llm-info":
        cmd_llm_info(args)
    elif args.command == "generate-image":
        cmd_generate_image(args)
    elif args.command == "generate-video":
        cmd_generate_video(args)
    elif args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "config":
        cmd_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
