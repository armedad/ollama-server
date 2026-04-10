"""Configuration management for ollama-server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, TypedDict

CONFIG_PATH = Path(__file__).parent.parent / "config.json"
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.example.json"


class Config(TypedDict):
    ollama_url: str
    server_host: str
    server_port: int


DEFAULT_CONFIG: Config = {
    "ollama_url": "http://localhost:11434",
    "server_host": "0.0.0.0",
    "server_port": 11435,
}


def load_config() -> Config:
    """Load config from file, creating from example if needed."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = json.load(f)
            # Merge with defaults to handle missing keys
            return {**DEFAULT_CONFIG, **data}
    
    # If no config exists, check for example config
    if DEFAULT_CONFIG_PATH.exists():
        with open(DEFAULT_CONFIG_PATH) as f:
            data = json.load(f)
            return {**DEFAULT_CONFIG, **data}
    
    return DEFAULT_CONFIG.copy()


def save_config(config: Config) -> None:
    """Save config to file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


# Module-level config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the current config, loading if needed."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def update_config(updates: dict) -> Config:
    """Update config with new values and persist."""
    global _config
    config = get_config()
    config.update(updates)
    save_config(config)
    _config = config
    return config


def get_ollama_url() -> str:
    """Get the configured Ollama URL."""
    return get_config()["ollama_url"]
