#!/usr/bin/env python3
"""
Enhanced Platform with OpenWebUI and LLM Integration

This launcher integrates your OpenWebUI frontend and adds LLM chat capabilities.
"""

import logging
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Setup paths
current_dir = Path(__file__).parent
project_root = current_dir.parent if current_dir.name == "core" else current_dir
ai_behar_root = project_root.parent
openwebui_path = ai_behar_root / "open-webui"

# OpenWebUI base URL (can be remote when deployed)
OPENWEBUI_BASE_URL = os.getenv("OPENWEBUI_BASE_URL", "http://localhost:8080").rstrip("/")

# Add to Python path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(ai_behar_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Behar Platform - Complete with OpenWebUI",
    description="Full AI platform with OpenWebUI frontend and LLM chat capabilities",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for custom frontend
static_files = ["styles.css", "script.js", "index.html"]
for file in static_files:
    file_path = project_root / file
    if file_path.exists():
        if file == "index.html":
            continue  # Handle index.html separately
        app.mount(f"/{file}", StaticFiles(directory=str(project_root)), name=file.replace('.', '_'))

logger.info(f"📁 Static files checked in: {project_root}")

# Global state
platform_state = {
    "status": "starting",
    "start_time": datetime.now(),
    "components": {},
    "agents": {},
    "memory": {},
    "health": {"status": "healthy"},
    "llm_models": [],
    "chat_sessions": {}
}

# Pydantic models for API
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "llama3.1"
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

class ModelInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    size: Optional[str] = ""

@app.on_event("startup")
async def startup_event():
    """Initialize the enhanced platform with OpenWebUI"""
    logger.info("🚀 Starting AI Behar Platform - Enhanced with OpenWebUI")

    platform_state["status"] = "running"
    platform_state["components"]["api"] = "active"
    platform_state["components"]["consciousness"] = "active"
    platform_state["components"]["agents"] = "active"

    # Initialize OpenWebUI integration
    await initialize_openwebui_integration()

    # Initialize LLM connections
    await initialize_llm_connections()

    logger.info("✅ Enhanced Platform started successfully!")

async def initialize_openwebui_integration():
    """Initialize comprehensive OpenWebUI integration using configurable base URL"""
    logger.info(f"🌐 OpenWebUI base: {OPENWEBUI_BASE_URL}")

    # Define reverse proxy to forward requests to OpenWebUI
    @app.api_route("/ui/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"])
    @app.api_route("/ui", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"])
    async def proxy_openwebui(request: Request, path: str = ""):
        """Proxy requests to OpenWebUI (can be remote)"""
        target = f"{OPENWEBUI_BASE_URL}/{path}" if path else OPENWEBUI_BASE_URL
        # Forward headers except hop-by-hop
        excluded_headers = {"host", "content-length", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"}
        forward_headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded_headers}
        # Forward query params
        params = dict(request.query_params)
        # Forward body if any
        body = await request.body()
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                resp = await client.request(
                    request.method,
                    target,
                    headers=forward_headers,
                    params=params,
                    content=body,
                    timeout=60.0,
                )
                # Filter response headers
                excluded_resp_headers = {"content-encoding", "transfer-encoding", "connection"}
                response_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded_resp_headers}
                return Response(content=resp.content, status_code=resp.status_code, headers=response_headers, media_type=resp.headers.get("content-type"))
            except Exception as e:
                logger.error(f"Error proxying to OpenWebUI: {e}")
                return HTMLResponse(content=f"<html><body><h1>OpenWebUI Connection Error</h1><p>Could not connect to OpenWebUI at {target}</p></body></html>", status_code=502)

    # Serve OpenWebUI at /chat endpoint via redirect
    @app.get("/chat", response_class=HTMLResponse)
    async def serve_chat():
        return HTMLResponse(content=f'<html><head><meta http-equiv="refresh" content="0;url={OPENWEBUI_BASE_URL}/"></head><body><p>Redirecting to OpenWebUI Chat...</p></body></html>')

    logger.info("🎨 OpenWebUI redirection configured. Access via /chat or /ui")
    platform_state["components"]["frontend"] = "configured"
    platform_state["components"]["openwebui_frontend"] = "proxied"

