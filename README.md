# 🧠 God Bot — Local AI Discord Platform

God Bot is a **local, Ollama-powered Discord AI platform** with:

- ✅ Deterministic tools for **finance, fitness, nutrition, math, Wild Rift builds**
- ✅ A **Discord chat bot** with streaming replies
- ✅ A **web dashboard** (live logs, model switcher, memory viewer, plugins, agents, voice toggle)
- ✅ **Long-term memory** (SQLite + JSON) and **vector memory**
- ✅ A **plugin system** with sandboxed tools (temporarily running in non-sandboxed mode)
- ✅ A **scheduler** for background tasks (heartbeats, plugin reload, memory cleanup, daily reports)

It's built to be your personal "AI OS" running on your own hardware, using your models.

---

## 🔧 Features

### 💬 Discord AI Assistant

- Streams responses from your local Ollama model (default: `dolphin-llama3:latest`)
- Chat in channels or DMs
- Image description for attachments
- Personality layer on top of LLM output
- Long-term memory of past conversations (per-user)

### 🧮 Deterministic Tool System (Zero-Hallucination for Numbers)

Located in `deterministic/`:

- `math_tools.py` — arithmetic, percentages, tips, basic conversions
- `finance_tools.py` — runway, FI age, FIRE-style calculations (more to come)
- `fitness_tools.py` — 1RM & strength calculations (Epley, etc.)
- `nutrition_tools.py` — calories/macros helpers
- `wildrift_tools.py` — Wild Rift build loader + deterministic build lookup

These tools are pure Python. When a message matches a deterministic pattern (e.g. specific finance/bench/Wild Rift queries), God Bot:

1. Runs the Python tool first
2. Returns the exact numeric answer
3. Only uses the LLM for explanation or non-numeric reasoning

No hallucinations for math/finance/1RM once a tool is in place.

### ⚔️ Wild Rift Build System

- Champion builds stored as Markdown in `data/wild_rift_builds/`
  - e.g. `garen.md`, `vi.md`, `shyvana.md`, `jinx.md`, `leona.md`, `nasus.md`
- Deterministic loader in `deterministic/wildrift_tools.py`
- Triggers when user asks for a Wild Rift build or mentions specific champs

Easy to extend: just drop a new `.md` file and the system can pick it up.

### 📊 Finance Tools

- Runway calculator (months/years left at your current burn)
- FI age / time to FI (baseline)
- Designed to be extended with:
  - Coast FI, Lean FI
  - Inflation-adjusted millionaire timelines
  - Drawdown simulators
  - Net worth projections

All of this lives in `deterministic/finance_tools.py`.

### 🍗 Fitness & Nutrition

- 1RM estimation tools in `deterministic/fitness_tools.py`
- Basic macros/TDEE helpers in `deterministic/nutrition_tools.py`
- Extensible so you can add:
  - Strength standard checks
  - Program generators
  - Volume recommendations
  - Macro presets

### 🧠 Memory System

- `godbot/core/memory.py` — JSON + SQLite (`MemoryDB`) for long-term chat history
- `memory.json` — per-user "facts" (stable preferences, jobs, etc.)
- `long_memory.db` — long-term conversation logs
- `godbot/core/vector_memory.py` — vector memory for semantic search

The bot uses a combination of:

- recent chat snippets
- long-term memory
- optional vector search results

…to build context for each LLM call.

### 🕒 Scheduler

Core scheduler lives in `godbot/core/scheduler.py`.

Tasks are registered in `main.py` (or via scheduled task modules) and can include:

- Heartbeat logs
- Plugin auto-reload checks
- Memory cleanup (dedup + trimming)
- Daily reports to a Discord channel

Runs in the background as an async loop.

### 🧩 Plugins

The `plugins/` directory contains:

- `plugin_manager.py` — manages plugin loading, behavior injections, tools
- Example plugin: `example_search_tool/`
- Friendly behavior mode: `friendly_mode/`

Plugins can:

- Inject behavior into prompts (e.g., tone, style)
- Provide tool functions callable by the LLM
- Be hot-reloaded (via plugin manager and scheduler)

> **Note**: A temporary non-sandboxed `safe_exec` is in place during refactor;
> a stronger sandbox will be restored in a later phase.

### 🌐 Dashboard

`dashboard.py` + `dashboard/ui/` provide a small web UI:

- Live logs
- Model list + switcher (via Ollama tags)
- Memory viewer/editor
- Plugin viewer
- Agent list
- Voice agent toggle

Runs at:

```text
http://localhost:5000
```

when the bot is running.

---

## 🏗️ Architecture Overview

High-level layout:

