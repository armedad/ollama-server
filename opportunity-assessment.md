# Ollama Server - Opportunity Assessment

## Objective

Create a shared Ollama proxy server that centralizes LLM access for multiple applications. Instead of each app managing its own Ollama connection, they connect to this shared server which handles Ollama interaction, configuration, and management.

## Target Customer

- Me (the developer) running multiple AI-powered apps that need local LLM access
- Apps like `cold-local-llm-server` and `notetaker` that currently connect directly to Ollama
- Scenario: lightweight machines (laptops, etc.) connecting to a stronger machine running Ollama

## Success

1. Both `cold-local-llm-server` and `notetaker` can use this shared server instead of direct Ollama connections
2. Server can run on a separate (stronger) machine and be accessed over the network
3. Web UI allows configuration of Ollama settings without needing to SSH into the server
4. Configuration persists in `config.json`
5. Minimal code changes needed in consuming apps (just change the Ollama URL)

## What I Believe

- A proxy layer adds value beyond just "use Ollama on another machine" because:
  - Provides a management UI for model configuration
  - Can add logging/visibility into usage
  - Centralizes Ollama-specific configuration
  - Future: could add auth, rate limiting, model aliasing
- Both existing apps already support configurable Ollama URLs, so integration should be straightforward
- The proxy should be transparent enough that apps don't need to know they're talking to a proxy vs direct Ollama

## What I Need to Research

- Whether to pass through Ollama API exactly or create a simplified abstraction
- Network security considerations when exposing over LAN

## Solution Direction

A Python FastAPI server that:
1. **Proxies Ollama API** - Forwards requests to the actual Ollama instance
2. **Web UI** - Simple frontend to:
   - View available models
   - Pull/delete models
   - Configure Ollama URL (in case Ollama runs elsewhere)
   - View basic usage stats
3. **Config persistence** - `config.json` for server settings
4. **Health/status endpoints** - For clients to check connectivity

### API Compatibility

Since the two existing apps use different Ollama endpoints:
- `cold-local-llm-server` uses: `GET /api/tags`, `POST /api/chat`
- `notetaker` uses: `GET /api/tags`, `POST /api/generate`

The proxy should support both, passing through to Ollama transparently.

## Risks to Validate

1. **Streaming support** - Both apps use streaming; must work through proxy
   - Validate: Test streaming responses early
2. **Latency overhead** - Extra hop shouldn't noticeably slow things down
   - Validate: Benchmark proxy vs direct connection
3. **Network exposure** - Running on LAN introduces security considerations
   - Validate: Decide on auth requirements (start simple, add later if needed)

## Parking Lot (Out of Scope for v1)

- Authentication/access control (assume trusted LAN)
- Rate limiting
- Model aliasing/routing
- Usage analytics beyond basic logging
- Multi-Ollama-instance load balancing
- Automatic Ollama installation/management

---

## Detailed Spec

### Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  cold-local-llm     │────▶│                     │     │                 │
│      server         │     │   ollama-server     │────▶│     Ollama      │
└─────────────────────┘     │   (this project)    │     │  (localhost or  │
                            │                     │     │   remote)       │
┌─────────────────────┐     │  ┌───────────────┐  │     └─────────────────┘
│     notetaker       │────▶│  │  Web UI       │  │
│                     │     │  │  (config/mgmt)│  │
└─────────────────────┘     │  └───────────────┘  │
                            │                     │
┌─────────────────────┐     │  ┌───────────────┐  │
│  Future apps...     │────▶│  │ config.json   │  │
└─────────────────────┘     │  └───────────────┘  │
                            └─────────────────────┘
