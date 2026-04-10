# AGENTS.md - Ollama Server

## What This Project Does

A shared Ollama proxy server that centralizes LLM access for multiple applications. Instead of each app connecting directly to Ollama, they connect here. This server:

1. **Proxies Ollama API** - Transparent pass-through to the real Ollama instance
2. **Provides Web UI** - Browser-based interface for configuration and model management
3. **Persists Configuration** - Settings stored in `config.json`

## Why It Exists

- Multiple apps (`cold-local-llm-server`, `notetaker`) need Ollama access
- Want to run Ollama on a stronger machine, accessed by lighter clients
- Centralized configuration and model management without SSH

## Project Structure

```
ollama-server/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Config loading/saving
│   ├── proxy.py          # Ollama API proxy logic
│   └── routers/
│       ├── __init__.py
│       ├── ollama.py     # Proxy routes for Ollama API
│       └── management.py # Config and status routes
├── static/
│   ├── index.html        # Web UI
│   ├── style.css
│   └── app.js
├── config.json           # Runtime config (gitignored)
├── config.example.json   # Example config (committed)
├── requirements.txt
└── README.md
```

## Key Files

- `app/main.py` - FastAPI application, serves static files, includes routers
- `app/config.py` - Load/save `config.json`, provides `get_config()` function
- `app/proxy.py` - Core proxy logic: forward requests to Ollama, handle streaming
- `app/routers/ollama.py` - Routes that proxy Ollama API (`/api/tags`, `/api/generate`, etc.)
- `app/routers/management.py` - Routes for config and status (`/api/config`, `/api/status`)

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, httpx (async HTTP client)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no build step)
- **Config**: JSON file

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run server (development)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 11435

# Run server (production-ish)
python -m uvicorn app.main:app --host 0.0.0.0 --port 11435
```

## API Routes

### Ollama Proxy Routes (pass-through to Ollama)
- `GET /api/tags` - List models
- `POST /api/generate` - Generate completion (streaming supported)
- `POST /api/chat` - Chat completion (streaming supported)
- `POST /api/pull` - Pull a model
- `DELETE /api/delete` - Delete a model
- `GET /api/ps` - List running models

### Management Routes
- `GET /` - Web UI
- `GET /api/config` - Get current config
- `PUT /api/config` - Update config
- `GET /api/status` - Health check + Ollama connectivity

## Configuration

`config.json` structure:
```json
{
  "ollama_url": "http://localhost:11434",
  "server_host": "0.0.0.0",
  "server_port": 11435
}
```

## Patterns and Conventions

### Streaming Responses

Use `StreamingResponse` with an async generator for SSE:

```python
from fastapi.responses import StreamingResponse

async def stream_from_ollama():
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=payload) as response:
            async for chunk in response.aiter_bytes():
                yield chunk

return StreamingResponse(stream_from_ollama(), media_type="application/x-ndjson")
```

### Config Access

Always use `get_config()` from `app/config.py` - never read the file directly in route handlers.

### Error Handling

Pass through Ollama errors transparently. If Ollama returns an error, proxy it to the client unchanged.

## Testing

### Manual Testing

1. Start server: `python -m uvicorn app.main:app --reload --port 11435`
2. Check health: `curl http://localhost:11435/api/status`
3. List models: `curl http://localhost:11435/api/tags`
4. Test streaming: `curl http://localhost:11435/api/generate -d '{"model":"llama3","prompt":"Hi","stream":true}'`
5. Open Web UI: `http://localhost:11435/`

### Integration Testing

Point `notetaker` or `cold-local-llm-server` at this server and verify they work normally.

## Debugging Tips

- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Check proxy connectivity: `curl http://localhost:11435/api/status`
- Streaming issues: Check `Content-Type` headers and chunked transfer encoding
- CORS issues: If browser requests fail, check CORS middleware configuration

## Security Notes

- **v1 assumes trusted LAN** - no authentication
- Server binds to `0.0.0.0` for network access
- Don't expose to public internet without adding auth
