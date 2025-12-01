"""
Auto-Research Agent
Multi-step planning and research capabilities
"""
from ollama_client import stream_ollama
import json
import asyncio

class ResearchAgent:
    def __init__(self, bot, max_steps=5):
        self.bot = bot
        self.max_steps = max_steps
    
    async def research(self, topic, depth="medium"):
        """
        Conduct multi-step research on a topic
        depth: "shallow", "medium", "deep"
        """
        steps = {
            "shallow": 2,
            "medium": 4,
            "deep": 6
        }.get(depth, 4)
        
        research_plan = await self._create_plan(topic, steps)
        results = []
        
        for i, step in enumerate(research_plan[:self.max_steps]):
            step_result = await self._execute_step(step, topic, i+1, len(research_plan))
            results.append(step_result)
            
            # Update plan based on findings
            if i < len(research_plan) - 1:
                research_plan = await self._refine_plan(research_plan, results, topic)
        
        # Synthesize final answer
        final_answer = await self._synthesize(results, topic)
        return final_answer
    
    async def _create_plan(self, topic, num_steps):
        """Create a research plan"""
        prompt = f"""Create a {num_steps}-step research plan for: {topic}

Return ONLY a JSON array of research steps, each step should be a clear question or task.
Example: ["What is X?", "What are the main components of X?", "What are recent developments in X?"]

JSON array:"""
        
        response = ""
        async for data in stream_ollama(prompt, self.bot.current_model):
            if "response" in data:
                response += data["response"]
        
        try:
            # Try to extract JSON from response
            json_match = None
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                json_str = response[start:end]
                json_match = json.loads(json_str)
            
            if json_match and isinstance(json_match, list):
                return json_match[:num_steps]
        except:
            pass
        
        # Fallback: generate simple plan
        return [f"Research {topic} - step {i+1}" for i in range(num_steps)]
    
    async def _execute_step(self, step, topic, step_num, total_steps):
        """Execute a single research step"""
        # Use web search tool
        from tools.tool_registry import ToolRegistry
        tools = ToolRegistry()
        
        # Search for information
        search_result = tools.call_tool("web_search", {"query": f"{topic} {step}"})
        
        # Analyze with LLM
        analysis_prompt = f"""Based on this research step: "{step}"
And search results: {search_result[:1000]}

Provide a concise summary (2-3 sentences) of key findings.
Summary:"""
        
        analysis = ""
        async for data in stream_ollama(analysis_prompt, self.bot.current_model):
            if "response" in data:
                analysis += data["response"]
        
        return {
            "step": step,
            "step_number": step_num,
            "search_results": search_result[:500],
            "analysis": analysis
        }
    
    async def _refine_plan(self, plan, results, topic):
        """Refine research plan based on findings"""
        # Simple implementation - could be enhanced
        return plan
    
    async def _synthesize(self, results, topic):
        """Synthesize all research results into final answer"""
        all_findings = "\n\n".join([
            f"Step {r['step_number']}: {r['step']}\n{r['analysis']}"
            for r in results
        ])
        
        synthesis_prompt = f"""Based on this research about "{topic}":

{all_findings}

Provide a comprehensive, well-structured answer synthesizing all findings.
Answer:"""
        
        final_answer = ""
        async for data in stream_ollama(synthesis_prompt, self.bot.current_model):
            if "response" in data:
                final_answer += data["response"]
        
        return final_answer

