"""
GodBot main entry point for CLI usage
"""
import os
import sys
import discord
from discord import app_commands
import asyncio

from discord.ext import commands

from godbot.core.memory import MemoryDB
from godbot.core.vector_memory import VectorMemory
from godbot.core.llm import llm
from godbot.core.scheduler import scheduler
from godbot.core.logging import get_logger
from godbot.plugins.loader import plugin_manager

# Legacy imports (still supported)
from plugins.plugin_manager import SuperPluginManager
from agents import AgentManager
from research_agent import ResearchAgent
from committee_agent import CommitteeAgent
from optimizer import PerformanceOptimizer
from personality import PersonalityManager
import audio
import dashboard

log = get_logger(__name__)


class MyClient(commands.Bot):
    """Discord bot client (Phase 11 architecture, corrected for slash commands)"""

    def __init__(self, intents: discord.Intents):
        super().__init__(command_prefix="", intents=intents)  # empty prefix, safest

        # self.tree is already created by commands.Bot
        self.current_model = "dolphin-llama3:latest"
        self.long_memory = MemoryDB("long_memory.db")


        # Tools stub for backward compatibility
        class ToolStub:
            def list_schemas(self):
                return []
            def call_tool(self, name, args):
                return None

        self.tools = ToolStub()

        # Legacy systems
        self.plugins = SuperPluginManager()
        self.vector_memory = VectorMemory()
        self.agent_manager = AgentManager()
        self.research_agent = ResearchAgent(self)
        self.committee_agent = CommitteeAgent(self)
        self.optimizer = PerformanceOptimizer(self)
        self.personality = PersonalityManager()
        self.voice_agent = audio.VoiceAgent(self)

        # Phase 11.5 global scheduler
        self.dashboard_config = {}

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        log.info("Discord slash commands synced.")

        # Start dashboard
        dashboard.start_dashboard(self, port=5000)
        log.info("Dashboard running on http://localhost:5000")

        # Autoupdate loop
        asyncio.create_task(self.autoupdater())

        # Auto-load plugins
        discovered = plugin_manager.discover_plugins()
        for module_name in discovered:
            plugin_manager.load_plugin(module_name, self)
        log.info(f"Plugins loaded: {plugin_manager.list_plugins()}")

        # Load generation-based commands
        from godbot.commands.generation import setup as setup_generation
        await setup_generation(self)

        # Start scheduler engine (global)
        scheduler.start()

    async def autoupdater(self):
        while True:
            await asyncio.sleep(3600)
            self.plugins.auto_update()
    async def on_message(self, message):
        return  # ignore classic messages entirely

    async def stream(self, prompt):
        """Streaming interface for agents (placeholder)"""
        response = llm.complete(prompt)
        yield {"response": response}

    async def direct_agent_call(self, prompt):
        agent_prompt = f"""You are God Bot, a helpful and intelligent AI assistant.
Your name is God Bot.

User: {prompt}
Assistant:"""

        full = llm.complete(agent_prompt)
        return full if full.strip() else "(no response)"


def create_client(intents: discord.Intents) -> MyClient:
    """Create and return the bot instance"""
    return MyClient(intents)


def main():
    """Start the Discord bot."""
    from dotenv import load_dotenv

    log.info("Starting Discord bot...")

    # Load .env
    load_dotenv()

    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        log.error("DISCORD_TOKEN missing in environment.")
        sys.exit(1)

    # Force-load deterministic tools
    import deterministic.math_tools
    import deterministic.finance_tools
    import deterministic.fitness_tools
    import deterministic.nutrition_tools
    import deterministic.wildrift_tools

    # Intents setup
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    # Create bot
    client = create_client(intents)

    # Register modular slash commands
    from godbot.discord.commands import (
        register_finance_commands,
        register_wildrift_commands,
    )
    from godbot.commands.plugins import register_plugin_commands

    register_finance_commands(client)
    register_wildrift_commands(client)
    register_plugin_commands(client)

    # Run the bot
    try:
        client.run(TOKEN)
    except Exception as e:
        log.error(f"Bot crashed: {e}", exc_info=True)
        raise
