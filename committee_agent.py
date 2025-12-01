# committee_agent.py
"""
Multi-Agent Committee V2
Each specialist agent votes.
The committee merges opinions and produces a final answer.
"""
import asyncio
from ollama_client import stream_ollama

class CommitteeAgent:
    def __init__(self, bot):
        self.bot = bot
        self.specialists = {
            "finance": None,
            "fitness": None,
            "wild_rift": None,
            "general": None,
        }
        # Auto-register specialists if they exist
        self._update_specialists()

    def _update_specialists(self):
        """Update specialist references from agent manager"""
        for name in self.specialists.keys():
            if name in self.bot.agent_manager.agents:
                self.specialists[name] = self.bot.agent_manager.agents[name]

    async def discuss(self, question: str):
        """Have specialist agents discuss and reach consensus"""
        self._update_specialists()
        
        tasks = []
        for name, agent in self.specialists.items():
            if agent:
                tasks.append(agent.run(self.bot, question))

        if not tasks:
            return {"consensus": "No agents available."}

        results = await asyncio.gather(*tasks)

        combined = "\n\n".join(
            [f"Agent {i+1} says:\n{res}" for i, res in enumerate(results)]
        )

        final_prompt = (
            "You are the arbiter agent. Combine these opinions into a single, "
            "clear, accurate answer. Avoid repetition.\n\n"
            f"{combined}\n\nFinal answer:"
        )

        final = ""
        async for chunk in stream_ollama(final_prompt, self.bot.current_model):
            c = chunk.get("response", "")
            if c:
                final += c

        return {"consensus": final.strip()}
