"""
Performance Optimizer
Streaming, context management, and memory optimization
"""
import asyncio
from ollama_client import stream_ollama

class PerformanceOptimizer:
    def __init__(self, bot):
        self.bot = bot
        self.stream_buffer_size = 50  # Characters before updating Discord
        self.max_context_length = 4000  # Max context tokens
        self.memory_compression = True
    
    async def optimized_stream(self, prompt, model, interaction_msg, tools=None):
        """
        Optimized streaming with better update frequency
        """
        full_text = ""
        last_update_len = 0
        
        async for data in stream_ollama(prompt, model, tools):
            if "response" in data:
                chunk = data["response"]
                full_text += chunk
                
                # Update Discord message at optimal intervals
                if len(full_text) - last_update_len >= self.stream_buffer_size:
                    # Limit to Discord's 2000 char limit
                    display_text = full_text[:2000]
                    if len(full_text) > 2000:
                        display_text += f"\n\n... ({len(full_text) - 2000} more characters)"
                    
                    await interaction_msg.edit(content=display_text)
                    last_update_len = len(full_text)
        
        # Final update
        final_text = full_text[:2000]
        if len(full_text) > 2000:
            final_text += f"\n\n... ({len(full_text) - 2000} more characters truncated)"
        await interaction_msg.edit(content=final_text)
        
        return full_text
    
    def compress_context(self, context, max_length=None):
        """
        Compress context by removing less important parts
        """
        if max_length is None:
            max_length = self.max_context_length
        
        if len(context) <= max_length:
            return context
        
        # Simple compression: keep first and last parts
        half = max_length // 2
        compressed = context[:half] + "\n\n[... context compressed ...]\n\n" + context[-half:]
        return compressed
    
    def optimize_memory_injection(self, memories, max_items=5):
        """
        Optimize which memories to inject
        """
        if not memories:
            return []
        
        # Return most recent and most relevant
        return memories[-max_items:]
    
    def estimate_tokens(self, text):
        """
        Rough token estimation (4 chars ≈ 1 token)
        """
        return len(text) // 4

