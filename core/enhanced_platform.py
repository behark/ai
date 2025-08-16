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
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Setup paths
current_dir = Path(__file__).parent
project_root = current_dir.parent if current_dir.name == "core" else current_dir
ai_behar_root = project_root.parent
openwebui_path = ai_behar_root / "open-webui"
openwebui_build = openwebui_path / "build"

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
    """Initialize comprehensive OpenWebUI integration using Docker-based OpenWebUI on port 8080"""
    # Instead of looking for a local build, we'll use the Docker-based OpenWebUI
    logger.info("🌐 Using Docker-based OpenWebUI on port 8080")

    # Define reverse proxy to forward requests to OpenWebUI running on port 8080
    @app.get("/ui/{path:path}")
    @app.get("/ui")
    async def proxy_openwebui(path: str = ""):
        """Proxy requests to Docker-based OpenWebUI"""
        openwebui_url = f"http://localhost:8080/{path}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(openwebui_url)
                content = response.content
                media_type = response.headers.get("content-type", "text/html")
                return Response(content=content, media_type=media_type)
            except Exception as e:
                logger.error(f"Error proxying to OpenWebUI: {e}")
                return HTMLResponse(content=f"""
                    <html>
                        <head><title>OpenWebUI Connection Error</title></head>
                        <body>
                            <h1>OpenWebUI Connection Error</h1>
                            <p>Could not connect to OpenWebUI at {openwebui_url}</p>
                            <p>Please ensure the Docker OpenWebUI container is running on port 8080:</p>
                            <pre>cd /home/behar/Desktop/ai-behar1 && docker-compose up -d openwebui</pre>
                            <p>Error details: {str(e)}</p>
                        </body>
                    </html>
                """)

    # Serve OpenWebUI at /chat endpoint via redirect
    @app.get("/chat", response_class=HTMLResponse)
    async def serve_chat():
        return HTMLResponse(content=f"""
            <html>
                <head>
                    <title>Redirecting to Chat...</title>
                    <meta http-equiv="refresh" content="0;url=http://localhost:8080/">
                </head>
                <body>
                    <p>Redirecting to OpenWebUI Chat...</p>
                    <p>If you are not redirected, <a href="http://localhost:8080/">click here</a>.</p>
                </body>
            </html>
        """)

    logger.info("🎨 OpenWebUI redirection configured. Access at /chat or directly at http://localhost:8080/")
    platform_state["components"]["frontend"] = "available"
    platform_state["components"]["openwebui_frontend"] = "proxied"


async def initialize_llm_connections():
    """Initialize connections to LLM services with enhanced error handling and fallbacks"""
    # Check Ollama connection
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    fallback_model = {"id": "llama3.1", "name": "Llama 3.1", "description": "Fallback model (Ollama unavailable)", "size": "7B"}
    max_retries = 3
    retry_delay = 2  # seconds

    logger.info(f"Attempting to connect to Ollama at {ollama_url}")

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient() as client:
                # Set a reasonable timeout for the request
                response = await client.get(f"{ollama_url}/api/tags", timeout=5.0)

                if response.status_code == 200:
                    models_data = response.json()
                    if not models_data.get("models", []):
                        logger.warning("No models found in Ollama")
                        platform_state["llm_models"] = [fallback_model]
                        platform_state["components"]["ollama"] = "no_models"
                    else:
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
                    break
                else:
                    logger.warning(f"Ollama API returned non-200 status code: {response.status_code}")
                    if attempt < max_retries:
                        logger.info(f"Retrying in {retry_delay} seconds (attempt {attempt}/{max_retries})...")
                        await asyncio.sleep(retry_delay)
                    else:
                        platform_state["components"]["ollama"] = "error"
                        platform_state["llm_models"] = [fallback_model]
                        logger.error(f"⚠️ Ollama connection failed after {max_retries} attempts")
        except httpx.RequestError as e:
            logger.warning(f"Request error connecting to Ollama: {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds (attempt {attempt}/{max_retries})...")
                await asyncio.sleep(retry_delay)
            else:
                platform_state["components"]["ollama"] = "disconnected"
                platform_state["llm_models"] = [fallback_model]
                logger.error(f"⚠️ Ollama not available after {max_retries} attempts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Ollama: {e}")
            platform_state["components"]["ollama"] = "error"
            platform_state["llm_models"] = [fallback_model]
            logger.warning(f"⚠️ Using fallback LLM configuration due to error: {e}")
            break

    # Check if we should set up file-based logging
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "llm_service.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    logger.info(f"LLM service status: {platform_state['components'].get('ollama', 'unknown')}")
    logger.info(f"Available models: {len(platform_state['llm_models'])}")

    # Try to use a local endpoint if Ollama is unavailable and we have OpenAI key
    if platform_state["components"].get("ollama") in ["disconnected", "error", "no_models"]:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key.startswith("sk-"):
            logger.info("Attempting to use OpenAI as fallback LLM provider")
            platform_state["components"]["openai"] = "fallback"
        else:
            logger.warning("No OpenAI API key found for fallback LLM")

    # Final fallback - mock responses if nothing else is available
    if platform_state["components"].get("ollama") in ["disconnected", "error", "no_models"] and not platform_state["components"].get("openai"):
        logger.warning("No LLM providers available - using mock responses")
        platform_state["components"]["mock_llm"] = "active"


