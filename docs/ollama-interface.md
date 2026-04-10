# Ollama Server Interface

How clients connect to ollama-server for LLM inference.

## Architecture Overview

Ollama-server is a **transparent proxy** to the Ollama REST API. Clients make the exact same requests they would make to Ollama directly, just pointing to this server instead.

```
Client App (notetaker, cold-local-llm-server, etc.)
    ↓ HTTP requests to ollama-server
ollama-server at http://<host>:11435
    ↓ forwards requests unchanged
Ollama at http://localhost:11434 (or configured URL)
    ↓ returns response
ollama-server
    ↓ passes response back
Client App
```

## Ollama REST API Endpoints (Proxied)

These endpoints mirror Ollama's API exactly. All request/response formats are unchanged.

| Endpoint | Method | Purpose | Streaming |
|---|---|---|---|
| `/api/generate` | POST | Text generation (completion-style) | Yes |
| `/api/chat` | POST | Chat completion (message-style) | Yes |
| `/api/tags` | GET | List available models | No |
| `/api/ps` | GET | List currently running/loaded models | No |
| `/api/pull` | POST | Download a model | Yes (progress) |
| `/api/delete` | DELETE | Remove a model | No |

### `/api/generate` — Text Generation

Request body (same as Ollama):

```json
{
  "model": "llama3",
  "prompt": "Why is the sky blue?",
  "stream": true,
  "format": "json"
}
```

- `model` (required): Model name as shown in `ollama list`
- `prompt` (required): The prompt text
- `stream` (optional): `true` for streaming, `false` for single response
- `format` (optional): `"json"` for JSON mode

Response (non-streaming):

```json
{
  "model": "llama3",
  "response": "The sky appears blue because...",
  "done": true,
  "done_reason": "stop"
}
```

Response (streaming): NDJSON, one JSON object per line. Each has a `response` field with a token. Final object has `"done": true`.

### `/api/chat` — Chat Completion

Request body (same as Ollama):

```json
{
  "model": "llama3",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": true
}
```

Response format mirrors `/api/generate` but with `message` instead of `response`.

### `/api/tags` — List Models

No request body. Response:

```json
{
  "models": [
    {
      "name": "llama3:8b",
      "size": 4661224676,
      "modified_at": "2024-01-15T10:30:00Z",
      "details": {
        "parameter_size": "8B",
        "quantization_level": "Q4_K_M"
      }
    }
  ]
}
```

### `/api/pull` — Download Model

Request body:

```json
{
  "name": "llama3:8b"
}
```

Response: Streaming NDJSON with progress updates. Each line contains `status` and optionally `completed`/`total` for progress calculation.

### `/api/delete` — Remove Model

Request body:

```json
{
  "name": "llama3:8b"
}
```

Response: Empty on success (HTTP 200).

## Management Endpoints (ollama-server only)

These endpoints are specific to ollama-server and don't exist in Ollama.

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Web UI for configuration and model management |
| `/api/status` | GET | Health check + Ollama connectivity status |
| `/api/config` | GET | Get current server configuration |
| `/api/config` | PUT | Update server configuration |

### `/api/status` — Health Check

Response:

```json
{
  "status": "ok",
  "ollama": {
    "connected": true,
    "url": "http://localhost:11434",
    "model_count": 2
  }
}
```

### `/api/config` — Configuration

GET response / PUT request body:

```json
{
  "ollama_url": "http://localhost:11434",
  "server_host": "0.0.0.0",
  "server_port": 11435
}
```

## Client Configuration

To use ollama-server instead of Ollama directly, clients just change the base URL:

**Before (direct Ollama):**
```
http://localhost:11434
```

**After (via ollama-server):**
```
http://<server-ip>:11435
```

No other code changes needed — the API is identical.

---

# Interface Comparison: ollama-server vs notetaker's Ollama Integration

## Summary

**The interfaces are compatible but not identical.**

ollama-server provides a **superset** of what notetaker needs. Notetaker can use ollama-server with zero code changes — just update the `base_url` in config.

## Detailed Comparison

| Aspect | notetaker | ollama-server |
|---|---|---|
| `/api/generate` | Yes (primary endpoint) | Yes |
| `/api/chat` | **No** (not used) | Yes |
| `/api/tags` | Yes (health check + model discovery) | Yes |
| `/api/ps` | No | Yes |
| `/api/pull` | No | Yes (for web UI) |
| `/api/delete` | No | Yes (for web UI) |
| Streaming | Yes | Yes |
| JSON mode | Yes (`"format": "json"`) | Yes (pass-through) |

## Why the Differences?

### notetaker doesn't use `/api/chat`

Notetaker uses completion-style prompts via `/api/generate`. System prompts are prepended to user prompts as a single string:

```python
prompt = f"{system_prompt}\n\n{user_prompt}"
# POST /api/generate with prompt
```

This is a design choice — `/api/generate` is simpler and sufficient for notetaker's summarization use case. The chat endpoint's message history management isn't needed.

### ollama-server includes `/api/chat`

ollama-server supports `/api/chat` because `cold-local-llm-server` uses it. The proxy is designed to work with multiple clients that may have different needs.

### ollama-server includes model management endpoints

`/api/pull` and `/api/delete` exist for the web UI, allowing model management without using the CLI. Notetaker doesn't need these — it assumes models are already installed.

## Migration Path

For notetaker to use ollama-server:

1. Update `config.json`:
   ```json
   {
     "providers": {
       "ollama": {
         "base_url": "http://<server-ip>:11435"
       }
     }
   }
   ```

2. Disable auto-launch (optional but recommended when using remote server)

That's it. The `/api/generate` and `/api/tags` endpoints notetaker uses are fully compatible.

## What About cold-local-llm-server?

cold-local-llm-server uses `/api/chat` instead of `/api/generate`. ollama-server supports both, so it works with both clients simultaneously.

| Endpoint | notetaker | cold-local-llm-server | ollama-server |
|---|---|---|---|
| `/api/generate` | Yes | No | Yes |
| `/api/chat` | No | Yes | Yes |
| `/api/tags` | Yes | Yes | Yes |
