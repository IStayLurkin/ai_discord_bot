import discord
from discord import app_commands
import asyncio
from ollama_client import stream_ollama
from godbot.core.llm import stream_response
from godbot.core.memory import MemoryDB
# ToolRegistry removed - using deterministic tools directly
from plugins.plugin_manager import SuperPluginManager
from godbot.core.vector_memory import VectorMemory
from agents import AgentManager
from research_agent import ResearchAgent
from committee_agent import CommitteeAgent
from optimizer import PerformanceOptimizer
from personality import PersonalityManager
import audio
import dashboard
import json
import logging
import warnings
import os
from dotenv import load_dotenv
from deterministic import try_deterministic_tools
from godbot.core.scheduler import Scheduler
import scheduled_tasks.memory_cleanup as task_memory_cleanup
import scheduled_tasks.plugin_autoreload as task_plugin_reload
import scheduled_tasks.daily_report as task_daily_report
import scheduled_tasks.ping_test as task_ping_test

# Deterministic tool imports (for handlers, not commands - commands are in godbot.discord.commands)

# Load environment variables from .env file
load_dotenv()

# Force import of tool modules so they register
import deterministic.math_tools
import deterministic.finance_tools
import deterministic.fitness_tools
import deterministic.nutrition_tools
import deterministic.wildrift_tools

# Suppress openwakeword tflite warning (harmless - it falls back to onnxruntime)
logging.getLogger("root").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*tflite.*")

# -----------------------------
# MEMORY.JSON SYSTEM
# -----------------------------
MEM_FILE = "memory.json"