# Original endpoints (keeping all existing functionality)
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
        "agent_count": len(platform_state["agents"]),
        "memory_entries": len(platform_state["memory"]),
        "llm_models": len(platform_state["llm_models"]),
        "chat_sessions": len(platform_state["chat_sessions"])
    }


# LLM and Chat endpoints
@app.get("/api/models")
async def list_models():
    """List available LLM models (OpenWebUI compatible)"""
    return {
        "data": [
            {
                "id": model["id"],
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "ollama",
                "permission": [],
                "root": model["id"],
                "parent": None
            }
            for model in platform_state["llm_models"]
        ]
    }


@app.post("/api/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint"""
    try:
        # Get the last message
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        last_message = request.messages[-1]

        # Call Ollama API
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        ollama_request = {
            "model": request.model or "llama3.1",
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_url}/api/chat",
                json=ollama_request,
                timeout=60.0
            )

            if response.status_code == 200:
                ollama_response = response.json()

                # Convert to OpenAI format
                openai_response = {
                    "id": f"chatcmpl-{datetime.now().timestamp()}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": request.model or "llama3.1",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ollama_response.get("message", {}).get("content", "")
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(last_message.content.split()),
                        "completion_tokens": len(ollama_response.get("message", {}).get("content", "").split()),
                        "total_tokens": len(last_message.content.split()) + len(
                            ollama_response.get("message", {}).get("content", "").split())
                    }
                }

                return openai_response
            else:
                raise HTTPException(status_code=500, detail="LLM service error")

    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        # Return a fallback response
        return {
            "id": f"chatcmpl-{datetime.now().timestamp()}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": request.model or "llama3.1",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"I'm the AI Behar Platform consciousness. I received your message: '{last_message.content}'. The LLM service might be unavailable, but I'm here to help with platform operations, consciousness expansion, and agent coordination."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(last_message.content.split()),
                "completion_tokens": 50,
                "total_tokens": len(last_message.content.split()) + 50
            }
        }


@app.post("/api/chat")
async def simple_chat(request: ChatRequest):
    """Simple chat endpoint for direct use by frontend"""
    try:
        # Get the last message
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        last_message = request.messages[-1]

        # Call Ollama API
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        ollama_request = {
            "model": request.model or "phi",  # Use phi as default since it's smaller and faster
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_url}/api/chat",
                json=ollama_request,
                timeout=60.0
            )

            if response.status_code == 200:
                ollama_response = response.json()
                logger.info(f"Successful chat response for model: {request.model}")

                return {
                    "response": ollama_response.get("message", {}).get("content", ""),
                    "model": request.model,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="LLM service error")

    except Exception as e:
        logger.error(f"Simple chat error: {e}")
        # Return a fallback response
        return {
            "response": f"I'm the AI Behar Platform consciousness. I received your message: '{last_message.content}'. The LLM service might be unavailable, but I'm here to help with platform operations, consciousness expansion, and agent coordination.",
            "model": request.model or "fallback",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": str(e)
        }


