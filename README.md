AI Behar Platform - Minimal Deployment

This repository contains only the minimal, safe-to-publish files needed to deploy the AI Behar backend with Docker and OpenWebUI.

Included
- Dockerfile
- docker-compose.yml
- requirements.txt
- core/enhanced_platform.py (FastAPI app)
- core/__init__.py
- sql/init.sql (Postgres bootstrap used by docker-compose)
- monitoring/prometheus.yml (optional monitoring)
- deploy.sh (helper script)
- initialize_databases.sh (optional local SQLite initialization)
- .gitignore and .dockerignore
- .env.example (no real secrets)

Not included (on purpose)
- Any .env files with secrets
- Databases, logs, models, archived data, venv, IDE metadata

Quick start
1) Copy env template and adjust as needed (don’t commit .env):
   cp .env.example .env
   # set values as needed; DB_PASSWORD can be provided at runtime

2) Start with Docker Compose:
   docker compose up -d

   Services:
   - API: http://localhost:8000
   - OpenWebUI: http://localhost:8080
   - Ollama: http://localhost:11434 (models directory persisted in volume)
   - Redis, Postgres (if enabled)

3) Check API:
   curl http://localhost:8000/health
   curl http://localhost:8000/status

Security notes
- Never commit real API keys or secrets. Keep them in .env or your orchestrator’s secrets store.
- POSTGRES_PASSWORD is read from DB_PASSWORD env at compose runtime; set it before running in production.

Troubleshooting
- If Docker build fails on heavy dependencies, comment them out in requirements.txt as needed for your target.
- For initial local SQLite usage, run:
   bash initialize_databases.sh

Railway (API-only) notes
- The backend can link to an external OpenWebUI via OPENWEBUI_BASE_URL (e.g., https://chat.example.com).
- If you want LLM chat to work from Railway, set OLLAMA_BASE_URL to a reachable Ollama endpoint (e.g., on your VPS: http://YOUR_VPS_IP:11434).
- After setting variables, redeploy and visit / (root) to use the /chat link or /ui proxy.

License
- Proprietary or TBD by repository owner.
