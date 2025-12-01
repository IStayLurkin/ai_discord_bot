# Quick System Test Checklist

Run this while your bot is running (`python main.py`):

## Automated Test
```bash
python test_system.py
```

## Manual Checklist

### DASHBOARD (http://localhost:5000)
- [ ] Dashboard opens in browser
- [ ] Status tab shows model info
- [ ] Models tab allows changing model
- [ ] Memory tab loads user memory
- [ ] Plugins tab shows installed plugins
- [ ] Agent Console sends/receives messages

### DISCORD TEXT COMMANDS
- [ ] `/ask hello` - Bot responds
- [ ] `/setmodel llama3:instruct` - Model changes
- [ ] `/plugins_list` - Shows plugins
- [ ] `/plugin_install <folder>` - Installs plugin
- [ ] `/plugin_remove <name>` - Removes plugin

### VOICE (if available)
- [ ] `/joinvoice` - Bot joins VC
- [ ] Bot listens when you speak
- [ ] Bot responds with voice (if TTS installed)

### MEMORY
- [ ] Bot remembers previous messages in conversation
- [ ] Vector memory returns related info

### AGENTS
- [ ] `/agent_create test_agent llama3:instruct` - Creates agent
- [ ] `/agent_list` - Lists agents
- [ ] `/agent_kill test_agent` - Kills agent

---

**Mark each item as:**
- ✅ Working
- ❌ Error (describe error)
- ⚠️ Haven't tested