```
flowchart LR
    subgraph Discord
        U[User] -->|messages| B[God Bot Client]
    end

    subgraph Core
        LLM[LLM Wrapper<br/>godbot/core/llm.py]
        MEM[MemoryDB + JSON<br/>godbot/core/memory.py]
        VM[Vector Memory<br/>godbot/core/vector_memory.py]
        SCHED[Scheduler<br/>godbot/core/scheduler.py]
    end

    subgraph Deterministic
        FIN[Finance Tools]
        FIT[Fitness Tools]
        NUT[Nutrition Tools]
        MATH[Math Tools]
        WR[Wild Rift Tools]
    end

    subgraph Plugins
        PM[Plugin Manager]
        PL[Plugins Folder]
    end

    subgraph Dashboard
        FLASK[dashboard.py]
        UI[dashboard/ui]
    end

    B --> LLM
    B --> MEM
    B --> VM
    B --> SCHED
    B --> PM
    PM --> PL

    B --> FIN
    B --> FIT
    B --> NUT
    B --> MATH
    B --> WR

    B --> FLASK
    FLASK --> UI
```

---

## 📁 Project Structure

Current key layout:

```
ai_discord_bot/
├── main.py                 # Entry point (Discord bot bootstrap)
├── agents.py               # Agent manager
├── audio.py                # Voice agent
├── committee_agent.py      # Committee-style multi-agent logic
├── dashboard.py            # Flask backend for web UI
├── godbot/
│   ├── core/
│   │   ├── llm.py          # Central Ollama streaming wrapper
│   │   ├── memory.py       # MemoryDB + JSON memory logic
│   │   ├── vector_memory.py# Vector memory search
│   │   └── scheduler.py    # Core scheduler
│   └── discord/
│       └── bot.py          # MyClient definition & factory
├── deterministic/
│   ├── finance_tools.py
│   ├── fitness_tools.py
│   ├── math_tools.py
│   ├── nutrition_tools.py
│   └── wildrift_tools.py
├── data/
│   └── wild_rift_builds/
│       ├── garen.md
│       ├── vi.md
│       ├── shyvana.md
│       ├── leona.md
│       ├── nasus.md
│       └── jinx.md
├── plugins/
│   ├── plugin_manager.py
│   ├── example_search_tool/
│   └── friendly_mode/
├── dashboard/
│   └── ui/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── scheduled_tasks/        # (if present) memory cleanup, plugin reload, etc.
├── tests/                  # basic test scaffolding
├── requirements.txt
├── pyproject.toml
└── README.md               # (this file)
```

---

## 🚀 Getting Started

### 1. Requirements

- Python 3.10+
- A working Ollama install with at least one model (e.g. `dolphin-llama3:latest`)
- A Discord bot token

### 2. Clone and set up

```bash
git clone https://github.com/IStayLurkin/ai_discord_bot.git
cd ai_discord_bot

# Optional: create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Create your `.env`

In the project root (`ai_discord_bot/`):

```env
DISCORD_TOKEN=your_discord_bot_token_here
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=dolphin-llama3:latest
```

### 4. Make sure Ollama is running

```bash
ollama serve
ollama list
# ensure the model in OLLAMA_MODEL is available
```

### 5. Run the bot

```bash
python main.py
```

You should see logs like:

```
Discord slash commands synced.
Dashboard running on http://localhost:5000
Logged in as God Bot#1234
[Scheduler] Started
```

---

## 💡 Usage

### Discord

Mention the bot or talk in a channel it can read.

Use slash commands like `/ask`, `/research`, `/committee` (depending on your current setup).

It will automatically:

- Use deterministic tools for math/finance/WR when applicable.
- Fall back to LLM for general reasoning.

### Dashboard

Once the bot is running:

Open `http://localhost:5000` in your browser.

View logs, switch models, inspect memory, and more.

---

## 🔧 Extending God Bot

### Add a new deterministic tool

1. Pick a module in `deterministic/` or create a new one.
2. Use the registry system in `deterministic/registry.py` (if present) or integrate with the existing pattern in `main.py`.
3. Write pure Python logic for the tool.
4. Add pattern detection in the deterministic layer so the tool fires before the LLM.

### Add a new Wild Rift champion build

1. Create a new file in `data/wild_rift_builds/`, e.g. `darius.md`
2. Follow the build format used in `garen.md` / `vi.md`
3. Update `wildrift_tools.py` if needed to include any special logic

### Add a plugin

1. Create a new folder under `plugins/`
2. Add a `manifest.json` and `tool.py` (see `example_search_tool` for reference)
3. The plugin manager will scan and load it on startup (or via auto-reload).

---

## 📜 License

MIT License

---

## ⭐ Acknowledgements

Built for high-performance local AI with Ollama, using Deterministic-First architecture for reliability.
