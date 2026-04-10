# Ollama Server

A shared Ollama proxy server that centralizes LLM access for multiple applications.

## Why?

Instead of each app managing its own Ollama connection, they all connect to this server. Benefits:

- **Run Ollama on a powerful machine** - lightweight laptops send requests to a beefy server
- **Centralized configuration** - one place to manage models and settings
- **Web UI** - pull models, view status, configure settings from a browser

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy example config
cp config.example.json config.json

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 11435
```

Open http://localhost:11435 in your browser for the Web UI.

## Configuration

Edit `config.json`:

```json
{
  "ollama_url": "http://localhost:11434",
  "server_host": "0.0.0.0",
  "server_port": 11435
}
```

- `ollama_url`: Where the actual Ollama instance is running
- `server_host`: Interface to bind (use `0.0.0.0` for network access)
- `server_port`: Port for this proxy server

## Using with Other Apps

Point your apps to this server instead of Ollama directly:

### cold-local-llm-server

Set environment variable:
```bash
OLLAMA_URL=http://<server-ip>:11435
```

Or update `settings.json`:
```json
{
  "ollama_url": "http://<server-ip>:11435"
}
```

### notetaker

Update `config.json`:
```json
{
  "providers": {
    "ollama": {
      "base_url": "http://<server-ip>:11435"
    }
  }
}
```

## API

### Ollama Proxy Endpoints

These pass through to Ollama unchanged:

- `GET /api/tags` - List models
- `POST /api/generate` - Generate completion
- `POST /api/chat` - Chat completion
- `POST /api/pull` - Pull a model
- `DELETE /api/delete` - Delete a model
- `GET /api/ps` - List running models

### Management Endpoints

- `GET /` - Web UI
- `GET /api/status` - Health check + Ollama status
- `GET /api/config` - Get current config
- `PUT /api/config` - Update config

## Security

This server is designed for **trusted LAN use only**:

- No authentication
- Binds to 0.0.0.0 (accessible from network)
- Do NOT expose to public internet

For production use, add authentication or run behind a reverse proxy with auth.

## Development

```bash
# Run with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 11435
```
