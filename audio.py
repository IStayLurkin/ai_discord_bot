import discord
import asyncio
import subprocess
import tempfile

# Optional imports for voice chat
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ollama_client import stream_ollama

try:
    from discord.sinks import Sink
    SINKS_AVAILABLE = True
    _SinkBase = Sink
except ImportError:
    SINKS_AVAILABLE = False
    _SinkBase = object

try:
    import warnings
    import logging
    # Suppress openwakeword tflite warning (harmless - falls back to onnxruntime)
    warnings.filterwarnings("ignore", message=".*tflite.*")
    logging.getLogger("root").setLevel(logging.ERROR)
    
    from openwakeword.model import Model
    hotword = Model(wakeword_models=["hey_jarvis"])
    HOTWORD_AVAILABLE = True
except:
    HOTWORD_AVAILABLE = False
    hotword = None

class VoiceAgent:
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.enabled = True
        self.listening = False
        self.sink = None

    async def join(self, channel):
        if not SINKS_AVAILABLE:
            print("Voice chat not available - discord.sinks module not found")
            return
        try:
            if self.voice_client:
                await self.voice_client.disconnect()
            self.voice_client = await channel.connect()
            self.sink = VoiceReceiver(self)
            self.voice_client.start_recording(self.sink)
        except Exception as e:
            print(f"Voice chat error: {e}")
            if self.voice_client:
                await self.voice_client.disconnect()
                self.voice_client = None

    async def leave(self):
        if self.voice_client:
            if self.sink:
                try:
                    self.voice_client.stop_recording()
                except:
                    pass
            await self.voice_client.disconnect()
            self.voice_client = None
            self.sink = None

    async def transcribe(self, pcm_data):
        if not SOUNDFILE_AVAILABLE:
            return "Voice transcription requires soundfile. Install with: pip install soundfile"
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, pcm_data, 48000)
            path = f.name
        
        try:
            text = subprocess.check_output([
                "whisper", path, "--model", "tiny", "--language", "en", "--fp16", "False", "--output_format", "txt"
            ]).decode()
            return text.strip()
        except:
            return ""

    async def speak(self, text):
        if not self.voice_client:
            return
        
        try:
            t = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            subprocess.check_output([
                "tts", "--text", text, "--out_path", t.name
            ])
            source = discord.FFmpegPCMAudio(t.name)
            self.voice_client.play(source)
        except:
            pass

if SINKS_AVAILABLE:
    class VoiceReceiver(_SinkBase):
        def __init__(self, agent):
            if SINKS_AVAILABLE:
                super().__init__()
            self.agent = agent
            self.buffer = {}

    def write(self, user, data):
        if not self.agent.enabled:
            return
        
        if not NUMPY_AVAILABLE:
            return
        
        if user.id not in self.buffer:
            self.buffer[user.id] = []
        
        try:
            pcm = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        except:
            return
            
            # Hotword detection if available
            if HOTWORD_AVAILABLE and hotword:
                try:
                    score = hotword.predict(pcm)
                    if score.get("hey_jarvis", 0) > 0.85:
                        self.agent.listening = True
                        return
                except:
                    pass
            
            # If hotword not available or push-to-talk mode, listen when enabled
            if not HOTWORD_AVAILABLE:
                self.agent.listening = True
            
            if not self.agent.listening:
                return
            
            self.buffer[user.id].append(pcm)
            
            if len(self.buffer[user.id]) > 60:  # about 1.5 seconds
                asyncio.run_coroutine_threadsafe(
                    self.process_audio(user),
                    asyncio.get_event_loop()
                )
                self.buffer[user.id] = []
                self.agent.listening = False

        async def process_audio(self, user):
            if user.id not in self.buffer or not self.buffer[user.id]:
                return
            
            pcm_data = np.concatenate(self.buffer[user.id])
            text = await self.agent.transcribe(pcm_data)
            
            if not text:
                return
            
            prompt = f"{user.name} said: {text}"
            
            reply = ""
            async for d in stream_ollama(prompt, self.agent.bot.current_model):
                if "response" in d:
                    reply += d["response"]
            
            await self.agent.speak(reply)
else:
    # Fallback if sinks not available
    class VoiceReceiver:
        pass

