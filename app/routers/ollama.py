"""Ollama API proxy routes."""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.proxy import proxy_request

router = APIRouter()


@router.get("/api/tags")
async def list_models():
    """List available models."""
    response = await proxy_request("GET", "/api/tags")
    return JSONResponse(
        content=response.json(),
        status_code=response.status_code,
    )


@router.get("/api/ps")
async def list_running_models():
    """List currently running models."""
    response = await proxy_request("GET", "/api/ps")
    return JSONResponse(
        content=response.json(),
        status_code=response.status_code,
    )


@router.post("/api/generate")
async def generate(request: Request):
    """Generate completion - supports streaming."""
    body = await request.json()
    stream = body.get("stream", False)
    
    if stream:
        generator = await proxy_request("POST", "/api/generate", body, stream=True)
        return StreamingResponse(
            generator,
            media_type="application/x-ndjson",
        )
    else:
        response = await proxy_request("POST", "/api/generate", body)
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
        )


@router.post("/api/chat")
async def chat(request: Request):
    """Chat completion - supports streaming."""
    body = await request.json()
    stream = body.get("stream", False)
    
    if stream:
        generator = await proxy_request("POST", "/api/chat", body, stream=True)
        return StreamingResponse(
            generator,
            media_type="application/x-ndjson",
        )
    else:
        response = await proxy_request("POST", "/api/chat", body)
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
        )


@router.post("/api/pull")
async def pull_model(request: Request):
    """Pull a model - streams progress."""
    body = await request.json()
    # Pull always streams progress updates
    generator = await proxy_request("POST", "/api/pull", body, stream=True)
    return StreamingResponse(
        generator,
        media_type="application/x-ndjson",
    )


@router.delete("/api/delete")
async def delete_model(request: Request):
    """Delete a model."""
    body = await request.json()
    response = await proxy_request("DELETE", "/api/delete", body)
    return JSONResponse(
        content=response.json() if response.text else {"status": "success"},
        status_code=response.status_code,
    )