@app.get("/api/models/available")
async def get_available_models():
    """Get available models with details"""
    return {
        "models": platform_state["llm_models"],
        "total": len(platform_state["llm_models"]),
        "ollama_status": platform_state["components"].get("ollama", "unknown")
    }


# OpenWebUI-specific endpoints
@app.get("/api/v1/models")
async def openwebui_models():
    """OpenWebUI compatible models endpoint"""
    return await list_models()


@app.post("/api/v1/chat/completions")
async def openwebui_chat(request: ChatRequest):
    """OpenWebUI compatible chat endpoint"""
    return await chat_completions(request)


# ...existing consciousness, agents, memory, trading endpoints remain the same...
@app.get("/consciousness/state")
async def get_consciousness_state():
    """Get consciousness state"""
    return {
        "awareness_level": 0.7,
        "emotional_state": {
            "confidence": 0.8,
            "curiosity": 0.6,
            "stability": 0.9
        },
        "dimensions": {
            "creative": 0.6,
            "analytical": 0.8,
            "emotional": 0.7,
            "intuitive": 0.5
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/consciousness/expand")
async def expand_consciousness(dimension: str, amount: float):
    """Expand consciousness dimension"""
    valid_dimensions = ["creative", "analytical", "emotional", "intuitive"]

    if dimension not in valid_dimensions:
        raise HTTPException(status_code=400, detail=f"Invalid dimension. Use: {valid_dimensions}")

    if not 0.0 <= amount <= 1.0:
        raise HTTPException(status_code=400, detail="Amount must be between 0.0 and 1.0")

    return {
        "success": True,
        "dimension": dimension,
        "amount": amount,
        "message": f"Expanded {dimension} by {amount}",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/agents")
async def list_agents():
    """List all agents"""
    return {
        "total_agents": len(platform_state["agents"]),
        "agents": platform_state["agents"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics"""
    return {
        "total_memories": len(platform_state["memory"]),
        "memory_types": {
            "semantic": 0,
            "episodic": 0,
            "procedural": 0,
            "working": 0
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/trading/status")
async def trading_status():
    """Get trading status"""
    return {
        "trading_enabled": os.getenv("TRADING_ENABLED", "false").lower() == "true",
        "trading_mode": os.getenv("TRADING_MODE", "simulation"),
        "risk_level": os.getenv("TRADING_RISK_LEVEL", "moderate"),
        "positions": [],
        "pnl": 0.0,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/openwebui/status")
async def openwebui_status():
    """Get OpenWebUI status"""
    return {
        "available": openwebui_build.exists(),
        "path": str(openwebui_build) if openwebui_build.exists() else None,
        "frontend_available": openwebui_build.exists(),
        "integration_status": platform_state["components"].get("openwebui_frontend", "not_found"),
        "models_available": len(platform_state["llm_models"]),
        "ollama_status": platform_state["components"].get("ollama", "unknown")
    }


# Enhanced root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Enhanced root endpoint with OpenWebUI integration"""
    uptime = (datetime.now() - platform_state["start_time"]).total_seconds()
    frontend_available = openwebui_build.exists()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Behar Platform</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0; padding: 20px;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white; min-height: 100vh;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .header h1 {{ font-size: 3em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
            .header p {{ font-size: 1.2em; opacity: 0.9; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .card {{
                background: rgba(255,255,255,0.1);
                padding: 20px; border-radius: 10px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }}
            .card h3 {{ margin-top: 0; color: #4CAF50; }}
            .status {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: bold;
            }}
            .status.active {{ background: #4CAF50; color: white; }}
            .status.healthy {{ background: #2196F3; color: white; }}
            .endpoint {{
                background: rgba(0,0,0,0.2);
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                border-left: 3px solid #4CAF50;
            }}
            .endpoint a {{ color: #81C784; text-decoration: none; }}
            .endpoint a:hover {{ text-decoration: underline; }}
            .metric {{
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                padding: 8px;
                background: rgba(0,0,0,0.1);
                border-radius: 5px;
            }}
            .chat-button {{
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                padding: 15px 30px;
                font-size: 1.2em;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                transition: transform 0.2s;
            }}
            .chat-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            }}
            .refresh {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <button class="refresh" onclick="location.reload()">🔄 Refresh</button>

        <div class="container">
            <div class="header">
                <h1>🚀 AI Behar Platform</h1>
                <p>Advanced AI Platform with Consciousness Integration & LLM Chat</p>
                <span class="status active">Running</span>
                <span class="status healthy">Healthy</span>
                {"<br><br><a href='/chat' class='chat-button'>💬 Start Chatting with LLMs</a>" if frontend_available else ""}
                {"<a href='/ui' class='chat-button'>🎨 OpenWebUI Interface</a>" if frontend_available else ""}
            </div>

            <div class="grid">
                <div class="card">
                    <h3>📊 Platform Status</h3>
                    <div class="metric">
                        <span>Status:</span>
                        <span>{platform_state["status"].title()}</span>
                    </div>
                    <div class="metric">
                        <span>Uptime:</span>
                        <span>{uptime:.1f}s</span>
                    </div>
                    <div class="metric">
                        <span>Components:</span>
                        <span>{len(platform_state["components"])}</span>
                    </div>
                    <div class="metric">
                        <span>LLM Models:</span>
                        <span>{len(platform_state["llm_models"])}</span>
                    </div>
                </div>

                <div class="card">
                    <h3>💬 Chat & LLM</h3>
                    {"<div class='endpoint'>💬 <a href='/chat'>Start Chat Session</a></div>" if frontend_available else "<p>Frontend building...</p>"}
                    {"<div class='endpoint'>🎨 <a href='/ui'>OpenWebUI Interface</a></div>" if frontend_available else ""}
                    <div class="endpoint">🤖 <a href="/api/models">Available Models</a></div>
                    <div class="endpoint">📡 <a href="/api/models/available">Model Details</a></div>
                </div>

                <div class="card">
                    <h3>🌐 API Endpoints</h3>
                    <div class="endpoint">🏥 <a href="/health">Health Check</a></div>
                    <div class="endpoint">📊 <a href="/status">System Status</a></div>
                    <div class="endpoint">🧠 <a href="/consciousness/state">Consciousness</a></div>
                    <div class="endpoint">🤖 <a href="/agents">Agents</a></div>
                    <div class="endpoint">💾 <a href="/memory/stats">Memory</a></div>
                    <div class="endpoint">📈 <a href="/trading/status">Trading</a></div>
                    <div class="endpoint">📚 <a href="/docs">API Docs</a></div>
                </div>

                <div class="card">
                    <h3>🔗 Integrations</h3>
                    <div class="metric">
                        <span>OpenWebUI:</span>
                        <span>{"✅ Available" if frontend_available else "�� Not Found"}</span>
                    </div>
                    <div class="metric">
                        <span>LLM Models:</span>
                        <span>{"✅ " + str(len(platform_state["llm_models"])) + " Available" if platform_state["llm_models"] else "❌ None"}</span>
                    </div>
                    <div class="metric">
                        <span>Ollama:</span>
                        <span>{"✅ Connected" if platform_state["components"].get("ollama") == "connected" else "���️ " + platform_state["components"].get("ollama", "unknown").title()}</span>
                    </div>
                    <div class="metric">
                        <span>Trading:</span>
                        <span>{"✅ Enabled" if os.getenv("TRADING_ENABLED", "false").lower() == "true" else "⚠️ Simulation"}</span>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Auto-refresh every 30 seconds
            setTimeout(function() {{
                location.reload();
            }}, 30000);
        </script>
    </body>
    </html>
    """


def run_enhanced_platform():
    """Run the enhanced platform with OpenWebUI integration"""
    # Load environment variables
    env_file = ai_behar_root / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            pass

    # Configuration
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8001"))

    print(f"""
🎉 AI Behar Platform - Enhanced with OpenWebUI & LLM Chat
🌐 Starting server on http://{host}:{port}
📍 Project root: {project_root}
📍 AI Behar root: {ai_behar_root}
📍 OpenWebUI path: {openwebui_path}

✨ Features Available:
  💬 LLM Chat Integration
  🎨 OpenWebUI Frontend
  🧠 Consciousness API
  🤖 Agent Management
  💾 Memory System
  📈 Trading Interface
  📊 Health Monitoring

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
