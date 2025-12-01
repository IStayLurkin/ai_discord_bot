# Quick Start Guide

## 1. Install Python 3.10+
Download from: https://www.python.org/downloads/

## 2. Install Ollama
Download from: https://ollama.com/download

Pull a model:
```bash
ollama pull llama3:instruct
```

Test it:
```bash
ollama run llama3:instruct "hello"
```

## 3. Create Discord Bot

1. Go to: https://discord.com/developers/applications
2. Click "New Application"
3. Name it (e.g., "LocalOllamaBot")
4. Go to "Bot" → "Add Bot"
5. Under "Privileged Gateway Intents":
   - ✅ Enable MESSAGE CONTENT INTENT
6. Copy the Bot Token

## 4. Invite Bot to Server

1. Go to OAuth2 → URL Generator
2. Check:
   - ✅ bot
   - ✅ Send Messages
   - ✅ Read Message History
3. Copy generated URL
4. Open in browser → choose server → authorize

## 5. Configure Bot

Edit `main.py` line 14:
```python
TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
```

## 6. Install Dependencies

```bash
pip install -r requirements.txt
```

## 7. Run Bot

```bash
python main.py
```

You should see:
- "Logged in as [BotName]"
- "Discord slash commands synced."
- "Dashboard running on http://localhost:5000"

## 8. Test in Discord

In any channel, type:
```
/ask hello
```

The bot will respond using your local Ollama model!

## Access Dashboard

Open browser: http://localhost:5000

## Optional: Voice Chat Setup

1. Install ffmpeg: https://ffmpeg.org/download.html
2. Install whisper: `pip install openai-whisper`
3. Install TTS: `pip install TTS`

Then use `/joinvoice` in Discord!

## Troubleshooting

- **Bot doesn't respond**: Check token is correct, bot has permissions
- **Ollama errors**: Make sure Ollama is running (`ollama serve`)
- **Import errors**: Run `pip install -r requirements.txt`
- **Dashboard not loading**: Check port 5000 is available

