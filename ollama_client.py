import requests
import json
import asyncio

async def stream_ollama(prompt, model, tools=None):
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }
    
    if tools:
        payload["tools"] = tools
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=30)
        response.raise_for_status()  # Raise exception for bad status codes
        
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
                yield data
            except json.JSONDecodeError:
                continue  # Skip invalid JSON lines
            await asyncio.sleep(0)
    except requests.exceptions.ConnectionError:
        yield {"error": "Cannot connect to Ollama. Is it running? (ollama serve)"}
    except requests.exceptions.Timeout:
        yield {"error": "Ollama request timed out"}
    except Exception as e:
        yield {"error": f"Ollama error: {str(e)}"}

