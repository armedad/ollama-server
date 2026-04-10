"""Management routes for config and status."""

from fastapi import APIRouter

from app.config import get_config, update_config
from app.proxy import check_ollama_status

router = APIRouter()


@router.get("/api/status")
async def get_status():
    """Health check and Ollama connectivity status."""
    ollama_status = await check_ollama_status()
    return {
        "status": "ok",
        "ollama": ollama_status,
    }


@router.get("/api/config")
async def get_config_endpoint():
    """Get current configuration."""
    return get_config()


@router.put("/api/config")
async def update_config_endpoint(updates: dict):
    """Update configuration."""
    # Only allow updating specific fields
    allowed_fields = {"ollama_url", "server_host", "server_port"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        return {"error": "No valid fields to update"}
    
    config = update_config(filtered_updates)
    return config
