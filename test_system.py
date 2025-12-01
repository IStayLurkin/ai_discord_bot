#!/usr/bin/env python3
"""
Comprehensive system test script
Tests all components of the Discord bot
"""
import sys
import asyncio
import requests
import json
import sqlite3
import os

print("=" * 60)
print("AI DISCORD BOT - SYSTEM TEST")
print("=" * 60)
print()

# Test results
results = {
    "dashboard": {},
    "discord": {},
    "plugins": {},
    "memory": {},
    "agents": {},
    "voice": {}
}

# ============================================================
# DASHBOARD TESTS
# ============================================================
print("TESTING DASHBOARD...")
print("-" * 60)

try:
    # Test dashboard status endpoint
    response = requests.get("http://localhost:5000/status", timeout=5)
    if response.status_code == 200:
        data = response.json()
        results["dashboard"]["status_endpoint"] = "✅ WORKING"
        results["dashboard"]["model"] = data.get("model", "unknown")
        print(f"✅ Status endpoint: WORKING (Model: {data.get('model')})")
    else:
        results["dashboard"]["status_endpoint"] = f"❌ ERROR ({response.status_code})"
        print(f"❌ Status endpoint: ERROR ({response.status_code})")
except Exception as e:
    results["dashboard"]["status_endpoint"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Status endpoint: ERROR - {e}")

try:
    # Test plugins endpoint
    response = requests.get("http://localhost:5000/plugins", timeout=5)
    if response.status_code == 200:
        plugins = response.json()
        results["dashboard"]["plugins_endpoint"] = "✅ WORKING"
        results["plugins"]["count"] = len(plugins) if isinstance(plugins, list) else 0
        print(f"✅ Plugins endpoint: WORKING ({len(plugins) if isinstance(plugins, list) else 0} plugins)")
    else:
        results["dashboard"]["plugins_endpoint"] = f"❌ ERROR ({response.status_code})"
        print(f"❌ Plugins endpoint: ERROR ({response.status_code})")
except Exception as e:
    results["dashboard"]["plugins_endpoint"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Plugins endpoint: ERROR - {e}")

try:
    # Test model endpoint
    response = requests.get("http://localhost:5000/model", timeout=5)
    if response.status_code == 200:
        data = response.json()
        results["dashboard"]["model_endpoint"] = "✅ WORKING"
        print(f"✅ Model endpoint: WORKING")
    else:
        results["dashboard"]["model_endpoint"] = f"❌ ERROR ({response.status_code})"
        print(f"❌ Model endpoint: ERROR ({response.status_code})")
except Exception as e:
    results["dashboard"]["model_endpoint"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Model endpoint: ERROR - {e}")

# Test dashboard UI files
print("\nTESTING DASHBOARD UI FILES...")
ui_files = [
    "dashboard/ui/index.html",
    "dashboard/ui/style.css",
    "dashboard/ui/app.js"
]
for file in ui_files:
    if os.path.exists(file):
        results["dashboard"][f"ui_{os.path.basename(file)}"] = "✅ EXISTS"
        print(f"✅ {file}: EXISTS")
    else:
        results["dashboard"][f"ui_{os.path.basename(file)}"] = "❌ MISSING"
        print(f"❌ {file}: MISSING")

print()

# ============================================================
# PLUGIN TESTS
# ============================================================
print("TESTING PLUGINS...")
print("-" * 60)

try:
    from plugins.plugin_manager import PluginManager
    pm = PluginManager()
    pm.load_all()
    
    plugin_count = len(pm.loaded_plugins)
    behavior_count = len(pm.behavior_injections)
    
    results["plugins"]["manager"] = "✅ WORKING"
    results["plugins"]["python_plugins"] = plugin_count
    results["plugins"]["behavior_plugins"] = behavior_count
    
    print(f"✅ Plugin Manager: WORKING")
    print(f"   - Python plugins: {plugin_count}")
    print(f"   - Behavior plugins: {behavior_count}")
    
    # Check example plugins
    if os.path.exists("plugins/example_search_tool/manifest.json"):
        results["plugins"]["example_search_tool"] = "✅ EXISTS"
        print(f"✅ Example search tool: EXISTS")
    else:
        results["plugins"]["example_search_tool"] = "❌ MISSING"
        print(f"❌ Example search tool: MISSING")
    
    if os.path.exists("plugins/friendly_mode/manifest.json"):
        results["plugins"]["friendly_mode"] = "✅ EXISTS"
        print(f"✅ Friendly mode plugin: EXISTS")
    else:
        results["plugins"]["friendly_mode"] = "❌ MISSING"
        print(f"❌ Friendly mode plugin: MISSING")
        
except Exception as e:
    results["plugins"]["manager"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Plugin Manager: ERROR - {e}")

print()

# ============================================================
# MEMORY TESTS
# ============================================================
print("TESTING MEMORY SYSTEMS...")
print("-" * 60)

try:
    from godbot.core.memory import MemoryDB
    db = MemoryDB("test_memory.db")
    db.save("test_user", "user", "test message")
    recent = db.get_recent("test_user", 1)
    
    if recent and len(recent) > 0:
        results["memory"]["sqlite"] = "✅ WORKING"
        print(f"✅ SQLite Memory: WORKING")
        # Cleanup test DB
        try:
            os.remove("test_memory.db")
        except:
            pass
    else:
        results["memory"]["sqlite"] = "❌ ERROR"
        print(f"❌ SQLite Memory: ERROR")
except Exception as e:
    results["memory"]["sqlite"] = f"❌ ERROR ({str(e)})"
    print(f"❌ SQLite Memory: ERROR - {e}")

try:
    from godbot.core.vector_memory import VectorMemory
    vm = VectorMemory()
    vm.add("test_user", "test vector memory")
    search_results = vm.search("test", 1)
    
    results["memory"]["vector"] = "✅ WORKING"
    print(f"✅ Vector Memory: WORKING")
except Exception as e:
    results["memory"]["vector"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Vector Memory: ERROR - {e}")

print()

# ============================================================
# TOOLS TESTS
# ============================================================
print("TESTING TOOLS...")
print("-" * 60)

try:
    from tools.tool_registry import ToolRegistry
    tr = ToolRegistry()
    schemas = tr.list_schemas()
    
    results["tools"]["registry"] = "✅ WORKING"
    results["tools"]["count"] = len(schemas)
    print(f"✅ Tool Registry: WORKING ({len(schemas)} tools)")
    
    if "web_search" in [s.get("name") for s in schemas]:
        results["tools"]["web_search"] = "✅ EXISTS"
        print(f"✅ Web search tool: EXISTS")
    else:
        results["tools"]["web_search"] = "❌ MISSING"
        print(f"❌ Web search tool: MISSING")
except Exception as e:
    results["tools"] = {"registry": f"❌ ERROR ({str(e)})"}
    print(f"❌ Tool Registry: ERROR - {e}")

print()

# ============================================================
# AGENTS TESTS
# ============================================================
print("TESTING AGENT SYSTEM...")
print("-" * 60)

try:
    from agents import AgentManager
    am = AgentManager()
    am.create("test_agent", "llama3:instruct")
    agent_list = am.list()
    
    if "test_agent" in agent_list:
        results["agents"]["manager"] = "✅ WORKING"
        results["agents"]["create"] = "✅ WORKING"
        print(f"✅ Agent Manager: WORKING")
        print(f"✅ Agent Create: WORKING")
        
        am.kill("test_agent")
        if "test_agent" not in am.list():
            results["agents"]["kill"] = "✅ WORKING"
            print(f"✅ Agent Kill: WORKING")
        else:
            results["agents"]["kill"] = "❌ ERROR"
            print(f"❌ Agent Kill: ERROR")
    else:
        results["agents"]["manager"] = "❌ ERROR"
        print(f"❌ Agent Manager: ERROR")
except Exception as e:
    results["agents"]["manager"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Agent System: ERROR - {e}")

print()

# ============================================================
# VOICE TESTS
# ============================================================
print("TESTING VOICE SYSTEM...")
print("-" * 60)

try:
    import audio
    results["voice"]["module"] = "✅ LOADED"
    print(f"✅ Audio module: LOADED")
    
    if hasattr(audio, 'SINKS_AVAILABLE'):
        if audio.SINKS_AVAILABLE:
            results["voice"]["sinks"] = "✅ AVAILABLE"
            print(f"✅ Discord sinks: AVAILABLE")
        else:
            results["voice"]["sinks"] = "⚠️ NOT AVAILABLE"
            print(f"⚠️ Discord sinks: NOT AVAILABLE (voice chat disabled)")
    else:
        results["voice"]["sinks"] = "⚠️ UNKNOWN"
        print(f"⚠️ Discord sinks: UNKNOWN")
except Exception as e:
    results["voice"]["module"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Audio module: ERROR - {e}")

print()

# ============================================================
# OLLAMA CONNECTION TEST
# ============================================================
print("TESTING OLLAMA CONNECTION...")
print("-" * 60)

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3:instruct", "prompt": "test", "stream": False},
        timeout=10
    )
    if response.status_code == 200:
        results["ollama"] = "✅ WORKING"
        print(f"✅ Ollama: WORKING")
    else:
        results["ollama"] = f"❌ ERROR ({response.status_code})"
        print(f"❌ Ollama: ERROR ({response.status_code})")
except Exception as e:
    results["ollama"] = f"❌ ERROR ({str(e)})"
    print(f"❌ Ollama: ERROR - {e}")
    print("   Make sure Ollama is running: ollama serve")

print()

# ============================================================
# SUMMARY
# ============================================================
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)

def print_section(name, data):
    print(f"\n{name.upper()}:")
    for key, value in data.items():
        status_icon = "✅" if "WORKING" in str(value) or "EXISTS" in str(value) or "AVAILABLE" in str(value) else "❌" if "ERROR" in str(value) or "MISSING" in str(value) else "⚠️"
        print(f"  {status_icon} {key}: {value}")

for section, data in results.items():
    if data:
        print_section(section, data)

print("\n" + "=" * 60)
print("MANUAL TESTING REQUIRED:")
print("=" * 60)
print("""
DISCORD COMMANDS (test in Discord):
  • /ask hello
  • /setmodel llama3:instruct
  • /plugins_list
  • /plugin_install <folder>
  • /plugin_remove <name>
  • /joinvoice (if in voice channel)
  • /agent_create test_agent llama3:instruct
  • /agent_list
  • /agent_kill test_agent

DASHBOARD (test in browser at http://localhost:5000):
  • Open dashboard
  • Click all tabs (Status, Models, Memory, Plugins, Agent Console)
  • Try changing model
  • Try loading memory for a user ID
  • Try sending message in Agent Console
""")

print("=" * 60)
print("Test complete! Review results above.")
print("=" * 60)

