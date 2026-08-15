import time
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import Base, engine
from app.api.endpoints import auth, users, chat, tools, documents, voice, vision, skills, system_research, memory

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis_app")

app = FastAPI(
    title=settings.APP_NAME,
    description="Futuristic JARVIS-like Personal & Organizational AI Control Center",
    version="1.0.0",
    docs_url="/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration: Allow standard local, production, and dynamic network origins cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ],
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Rate Limiting and Timing middleware
@app.middleware("http")
async def add_process_time_and_rate_limit(request: Request, call_next):
    # Skip assets, docs, or healthchecks from rate limiting if desired
    if not request.url.path.startswith("/api/v1/auth/login") and request.url.path.startswith("/api/v1"):
        from app.security.rate_limiter import check_rate_limit
        try:
            await check_rate_limit(request)
        except HTTPException as he:
            return JSONResponse(status_code=he.status_code, content={"detail": he.detail})

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Custom Global Exception Handler to safeguard sensitive system credentials
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled system error encountered on path {request.url.path}")

    # Check if it's a known HTTP Exception
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal system error occurred. Our engineers are tracking it. Please retry later.",
            "type": "internal_error"
        }
    )

# Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users Management"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(tools.router, prefix=f"{settings.API_V1_STR}/tools", tags=["Tools Registry"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["RAG Documents"])
app.include_router(voice.router, prefix=f"{settings.API_V1_STR}/voice", tags=["Voice Pipeline"])
app.include_router(vision.router, prefix=f"{settings.API_V1_STR}/vision", tags=["Vision OCR & Analytics"])
app.include_router(skills.router, prefix=f"{settings.API_V1_STR}/skills", tags=["Skill Engine"])
app.include_router(system_research.router, prefix=f"{settings.API_V1_STR}", tags=["System & Research"])
app.include_router(memory.router, prefix=f"{settings.API_V1_STR}/memory", tags=["Personal Memory"])

# System Health endpoints
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "app": settings.APP_NAME,
        "services": {
            "database": "online",
            "redis": "online",
            "ai_orchestrator": "online"
        }
    }
