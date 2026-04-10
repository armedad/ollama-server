"""Ollama API proxy logic."""

from __future__ import annotations

from typing import AsyncGenerator, Optional, Union

import httpx

from app.config import get_ollama_url

# Timeout settings
CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 300.0  # 5 minutes for long generations


async def check_ollama_status() -> dict:
    """Check if Ollama is reachable and get basic info."""
    url = get_ollama_url()
    try:
        async with httpx.AsyncClient(timeout=CONNECT_TIMEOUT) as client:
            response = await client.get(f"{url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return {
                    "connected": True,
                    "url": url,
                    "model_count": len(data.get("models", [])),
                }
            return {
                "connected": False,
                "url": url,
                "error": f"Unexpected status: {response.status_code}",
            }
    except httpx.ConnectError:
        return {
            "connected": False,
            "url": url,
            "error": "Connection refused - is Ollama running?",
        }
    except httpx.TimeoutException:
        return {
            "connected": False,
            "url": url,
            "error": "Connection timeout",
        }
    except Exception as e:
        return {
            "connected": False,
            "url": url,
            "error": str(e),
        }


async def proxy_request(
    method: str,
    path: str,
    body: Optional[dict] = None,
    stream: bool = False,
) -> Union[httpx.Response, AsyncGenerator[bytes, None]]:
    """
    Proxy a request to Ollama.
    
    For streaming requests, returns an async generator of bytes.
    For non-streaming, returns the response object.
    """
    url = f"{get_ollama_url()}{path}"
    timeout = httpx.Timeout(CONNECT_TIMEOUT, read=READ_TIMEOUT)
    
    if stream:
        return _stream_request(method, url, body, timeout)
    else:
        return await _simple_request(method, url, body, timeout)


async def _simple_request(
    method: str,
    url: str,
    body: Optional[dict],
    timeout: httpx.Timeout,
) -> httpx.Response:
    """Make a non-streaming request."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method == "GET":
            return await client.get(url)
        elif method == "POST":
            return await client.post(url, json=body)
        elif method == "DELETE":
            return await client.request("DELETE", url, json=body)
        else:
            raise ValueError(f"Unsupported method: {method}")


async def _stream_request(
    method: str,
    url: str,
    body: Optional[dict],
    timeout: httpx.Timeout,
) -> AsyncGenerator[bytes, None]:
    """Stream a request and yield chunks."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(method, url, json=body) as response:
            async for chunk in response.aiter_bytes():
                yield chunk