```

### Core Requirements

#### 1. Ollama API Proxy (transparent pass-through)

Proxy the following Ollama endpoints:
- `GET /api/tags` - List models
- `POST /api/generate` - Generate completions (streaming + non-streaming)
- `POST /api/chat` - Chat completions (streaming + non-streaming)
- `POST /api/pull` - Pull a model (for web UI)
- `DELETE /api/delete` - Delete a model (for web UI)
- `GET /api/ps` - List running models (for status display)

The proxy should:
- Forward requests to the configured Ollama URL
- Support streaming responses (SSE)
- Pass through all headers and parameters unchanged
- Return Ollama errors transparently

#### 2. Configuration System

`config.json` structure:
```json
{
  "ollama_url": "http://localhost:11434",
  "server_host": "0.0.0.0",
  "server_port": 11435
}
```

- `ollama_url`: Where the actual Ollama instance is running
- `server_host`: What interface to bind to (0.0.0.0 for network access)
- `server_port`: Port for this proxy server (different from Ollama's 11434)

Configuration should be:
- Loaded at startup
- Editable via Web UI
- Persisted to disk on change

#### 3. Web UI

Simple single-page interface with:

**Status Panel:**
- Connection status to Ollama
- Currently loaded model(s)

**Models Panel:**
- List available models (name, size, modified date)
- Pull new model (input field + button)
- Delete model (with confirmation)

**Settings Panel:**
- Edit Ollama URL
- View/edit server port
- Save button

**Tech stack:**
- Vanilla HTML/CSS/JavaScript (no build step)
- Served as static files from FastAPI
- Fetch API for AJAX calls

#### 4. Server Endpoints (non-Ollama)

- `GET /` - Serve web UI
- `GET /api/config` - Get current config
- `PUT /api/config` - Update config
- `GET /api/status` - Health check + Ollama connectivity status

### File Structure

```
ollama-server/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, startup, static files
│   ├── config.py         # Config loading/saving
│   ├── proxy.py          # Ollama API proxy logic
│   └── routers/
│       ├── __init__.py
│       ├── ollama.py     # Proxy routes for Ollama API
│       └── management.py # Config and status routes
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── config.json           # Runtime config (gitignored)
├── config.example.json   # Example config (committed)
├── requirements.txt
├── AGENTS.md
└── README.md
```

### Security Considerations

For v1 (trusted LAN):
- Bind to 0.0.0.0 to allow network access
- No authentication
- Document the security implications in README

Future considerations (parking lot):
- Optional API key authentication
- IP allowlist
- HTTPS support

### Integration with Existing Apps

**cold-local-llm-server:**
- Change `OLLAMA_URL` env var or `settings.json` to point to `http://<server-ip>:11435`
- No code changes needed

**notetaker:**
- Change `config.json` → `providers.ollama.base_url` to `http://<server-ip>:11435`
- May need to disable auto-launch logic when using remote server
- Minimal code changes

---

## Implementation Plan

### Phase 0: Project Setup
**Goal:** Skeleton FastAPI app with health check
**Files:** `app/main.py`, `requirements.txt`, `config.example.json`
**Done means:** `python -m uvicorn app.main:app` starts, `GET /api/status` returns JSON

### Phase 1: Configuration System
**Goal:** Load/save config from `config.json`
**Files:** `app/config.py`, `app/routers/management.py`
**Done means:** Config loads at startup, `GET /api/config` returns it, `PUT /api/config` persists changes

### Phase 2: Ollama Proxy (Non-Streaming)
**Goal:** Proxy `/api/tags` and non-streaming `/api/generate`, `/api/chat`
**Files:** `app/proxy.py`, `app/routers/ollama.py`
**Done means:** Point notetaker/cold-local-llm at this server, non-streaming requests work

### Phase 3: Streaming Support
**Goal:** Streaming responses for `/api/generate` and `/api/chat`
**Files:** Update `app/proxy.py`, `app/routers/ollama.py`
**Done means:** Streaming requests from both apps work through proxy

### Phase 4: Web UI - Status & Models
**Goal:** Basic web interface showing status and model list
**Files:** `static/index.html`, `static/style.css`, `static/app.js`
**Done means:** Browser shows connected status and lists models

### Phase 5: Web UI - Model Management
**Goal:** Pull and delete models from UI
**Files:** Update `static/app.js`, add proxy for `/api/pull`, `/api/delete`
**Done means:** Can pull new model and delete existing model from UI

### Phase 6: Web UI - Settings
**Goal:** Edit and save configuration from UI
**Files:** Update `static/index.html`, `static/app.js`
**Done means:** Can change Ollama URL from UI, changes persist

### Phase 7: Documentation & Polish
**Goal:** README, cleanup, final testing
**Files:** `README.md`, `AGENTS.md`, `.gitignore`
**Done means:** Fresh clone can follow README to get running
