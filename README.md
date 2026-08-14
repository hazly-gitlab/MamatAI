# JARVIS - Complete personal & organizational AI assistant

JARVIS is a complete, production-grade, highly-secure personal and organizational AI control center assistant. Inspired by futuristic sci-fi control centers, JARVIS is built using Python, FastAPI, React, TypeScript, Tailwind CSS, PostgreSQL, pgvector, and Redis, all fully coordinated under Docker Compose.

The assistant supports fluid text chatting, microphone/voice audio input transcribing (STT), natural synthesized audio speech responses (TTS), visual OCR analysis of screenshots, diagram parsing, document chunking & semantic RAG ingestion, interactive permission-based safe tool orchestration, sliding-window rate limiting, and structured auditing logs.

---

## Architecture Summary
```
                                +-------------------+
                                |    Web Browser    |
                                | (React / TS UI)   |
                                +---------+---------+
                                          | HTTP / WebSockets
                                          v
                                +---------+---------+
                                | Nginx Reverse Proxy|
                                +---------+---------+
                                          |
                        +-----------------+-----------------+
                        | /                                 | /api/v1
                        v                                   v
             +----------+----------+             +----------+----------+
             |  React Frontend     |             |   FastAPI Backend   |
             |  Static Nginx Server|             |   Python 3.12 Slim  |
             +---------------------+             +----+------+----+----+
                                                      |      |    |
             +----------------------------------------+      |    +-----------------------------+
             |                                               |                                  |
             v                                               v                                  v
+------------+------------+                     +------------+------------+        +------------+------------+
|  PostgreSQL (pgvector)  |                     |       Redis Cache       |        |   Local Speech / Vision |
| Relational Storage      |                     | Sliding-window limits   |        |  (gTTS, OCR Adapters)   |
+-------------------------+                     +-------------------------+        +-------------------------+
```

### Technology Stack
- **Frontend**: React (v18), TypeScript, Vite, Tailwind CSS, Lucide icons. Serves compiled bundles via Nginx Alpine.
- **Backend**: FastAPI (Async ASGI), SQLAlchemy (v2) models, Alembic/Direct schemas, Pydantic (v2) data validation, python-jose, bcrypt.
- **Databases**: PostgreSQL (pgvector extension enabled for semantic chunks), Redis (memory sliding limits, task caching).
- **Core AI**: Generic adapter interface supporting OpenAI cloud models, Ollama, or high-fidelity mock engines.
- **Audio Pipeline**: Google Text-to-Speech (gTTS) offline engine fallback.
- **Reverse Proxy**: Nginx Ingress routing.

---

## Quickstart Deployment (Docker Compose)

### 1. Configure Credentials
Copy `.env.example` to `.env` and set your credentials:
```bash
cp .env.example .env
```

### 2. Launch Stack
Run the standard Docker Compose command to build and launch the application:
```bash
docker compose up -d --build
```

The services will initialize, create all PostgreSQL tables, and seed the default administrator user.

### 3. Access Portal
Open your browser and navigate to:
- **Web UI Control Center**: `http://localhost`
- **Interactive OpenAPI Documentation**: `http://localhost/docs`

### 4. Default Credentials
Log in with the seeded administrator credentials:
- **Email**: `admin@jarvis.ai`
- **Passcode**: `admin123`

---

## Known Limitations & Recommendations

1. **Vite Environment Variables**: In a standard Vite build, `VITE_API_URL` is baked into static assets at build-time. For dynamic deployment, configure the `VITE_API_URL` in `.env` before running the compose command, or utilize Nginx relative routing (`/api`).
2. **GPU Profiling**: The local gTTS synthesizer and numpy-based semantic similarity search are highly optimized for CPU-only execution. If deploying live Whisper or local Ollama LLMs, enable the NVIDIA container toolkit and map the GPU profiles in `docker-compose.yml`.

---

## Recommended Next Steps
- **SSL Termination**: Configure Traefik or Certbot on the Ingress reverse proxy for production-ready secure cookie management.
- **Enterprise SQL**: Add Microsoft SQL Server / MySQL connection variables to query company DB analytics safely in natural language.