def load_memory():
    """Load memory.json or create if doesn't exist"""
    if not os.path.exists(MEM_FILE):
        with open(MEM_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    with open(MEM_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def compress_history(history: list) -> str:
    """
    Summaries long conversation histories into ~800 chars.
    """
    text = ""
    for role, msg in history[-12:]:   # take only last 12 messages
        text += f"{role}: {msg}\n"

    if len(text) < 900:
        return text

    return "Summary: Conversation has involved topics such as " + ", ".join(
        set([msg.split(" ")[0] for role, msg in history[-12:] if msg])
    )

def clean_memory(mem):
    """Deduplicate and limit memory facts"""
    for user in mem:
        facts = mem[user].get("facts", [])
        # Deduplicate
        mem[user]["facts"] = list(dict.fromkeys(facts))[-20:]
    return mem

def save_memory(mem):
    """Save memory to memory.json"""
    mem = clean_memory(mem)
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=4)

# Load memory at startup
user_memory = load_memory()

def store_fact(user_id, text):
    """
    Simple rule-based memory extraction.
    Only stores stable facts like preferences, names, locations.
    """
    keywords = [
        "i like", "my name is", "i live", "i'm from",
        "i am ", "my favorite", "i prefer", "i love",
        "i hate", "i work", "my job", "i study",
        "my age is", "i'm ", "call me"
    ]
    
    lowered = text.lower()
    
    # Only store if it contains a fact-like keyword
    if any(k in lowered for k in keywords):
        uid = str(user_id)
        if uid not in user_memory:
            user_memory[uid] = {"facts": []}
        
        # Don't store duplicates
        if text not in user_memory[uid]["facts"]:
            # Keep facts short - truncate if needed
            fact = text[:200] if len(text) > 200 else text
            user_memory[uid]["facts"].append(fact)
            # Limit to 20 facts per user
            if len(user_memory[uid]["facts"]) > 20:
                user_memory[uid]["facts"] = user_memory[uid]["facts"][-20:]
            save_memory(user_memory)
            print(f"[MEMORY] Stored fact for {uid}: {fact[:50]}...")

def get_user_facts(user_id):
    """Get stored facts for a user"""
    uid = str(user_id)
    if uid in user_memory and user_memory[uid].get("facts"):
        return user_memory[uid]["facts"]
    return []

# Load token from environment variable
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment. Create a .env file with DISCORD_TOKEN=your_token")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

from godbot.discord.bot import create_client
from godbot.discord.commands import (
    register_finance_commands,
    register_wildrift_commands,
)
from godbot.commands.plugins import register_plugin_commands

client = create_client(intents)

# Register modular slash commands
register_finance_commands(client)
register_wildrift_commands(client)
register_plugin_commands(client)

async def run_agent(interaction, prompt):
    try:
        await interaction.response.defer()
        msg = await interaction.followup.send("Thinking...")
        
        user_id = str(interaction.user.id)
        
        # Get recent memory - ONLY user messages to prevent echo loops
        history = client.long_memory.get_recent(user_id, limit=10)
        contextual_prompt = ""
        # Only include user messages in context (not bot's own responses)
        user_messages = []
        for role, content in history:
            if role == "user":
                user_messages.append(content)
        
        # Only include last 3-4 user messages for context
        if user_messages:
            contextual_prompt = "Previous conversation:\n"
            for msg in user_messages[-4:]:
                contextual_prompt += f"- {msg}\n"
        
        # Get vector memory for better context
        try:
            related = client.vector_memory.search(prompt, 3)
            if related:
                contextual_prompt += "\nRelated topics:\n"
                for m in related[:2]:  # Limit to 2 related items
                    contextual_prompt += f"- {m[:100]}\n"
        except:
            pass  # Vector memory optional
        
        # Inject behavior plugins
        for behavior in client.plugins.behavior_injections:
            contextual_prompt = behavior + "\n" + contextual_prompt
        
        # Build agent prompt with tool schemas
        tool_schemas = client.tools.list_schemas()
        
        # Get interaction context
        server_name = interaction.guild.name if interaction.guild else "DM"
        channel_name = interaction.channel.name if hasattr(interaction.channel, 'name') else "DM"
        
        # Get personality system prompt
        personality_prompt = client.personality.get_system_prompt()
        context_summary = client.personality.get_context_summary(history, prompt)
        
        agent_prompt = f"""{personality_prompt}

Server: {server_name}
Channel: {channel_name}
User: {interaction.user.name}

CRITICAL INSTRUCTIONS:
- Do NOT rewrite, echo, or repeat previous messages
- Do NOT create bullet lists, conversation transcripts, or chat logs
- Do NOT include usernames or role labels (like "user:" or "assistant:") in your response
- ONLY respond directly to the user's current message
- Keep your response natural and conversational

If a tool is needed, respond in this JSON format ONLY:

{{
  "tool": "<tool_name>",
  "arguments": {{ ... }}
}}

Otherwise, answer normally.

{contextual_prompt if contextual_prompt else ""}
{interaction.user.name}: {prompt}
{client.personality.bot_name}:"""
        
        print(f"[DEBUG] Sending prompt to Ollama: {agent_prompt[:200]}...")
        print(f"[DEBUG] Model: {client.current_model}")
        
        full_text = ""
        last_update = 0
        chunk_count = 0
        error_msg = None
        
        async for data in stream_response(agent_prompt, client.current_model, tools=tool_schemas):
            # Check for errors from Ollama
            if "error" in data:
                error_msg = data["error"]
                print(f"[ERROR] Ollama error: {error_msg}")
                break
            
            chunk = data.get("response", "")
            if chunk:
                chunk_count += 1
                full_text += chunk
                # Optimize: Update every 50 chars instead of 30 for better performance
                if len(full_text) - last_update >= 50:
                    await msg.edit(content=full_text[:2000])  # Limit to 2000 chars for Discord
                    last_update = len(full_text)
        
        print(f"[DEBUG] Received {chunk_count} chunks, total length: {len(full_text)}")
        
        # Handle Ollama errors
        if error_msg:
            await msg.edit(content=f"❌ {error_msg}")
            return None
    
        # Attempt to parse JSON function call
        tool_call = None
        try:
            tool_call = json.loads(full_text)
        except:
            tool_call = None
        
        if isinstance(tool_call, dict) and "tool" in tool_call:
            tool_name = tool_call["tool"]
            args = tool_call.get("arguments", {})
            print(f"[DEBUG] Tool call detected: {tool_name}")
            result = client.tools.call_tool(tool_name, args)
            
            final_prompt = f"""
The tool '{tool_name}' returned this result:

{result}

Now respond to the user using this tool output:
"""
            final_text = ""
            async for data in stream_response(final_prompt, client.current_model):
                chunk = data.get("response", "")
                if chunk:
                    final_text += chunk
            
            await msg.edit(content=final_text[:2000])
            client.long_memory.save(user_id, "user", prompt)
            client.long_memory.save(user_id, "assistant", final_text)
            try:
                client.vector_memory.add(user_id, prompt)
                client.vector_memory.add(user_id, final_text)
            except:
                pass
            return final_text
        else:
            # Ensure we always send a response, even if empty
            if not full_text.strip():
                full_text = "(no response from model - check Ollama is running)"
            else:
                # Enhance response with personality
                full_text = client.personality.enhance_response(full_text)
            await msg.edit(content=full_text[:2000])
            client.long_memory.save(user_id, "user", prompt)
            client.long_memory.save(user_id, "assistant", full_text)
            try:
                client.vector_memory.add(user_id, prompt)
                client.vector_memory.add(user_id, full_text)
            except:
                pass
            return full_text
    except Exception as e:
        print(f"[ERROR] run_agent failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            await interaction.followup.send(f"Error: {str(e)}")
        except:
            pass
        return None

@client.tree.command(name="ask", description="Ask the agent (with tool-use).")
async def ask_cmd(interaction: discord.Interaction, prompt: str):
    try:
        response = await run_agent(interaction, prompt)
    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}")

@client.tree.command(name="research", description="Conduct deep research on a topic.")
async def research_cmd(interaction: discord.Interaction, topic: str, depth: str = "medium"):
    await interaction.response.defer()
    msg = await interaction.followup.send(f"Researching '{topic}'...")
    
    valid_depths = ["shallow", "medium", "deep"]
    if depth not in valid_depths:
        depth = "medium"
    
    try:
        result = await client.research_agent.research(topic, depth)
        final_text = f"**Research on: {topic}**\n\n{result}"
        if len(final_text) > 2000:
            final_text = final_text[:1997] + "..."
        await msg.edit(content=final_text)
    except Exception as e:
        await msg.edit(content=f"Research failed: {str(e)}")

@client.tree.command(name="committee", description="Have multiple agents discuss a question.")
async def committee_cmd(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    msg = await interaction.followup.send("Forming committee...")
    
    try:
        result = await client.committee_agent.discuss(question)
        consensus = result["consensus"]
        if len(consensus) > 2000:
            consensus = consensus[:1997] + "..."
        await msg.edit(content=f"**Committee Discussion:**\n\n{consensus}")
    except Exception as e:
        await msg.edit(content=f"Committee discussion failed: {str(e)}")

@client.tree.command(name="committee2", description="Committee V2 analysis")
async def committee2_cmd(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    result = await client.committee_agent.discuss(question)
    await interaction.followup.send(result["consensus"][:2000])

async def model_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for available Ollama models"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            # Filter by what user has typed
            filtered = [m for m in model_names if current.lower() in m.lower()]
            # Return top 25 matches (Discord limit)
            return [app_commands.Choice(name=m, value=m) for m in filtered[:25]]
    except:
        pass
    return []

@client.tree.command(name="setmodel", description="Switch Ollama model.")
@app_commands.autocomplete(model=model_autocomplete)
async def setmodel_cmd(interaction: discord.Interaction, model: str):
    client.current_model = model
    await interaction.response.send_message(f"✅ Model changed to **{model}**")

@client.tree.command(name="models", description="List available Ollama models.")
async def models_cmd(interaction: discord.Interaction):
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                current = client.current_model
                lines = [f"**Available Models:** (current: `{current}`)\n"]
                for m in models[:20]:  # Limit to 20
                    name = m["name"]
                    size = m.get("size", 0) / (1024**3)  # Convert to GB
                    marker = "→ " if name == current else "  "
                    lines.append(f"`{marker}{name}` ({size:.1f} GB)")
                await interaction.response.send_message("\n".join(lines))
            else:
                await interaction.response.send_message("No models found. Run `ollama pull <model>` to download one.")
        else:
            await interaction.response.send_message("❌ Could not connect to Ollama.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}")

@client.tree.command(name="plugins_list", description="List installed plugins.")
async def plugins_list(interaction: discord.Interaction):
    out = client.plugins.list_plugins()
    await interaction.response.send_message("\n".join(map(str, out)) or "No plugins installed.")

@client.tree.command(name="plugin_install", description="Install plugin from local folder.")
async def plugin_install(interaction: discord.Interaction, folder: str):
    name = client.plugins.install_from_folder(folder)
    await interaction.response.send_message(f"Installed plugin: {name}")

@client.tree.command(name="plugin_remove", description="Remove plugin.")
async def plugin_remove(interaction: discord.Interaction, name: str):
    ok = client.plugins.remove(name)
    await interaction.response.send_message("Removed." if ok else "Not found.")

@client.tree.command(name="joinvoice", description="Bot joins your VC")
async def joinvoice(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("You must be in a voice channel.")
    channel = interaction.user.voice.channel
    await client.voice_agent.join(channel)
    await interaction.response.send_message("Joined voice channel.")

@client.tree.command(name="leavevoice", description="Bot leaves the voice channel.")
async def leavevoice(interaction: discord.Interaction):
    await client.voice_agent.leave()
    await interaction.response.send_message("Left voice channel.")

@client.tree.command(name="muteai", description="Stop the AI from listening.")
async def muteai(interaction: discord.Interaction):
    client.voice_agent.enabled = False
    await interaction.response.send_message("AI voice agent muted.")

@client.tree.command(name="unmuteai", description="Enable AI listening.")
async def unmuteai(interaction: discord.Interaction):
    client.voice_agent.enabled = True
    await interaction.response.send_message("AI voice agent unmuted.")

@client.tree.command(name="agent_create", description="Create a new agent.")
async def agent_create(interaction: discord.Interaction, name: str, model: str):
    client.agent_manager.create(name, model)
    await interaction.response.send_message(f"Agent '{name}' spawned.")

@client.tree.command(name="agent_list", description="List all agents.")
async def agent_list(interaction: discord.Interaction):
    await interaction.response.send_message(str(client.agent_manager.list()))

@client.tree.command(name="agent_kill", description="Kill an agent.")
async def agent_kill(interaction: discord.Interaction, name: str):
    client.agent_manager.kill(name)
    await interaction.response.send_message(f"Killed {name}.")

@client.tree.command(name="task_list", description="List scheduled tasks.")
async def task_list(interaction: discord.Interaction):
    out = []
    for t in client.scheduler.tasks.values():
        out.append(f"{t.name}: every {t.interval}s (enabled={t.enabled})")
    await interaction.response.send_message("\n".join(out) or "No tasks scheduled.")

@client.tree.command(name="task_enable", description="Enable a task.")
async def task_enable(interaction: discord.Interaction, name: str):
    client.scheduler.enable(name)
    await interaction.response.send_message(f"✅ Enabled: {name}")

@client.tree.command(name="task_disable", description="Disable a task.")
async def task_disable(interaction: discord.Interaction, name: str):
    client.scheduler.disable(name)
    await interaction.response.send_message(f"❌ Disabled: {name}")

@client.tree.command(name="remind", description="Set a reminder: remind <minutes> <message>")
async def remind(interaction: discord.Interaction, minutes: int, message: str):
    if minutes < 1 or minutes > 10080:  # Max 7 days
        await interaction.response.send_message("⏰ Minutes must be between 1 and 10080 (7 days).")
        return
    
    await interaction.response.defer()
    await interaction.followup.send(f"⏳ Reminder set for {minutes} minutes!")

    async def reminder():
        await asyncio.sleep(minutes * 60)
        try:
            await interaction.channel.send(f"⏰ <@{interaction.user.id}> Reminder: {message}")
        except Exception as e:
            print(f"[Reminder] Error sending reminder: {e}")

    asyncio.create_task(reminder())

@client.tree.command(name="mymemory", description="View what the bot remembers about you.")
async def mymemory_cmd(interaction: discord.Interaction):
    facts = get_user_facts(interaction.user.id)
    if facts:
        fact_list = "\n".join([f"• {f}" for f in facts])
        await interaction.response.send_message(f"**What I remember about you:**\n{fact_list[:1900]}")
    else:
        await interaction.response.send_message("I don't have any memories stored about you yet.")

@client.tree.command(name="forgetme", description="Clear all memories about you.")
async def forgetme_cmd(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if uid in user_memory:
        user_memory[uid] = {"facts": []}
        save_memory(user_memory)
        await interaction.response.send_message("✅ I've forgotten everything about you.")
    else:
        await interaction.response.send_message("I didn't have any memories about you anyway.")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    print(f"[DEBUG] Message received: {message.content[:50]}... from {message.author}")
    
    # Ignore slash commands (they're handled separately)
    if message.content.startswith('/'):
        return
    
    # Handle image attachments
    if message.attachments:
        file = message.attachments[0]
        img_bytes = await file.read()
        desc = ""
        async for d in stream_response("Describe this image.", client.current_model):
            chunk = d.get("response", "")
            if chunk:
                desc += chunk
        if desc.strip():
            await message.channel.send(desc[:2000])
        return
    
    # Freeform text responses - respond to all messages (with smart filtering)
    should_respond = False
    
    # Skip if message is too short or just emojis/mentions
    content_stripped = message.content.strip()
    if len(content_stripped) < 2:
        return  # Too short, probably just an emoji or punctuation
    
    # Skip slash commands (let Discord handle those)
    if content_stripped.startswith('/'):
        return
    
    # Skip if message is just mentions of other users (not the bot)
    if content_stripped.startswith('<@') and client.user not in message.mentions:
        return
    
    # Always respond in DMs
    if isinstance(message.channel, discord.DMChannel):
        should_respond = True
    
    # Respond to all messages in channels (freeform mode)
    # You can also respond when mentioned if you want both behaviors
    if client.user in message.mentions:
        should_respond = True
    else:
        # Freeform: respond to all messages
        should_respond = True
    
    if should_respond:
        # Show typing indicator
        async with message.channel.typing():
            user_id = str(message.author.id)
            
            # Clean the message text (remove bot mentions)
            prompt_text = message.content.replace(f"<@{client.user.id}>", "").replace(f"<@!{client.user.id}>", "").strip()
            
            # Skip empty messages
            if not prompt_text:
                return

            # ============================
            # TOOLS ORCHESTRATION LAYER (Phase 11)
            # ============================
            tool_result = None
            
            # Run deterministic handlers first
            det_response = try_deterministic_tools(prompt_text)
            if det_response is not None:
                tool_result = det_response
            
            if tool_result:
                # If it's a dict (like matchup context), send to LLM for reasoning
                if isinstance(tool_result, dict) and "matchup_context" in tool_result:
                    strategy_prompt = tool_result["matchup_context"]
                    full_text = ""
                    
                    async for data in stream_response(strategy_prompt, client.current_model):
                        chunk = data.get("response", "")
                        if chunk:
                            full_text += chunk
                    
                    if full_text.strip():
                        await message.reply(full_text[:2000])
                        client.long_memory.save(user_id, "user", prompt_text)
                        client.long_memory.save(user_id, "assistant", full_text)
                    return
                
                # Otherwise it's a normal deterministic tool response
                print(f"[DEBUG] Deterministic handler response: {tool_result[:200] if isinstance(tool_result, str) else 'dict response'}")
                await message.reply(tool_result[:2000] if isinstance(tool_result, str) else str(tool_result))
                client.long_memory.save(user_id, "user", prompt_text)
                client.long_memory.save(user_id, "assistant", tool_result if isinstance(tool_result, str) else str(tool_result))
                return
            # ============================
            # END TOOLS ORCHESTRATION
            # ============================

            # Store any facts from the message
            store_fact(message.author.id, prompt_text)
            
            # Get user's stored facts for context
            facts = get_user_facts(message.author.id)
            memory_context = ""
            if facts:
                memory_context = f"[You remember about this user: {'; '.join(facts[-5:])}]\n"
            
            # Get recent conversation history for context (limited to avoid stuck conversations)
            recent_history = client.long_memory.get_recent(user_id, limit=3)
            history_context = ""
            if recent_history:
                # Use compression for long histories (Phase 11)
                compressed = compress_history(recent_history)
                if len(compressed) < 900:
                    history_context = "Recent conversation:\n" + compressed + "\n\n"
                else:
                    history_lines = []
                    for role, content in recent_history[-3:]:
                        if role == "user":
                            history_lines.append(f"User: {content[:80]}")
                        else:
                            history_lines.append(f"You: {content[:80]}")
                    if history_lines:
                        history_context = "Recent conversation:\n" + "\n".join(history_lines[-2:]) + "\n\n"
            
            # Check if this is a greeting or a follow-up
            greetings = ["hi", "hey", "hello", "yo", "sup", "what's up", "whats up"]
            is_greeting = prompt_text.lower().strip() in greetings
            
            if is_greeting:
                agent_prompt = f"""Reply to "{prompt_text}" with a short casual greeting. Just say hey or what's up - nothing more."""
            else:
                agent_prompt = f"""{memory_context}{history_context}You are God Bot, a friendly assistant chatting in Discord.

Answer clearly and directly. If a calculation is needed, compute it correctly and show the final result.
Keep responses conversational and natural.

User: {prompt_text}
Your response:"""
            
            full_text = ""
            timeout_counter = 0
            max_timeout = 30  # 30 second max
            
            try:
                async for data in stream_response(agent_prompt, client.current_model):
                    chunk = data.get("response", "")
                    if chunk:
                        full_text += chunk
                        timeout_counter = 0  # Reset on successful chunk
                    else:
                        timeout_counter += 1
                        if timeout_counter > max_timeout:
                            print("[DEBUG] Timeout waiting for response")
                            break
                    await asyncio.sleep(0)  # Yield control
            except Exception as e:
                print(f"[ERROR] Ollama streaming failed: {e}")
                full_text = "Sorry, I had trouble responding. Try again!"
            
            if full_text.strip():
                # Clean up the response
                response = full_text.strip()
                
                # Remove surrounding quotes
                if response.startswith('"') and response.endswith('"'):
                    response = response[1:-1]
                if response.startswith("'") and response.endswith("'"):
                    response = response[1:-1]
                
                # Remove "Reply:" or similar prefixes
                for prefix in ["Reply:", "reply:", "Response:", "response:", "God Bot:", "god bot:", "Assistant:", "assistant:", "User:", "user:"]:
                    if response.startswith(prefix):
                        response = response[len(prefix):].strip()
                
                # Remove surrounding quotes again after prefix removal
                if response.startswith('"') and response.endswith('"'):
                    response = response[1:-1]
                if response.startswith("'") and response.endswith("'"):
                    response = response[1:-1]
                
                # Fix model identity issues (dolphin model sometimes identifies as Dolphin)
                response = response.replace("As Dolphin,", "").replace("as Dolphin,", "")
                response = response.replace("I am a Dolphin", "I'm just chilling")
                response = response.replace("I'm a Dolphin", "I'm good")
                response = response.replace("Seeing as I am a Dolphin,", "")
                response = response.replace("As a Dolphin,", "")
                response = response.replace("Dolphin", "God Bot")
                response = response.strip()
                
                # Remove AI assistant language
                ai_phrases = ["As an AI", "as an AI", "I'm an AI", "I am an AI", "I don't have personal experiences"]
                for phrase in ai_phrases:
                    if phrase in response:
                        # Remove the sentence containing AI language
                        sentences = response.split(". ")
                        response = ". ".join([s for s in sentences if phrase not in s])
                        response = response.strip()
                
                # Remove bullet point conversation logs
                lines = response.split("\n")
                clean_lines = []
                for line in lines:
                    stripped = line.strip()
                    # Skip conversation log patterns
                    if stripped.startswith("- ") and ":" in stripped[:30]:
                        continue
                    if stripped.startswith("*") and ":" in stripped[:30]:
                        continue
                    if " = " in stripped and len(stripped) < 30:
                        continue
                    if stripped in ["/\\", "/ \\", "\\/", ""]:
                        continue
                    clean_lines.append(line)
                
                response = "\n".join(clean_lines).strip()
                
                # Final cleanup
                if not response:
                    response = "hey"
                
                # Debug: Show what actually gets sent to Discord
                print(f"[DEBUG] Bot Response: {response[:2000]}")
                
                # Send response
                await message.reply(response[:2000])
                
                # Save to memory (simplified)
                client.long_memory.save(user_id, "user", prompt_text)
                client.long_memory.save(user_id, "assistant", response)

client.run(TOKEN)