async def initialize_llm_connections():
    """Initialize connections to LLM services"""
    # Check Ollama connection
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    fallback_model = {"id": "llama3.1", "name": "Llama 3.1", "description": "Fallback model", "size": "7B"}

    logger.info(f"Attempting to connect to Ollama at {ollama_url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models_data = response.json()
                if models_data.get("models", []):
                    platform_state["llm_models"] = [
                        {
                            "id": model["name"],
                            "name": model["name"],
                            "description": f"Ollama model - {model.get('size', 'Unknown size')}",
                            "size": model.get("size", "Unknown")
                        }
                        for model in models_data.get("models", [])
                    ]
                    platform_state["components"]["ollama"] = "connected"
                    logger.info(f"🦙 Ollama connected: {len(platform_state['llm_models'])} models available")
                else:
                    platform_state["llm_models"] = [fallback_model]
                    platform_state["components"]["ollama"] = "no_models"
            else:
                platform_state["llm_models"] = [fallback_model]
                platform_state["components"]["ollama"] = "error"
    except Exception as e:
        platform_state["llm_models"] = [fallback_model]
        platform_state["components"]["ollama"] = "disconnected"
        logger.error(f"⚠️ Ollama connection failed: {e}")

# Serve custom frontend at root
@app.get("/", response_class=HTMLResponse)
async def serve_custom_frontend():
    """Serve OpenWebUI by default when reachable; otherwise the built-in dashboard"""
    # Prefer OpenWebUI if configured and reachable
    if OPENWEBUI_BASE_URL:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(OPENWEBUI_BASE_URL, timeout=1.5)
                if resp.status_code < 500:
                    return RedirectResponse(url="/ui", status_code=307)
        except Exception:
            # Fall back to dashboard if not reachable
            pass

    # Fallback: Serve index.html if present, otherwise the built-in dashboard
    index_path = project_root / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return await serve_dashboard()

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the built-in dashboard"""
    uptime = (datetime.now() - platform_state["start_time"]).total_seconds()
    frontend_available = bool(OPENWEBUI_BASE_URL)

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Behar Platform</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white; min-height: 100vh; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .header h1 {{ font-size: 3em; margin: 0; }}
            .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px;
                      font-size: 0.9em; font-weight: bold; margin: 5px; }}
            .status.active {{ background: #4CAF50; color: white; }}
            .status.healthy {{ background: #2196F3; color: white; }}
            .chat-button {{ background: linear-gradient(45deg, #4CAF50, #45a049);
                           color: white; padding: 15px 30px; font-size: 1.2em;
                           border: none; border-radius: 25px; cursor: pointer;
                           text-decoration: none; display: inline-block; margin: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 AI Behar Platform</h1>
                <p>Advanced AI Platform with Consciousness Integration & LLM Chat</p>
                <span class="status active">Running</span>
                <span class="status healthy">Healthy</span>
                <br><br>
                {"<a href='/chat' class='chat-button'>💬 Open WebUI Chat</a>" if frontend_available else ""}
                {"<a href='/ui' class='chat-button'>🎨 Proxy OpenWebUI</a>" if frontend_available else ""}
                <a href="/health" class="chat-button">🏥 Health Check</a>
                <a href="/docs" class="chat-button">📚 API Docs</a>
            </div>
            <div style="text-align: center;">
                <h3>Platform Status</h3>
                <p>Status: {platform_state["status"].title()}</p>
                <p>Uptime: {uptime:.1f}s</p>
                <p>Components: {len(platform_state["components"])}</p>
                <p>LLM Models: {len(platform_state["llm_models"])}</p>
            </div>
        </div>
        <script>
            setTimeout(function() {{ location.reload(); }}, 30000);
        </script>
    </body>
    </html>
    """)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - platform_state["start_time"]).total_seconds()
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "timestamp": datetime.now().isoformat(),
        "platform_status": platform_state["status"],
        "components": platform_state["components"],
        "llm_models_available": len(platform_state["llm_models"])
    }

@app.get("/status")
async def get_status():
    """Get platform status"""
    return {
        "platform": "AI Behar Platform",
        "version": "2.0.0",
        "status": platform_state["status"],
        "uptime": (datetime.now() - platform_state["start_time"]).total_seconds(),
        "components": platform_state["components"],
        "llm_models": len(platform_state["llm_models"])
    }

# LLM and Chat endpoints
@app.get("/api/models")
async def list_models():
    """List available LLM models"""
    return {
        "data": [
            {
                "id": model["id"],
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "ollama"
            }
            for model in platform_state["llm_models"]
        ]
    }

@app.post("/api/chat")
async def simple_chat(request: ChatRequest):
    """Simple chat endpoint for direct use by frontend"""
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        last_message = request.messages[-1]
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        ollama_request = {
            "model": request.model or "phi",
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{ollama_url}/api/chat", json=ollama_request, timeout=60.0)
            if response.status_code == 200:
                ollama_response = response.json()
                return {
                    "response": ollama_response.get("message", {}).get("content", ""),
                    "model": request.model,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            else:
                raise HTTPException(status_code=response.status_code, detail="LLM service error")

    except Exception as e:
        logger.error(f"Simple chat error: {e}")
        return {
            "response": f"I'm the AI Behar Platform consciousness. I received your message: '{last_message.content}'. The LLM service might be unavailable, but I'm here to help with platform operations.",
            "model": request.model or "fallback",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": str(e)
        }

def run_enhanced_platform():
    """Run the enhanced platform with OpenWebUI integration"""
    # Configuration
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))

    print(f"""
🎉 AI Behar Platform - Enhanced with OpenWebUI & LLM Chat
🌐 Starting server on http://{host}:{port}
📍 Project root: {project_root}

🚀 Access Points:
  • Main Dashboard: http://{host}:{port}/
  • Chat Interface: http://{host}:{port}/chat
  • OpenWebUI: http://{host}:{port}/ui
  • API Documentation: http://{host}:{port}/docs
  • Health Check: http://{host}:{port}/health
    """)

    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_enhanced_platform()
