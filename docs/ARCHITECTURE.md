# Architecture Overview

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
