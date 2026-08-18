import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from app.core.database import engine, Base

from app.api.auth_router import router as auth_router
from app.api.conversation_router import router as conversation_router
from app.api.document_router import router as document_router
from app.api.admin_router import router as admin_router
from app.api.voice_vision_router import router as voice_vision_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("jarvis")

app = FastAPI(
    title=settings.APP_NAME,
    description="JARVIS - Complete Production-Ready AI Control Centre",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/v1/openapi.json"
)

# Initialize database schema tables on startup
@app.on_event("startup")
async def startup_db():
    logger.info("Initializing database schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas initialized successfully.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled error for path '{request.url.path}': {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "JARVIS is currently processing a backend subsystem disruption. Please try again.",
                "detail": str(exc) if settings.ENVIRONMENT == "development" else None
            }
        }
    )

app.include_router(auth_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(voice_vision_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": "1.0.0"}

@app.get("/readiness")
def readiness_check():
    return {"status": "ready"}

@app.get("/liveness")
def liveness_check():
    return {"status": "live"}
