# JARVIS - Complete Enterprise AI Assistant & Control Centre

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
