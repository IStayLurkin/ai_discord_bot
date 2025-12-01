# agents.py
from ollama_client import stream_ollama
import asyncio

class BaseAgent:
    def __init__(self, name, system_prompt, model=None):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model

    async def run(self, bot, prompt):
        full_prompt = f"{self.system_prompt}\n\nUser: {prompt}\nAgent:"
        text = ""
        model = self.model or bot.current_model
        async for chunk in stream_ollama(full_prompt, model):
            resp = chunk.get("response", "")
            if resp:
                text += resp
        return text.strip()

class SpecialistAgent(BaseAgent):
    """For Finance, Fitness, Wild Rift, Nutrition, etc."""
    pass

class AgentManager:
    def __init__(self):
        self.agents = {}

    def create(self, name, model):
        system_prompt = f"You are {name}, a specialist agent."
        self.agents[name] = BaseAgent(name, system_prompt, model)

    def list(self):
        out = []
        for name, agent in self.agents.items():
            out.append({
                "name": name,
                "model": agent.model or "default"
            })
        return out

    def kill(self, name):
        if name in self.agents:
            del self.agents[name]
