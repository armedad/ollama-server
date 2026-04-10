"""Ollama Server - Shared Ollama proxy with web UI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import management, ollama
from app.config import get_config

app = FastAPI(
    title="Ollama Server",
    description="Shared Ollama proxy server with web UI",
    version="0.1.0",
)

# CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(management.router)
app.include_router(ollama.router)

# Static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def serve_ui():
    """Serve the web UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Ollama Server is running. Web UI not found."}


@app.on_event("startup")
async def startup():
    """Load config on startup."""
    config = get_config()
    print(f"Ollama Server starting...")
    print(f"  Proxying to: {config['ollama_url']}")
    print(f"  Listening on: {config['server_host']}:{config['server_port']}")


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    uvicorn.run(
        "app.main:app",
        host=config["server_host"],
        port=config["server_port"],
        reload=True,
    )
