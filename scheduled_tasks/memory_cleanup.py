# scheduled_tasks/memory_cleanup.py
import json
import os

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

def save_memory(mem):
    """Save memory to memory.json"""
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=4)

async def memory_cleanup(bot):
    mem = load_memory()

    # dedupe + trim
    for user in mem:
        facts = mem[user].get("facts", [])
        mem[user]["facts"] = list(dict.fromkeys(facts))[-30:]

    save_memory(mem)
    print("[Scheduled] Memory cleanup complete")

