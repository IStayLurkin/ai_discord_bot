# godbot/discord/bot.py
"""
Discord bot client implementation
"""
import discord
from discord import app_commands
import asyncio

from godbot.core.memory import MemoryDB
from godbot.core.vector_memory import VectorMemory
from godbot.core.llm import stream_response
from plugins.plugin_manager import SuperPluginManager
from agents import AgentManager
from research_agent import ResearchAgent
from committee_agent import CommitteeAgent
from optimizer import PerformanceOptimizer
from personality import PersonalityManager
import audio
import dashboard
from godbot.core.scheduler import Scheduler
import scheduled_tasks.memory_cleanup as task_memory_cleanup
import scheduled_tasks.plugin_autoreload as task_plugin_reload
import scheduled_tasks.daily_report as task_daily_report
import scheduled_tasks.ping_test as task_ping_test


class MyClient(discord.Client):
    def __init__(self, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.current_model = "dolphin-llama3:latest"  # Fast and reliable
        self.long_memory = MemoryDB("long_memory.db")
        # Tools now handled via deterministic registry
        # Stub for backward compatibility
        class ToolStub:
            def list_schemas(self):
                return []
            def call_tool(self, name, args):
                return None
        self.tools = ToolStub()
        self.plugins = SuperPluginManager()
        self.vector_memory = VectorMemory()
        self.agent_manager = AgentManager()
        self.research_agent = ResearchAgent(self)
        self.committee_agent = CommitteeAgent(self)
        self.optimizer = PerformanceOptimizer(self)
        self.personality = PersonalityManager()
        self.voice_agent = audio.VoiceAgent(self)
        self.scheduler = Scheduler(self)
        self.dashboard_config = {}  # For storing config like report_channel_id

    async def setup_hook(self):
        await self.tree.sync()
        print("Discord slash commands synced.")
        dashboard.start_dashboard(self, port=5000)
        print("Dashboard running on http://localhost:5000")
        asyncio.create_task(self.autoupdater())
        
        # Register scheduled tasks (Phase 12)
        self.scheduler.add("heartbeat", 60, task_ping_test.ping_test)
        self.scheduler.add("plugin_reload", 30, task_plugin_reload.plugin_autoreload)
        self.scheduler.add("memory_cleanup", 1800, task_memory_cleanup.memory_cleanup)
        self.scheduler.add("daily_report", 86400, task_daily_report.daily_report)
        
        # Start scheduler
        asyncio.create_task(self.scheduler.start())

    async def autoupdater(self):
        while True:
            await asyncio.sleep(3600)
            self.plugins.auto_update()

    async def stream(self, prompt):
        """Stream method for agents to use"""
        async for chunk in stream_response(prompt, self.current_model):
            yield chunk

    async def direct_agent_call(self, prompt):
        # Format prompt like the agent wrapper for consistency
        agent_prompt = f"""You are God Bot, a helpful and intelligent AI assistant.

Your name is God Bot. You are friendly, knowledgeable, and respond naturally.

User: {prompt}
Assistant:"""
        
        full = ""
        async for chunk in stream_response(agent_prompt, self.current_model):
            txt = chunk.get("response", "")
            if txt:
                full += txt
        
        return full if full.strip() else "(no response)"


def create_client(intents: discord.Intents) -> MyClient:
    """Create and return a configured Discord client"""
    return MyClient(intents)

