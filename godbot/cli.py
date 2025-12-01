#!/usr/bin/env python3

"""
godbot CLI

Commands:
    godbot start
    godbot doctor
    godbot version
    godbot config
"""

import argparse
import os
import sys


def cmd_start(args):
    """Start the Discord bot."""
    print("Starting GodBot...")
    try:
        from godbot.bot import main as bot_main
        bot_main()
    except Exception as e:
        print("Failed to start GodBot:", e)
        sys.exit(1)


def cmd_version(args):
    print("GodBot version 0.1.0")


def cmd_doctor(args):
    print("Running diagnostics...\n")

    print(f"Python Version: {sys.version}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Environment File: {os.path.abspath('.env')}")

    # Check discord token
    token = os.getenv("DISCORD_TOKEN")
    print(f"DISCORD_TOKEN present: {token is not None}")

    print("\nDiagnostics complete.")


def cmd_config(args):
    print("GodBot Configuration Paths")
    print("--------------------------")
    print("Project root:", os.getcwd())
    print("Data directory:", os.path.abspath("data"))
    print("Wild Rift builds:", os.path.abspath("data/wild_rift_builds"))


def main():
    parser = argparse.ArgumentParser(
        prog="godbot",
        description="GodBot CLI — Modular AI Discord Bot Platform",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Create subcommands
    start = subparsers.add_parser("start")
    doctor = subparsers.add_parser("doctor")
    version = subparsers.add_parser("version")
    config = subparsers.add_parser("config")

    args = parser.parse_args()

    # Python 3.10 compatible (no match-case)
    if args.command == "start":
        cmd_start(args)
    elif args.command == "doctor":
        cmd_doctor(args)
    elif args.command == "version":
        cmd_version(args)
    elif args.command == "config":
        cmd_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
