import os

docs = {
    "README.md": """# JARVIS - Complete Enterprise AI Assistant & Control Centre

JARVIS is a production-ready, self-hosted, modular personal and organizational AI control centre built with FastAPI, React, PostgreSQL, Redis, and Docker Compose.

## Key Features
- **Multi-Modal Interaction**: Text chat, push-to-talk speech-to-text, audio speech synthesis, drag-and-drop file ingestion, and vision screenshot analysis.
- **Streaming Response Architecture**: Server-Sent Events (SSE) stream AI tokens, tool states, and citations in real time.
- **Unified Tool Registry & Security**: Weather, Calculator, System Health, Read-only SQL connector, and manual confirmation prompts for sensitive tools.
- **Document Intelligence (RAG)**: Full extraction for PDF, DOCX, XLSX, CSV, and TXT files paired with cosine vector similarity retrieval.
- **Configurable AI Providers**: Easily switch between OpenAI-compatible APIs, local Ollama LLMs, and zero-dependency offline mock adapters.

## Quickstart
```bash
cp .env.example .env
docker compose up -d --build
```
Open [http://localhost](http://localhost) in your browser.
""",

    "QUICKSTART.md": """# Quickstart Guide

1. Clone the repository and navigate into the folder.
2. Copy environment settings:
   ```bash
   cp .env.example .env
   ```
3. Start the stack:
   ```bash
   docker compose up -d --build
   ```
4. Access the web interface at `http://localhost`. Default credentials auto-initialize your first user as `admin`.
""",

    "ARCHITECTURE.md": """# Architecture Overview

```
Frontend (React + Vite + TS + Tailwind)
   ↓ (SSE / REST)
Nginx Gateway (Port 80)
   ↓
FastAPI Backend Core (Port 8000)
   ├── Auth & RBAC (JWT)
   ├── AI Orchestrator Loop
   ├── Tool Registry (Calculator, SQL, Weather)
   ├── RAG Engine & Document Extractor
   ├── Voice & Vision Subsystems
   └── SQLite / PostgreSQL + Redis
```
""",

    "DEPLOYMENT.md": """# Deployment Guide

## Production Docker Compose Setup
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Monitoring Health
- `/health`: Health status endpoint
- `/readiness`: Readiness check
- `/liveness`: Liveness check
""",

    "SECURITY.md": """# Security & Hardening Policy

1. **Role-Based Access Control (RBAC)**: Admin, User, Read-only.
2. **Safe Tool Execution**: Dangerous tools require confirmation prompts.
3. **Database Safeguards**: SQL tools strictly enforce `SELECT` queries and reject destructive keywords (`DROP`, `DELETE`, `UPDATE`).
4. **Header Protection**: Enforced Content-Security-Policy (CSP), CORS, and X-Frame-Options.
""",

    "CONFIGURATION.md": """# Configuration Reference

All environment settings are loaded from `.env`:
- `APP_NAME`: Assistant identifier (default: `JARVIS`)
- `LLM_PROVIDER`: `local_mock`, `openai`, `ollama`
- `SECRET_KEY`: Minimum 32-character secret string
- `DATABASE_URL`: Async SQLAlchemy connection string
""",

    "API.md": """# API Specification

All endpoints are versioned under `/api/v1/`:
- `POST /auth/register` & `POST /auth/login`
- `GET /conversations` & `POST /conversations`
- `POST /conversations/{id}/messages/stream` (SSE)
- `POST /documents/upload` & `GET /documents`
- `POST /vision/analyse`
- `POST /voice/stt` & `POST /voice/tts`
""",

    "TOOLS.md": """# Tool System Reference

Registered tools:
1. `get_current_time` (SAFE)
2. `calculator` (SAFE)
3. `get_weather` (SAFE)
4. `get_system_health` (ADMIN)
5. `read_only_database_query` (ADMIN, SELECT ONLY)
6. `delete_user_session_files` (CONFIRMATION REQUIRED)
""",

    "RAG.md": """# Document RAG Architecture

Pipeline:
Upload -> Text Extraction (PDF/DOCX/XLSX/CSV) -> Chunking -> Vector Hash Embeddings -> Local Cosine Search -> Citation Prompt Injection.
""",

    "VOICE.md": """# Voice Pipeline

Features:
- Browser Web Speech API push-to-talk recognition
- Bilingual support (Malay & English)
- Speech Synthesis API (TTS) for automatic spoken responses
""",

    "VISION.md": """# Vision Pipeline

Users can upload or paste screenshots to analyze SQL errors, tracebacks, architecture diagrams, and tabular data.
""",

    "TROUBLESHOOTING.md": """# Troubleshooting & FAQ

- **Containers failing to start**: Verify port 80 and 8000 are not occupied by running `lsof -i :80`.
- **Database Connection Error**: Verify `DATABASE_URL` matches your container IP.
""",

    "BACKUP_RESTORE.md": """# Backup & Restoration Procedures

To backup user database and uploads:
```bash
tar -cvzf jarvis_backup.tar.gz ./data/uploads jarvis.db
```
To restore:
```bash
tar -xvzf jarvis_backup.tar.gz
```
""",

    "DEVELOPMENT.md": """# Developer Setup Guide

1. Backend:
   ```bash
   pip install -r backend/requirements.txt
   uvicorn backend.app.main:app --reload
   ```
2. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
"""
}

os.makedirs("docs", exist_ok=True)
for filename, content in docs.items():
    filepath = filename if filename in ["README.md", "QUICKSTART.md"] else os.path.join("docs", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("All 14 documentation deliverables generated successfully!")
