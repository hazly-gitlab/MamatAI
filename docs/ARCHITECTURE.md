# System Architecture

## Overview
This system is designed around a decoupled, asynchronous, API-first architecture ensuring maximum performance, modularity, and scalability.

```
+------------+       HTTP       +-------------+
|  Frontend  | -------------->  |   FastAPI   |
| (React/TS) | <--------------  |   Backend   |
+------------+    SSE Stream    +-------------+
                                       |
                   +-------+-----------+-----------+
                   |       |                       |
                   v       v                       v
               +-------+ +----------+      +---------------+
               | Redis | | Postgres |      |  AI adapters  |
               +-------+ +----------+      +---------------+
```

## Service Components

### 1. Ingress Router (Nginx)
The reverse proxy listens on host port `80` and routes matching paths:
- `/api/` traffic to the asynchronous Uvicorn-backend server on port `8000`.
- Root `/` requests to the multi-staged static Nginx React server.
- Supports WebSocket upgrades and SSE connections out of the box with zero-buffering headers.

### 2. Back-end API (FastAPI)
FastAPI runs on modern Python 3.12-slim under Uvicorn.
- **Deps/Middlewares**: Extracts JWT tokens, verifies user permissions, validates request size limits, and enforces sliding rate-limits using Redis or memory fallbacks.
- **Global Handlers**: Catches untracked Python exceptions and hides internal system trace-backs to prevent credential leakage.

### 3. Databases & Search (PostgreSQL & pgvector)
A persistent PostgreSQL volume hosts system tables.
- **Relational models**: Stores Users, Conversations, Messages, Tool Settings, Memories, Documents, and Audit Logs.
- **Semantic index**: Documents are chunked into overlapping blocks, embedded into normalized floating-point vectors, and queried using distance calculations.
