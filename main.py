"""
Main bootstrap for running GodBot directly.

Preferred usage is via:
    godbot start

This file simply loads the Discord bot and initializes
all modules according to the new Phase 11 architecture.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

from godbot.bot import create_client
from godbot.core.logging import get_logger

log = get_logger(__name__)

# Load environment variables
load_dotenv()

# Force import of deterministic tool modules so they register
import deterministic.math_tools
import deterministic.finance_tools
import deterministic.fitness_tools
import deterministic.nutrition_tools
import deterministic.wildrift_tools

# Import command registration functions
from godbot.discord.commands import (
    register_finance_commands,
    register_wildrift_commands,
)
from godbot.commands.plugins import register_plugin_commands

if __name__ == "__main__":
    log.info("Launching GodBot via main.py (direct mode)")
    
    # Get Discord token
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        log.error("DISCORD_TOKEN not found in environment. Create a .env file with DISCORD_TOKEN=your_token")
        sys.exit(1)
    
    # Create intents
    import discord
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    
    # Create client
    client = create_client(intents)
    
    # Register modular slash commands
    register_finance_commands(client)
    register_wildrift_commands(client)
    register_plugin_commands(client)
    
    try:
        # Run the bot
        client.run(TOKEN)
    except Exception as e:
        log.error(f"GodBot failed to launch: {e}", exc_info=True)
        raise
