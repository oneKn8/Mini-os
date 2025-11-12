"""
FastAPI server for Personal Ops Center.
Based on patterns from GenerativeAIExamples/RAG/src/chain_server/server.py
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import actions, inbox, planner, sync

# Configure logging
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup/shutdown)."""
    # Startup
    logger.info("Starting Personal Ops Center API")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # TODO: Initialize database connection pool
    # TODO: Initialize orchestrator client
    # TODO: Load configuration

    yield

    # Shutdown
    logger.info("Shutting down Personal Ops Center API")
    # TODO: Close database connections
    # TODO: Clean up resources


# Create FastAPI application
app = FastAPI(
    title="Personal Ops Center API",
    description="Multi-agent AI assistant for email, calendar, and task management",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # API docs
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": "ops-center-api", "version": "0.1.0"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {"service": "Personal Ops Center API", "version": "0.1.0", "docs": "/docs", "health": "/health"}


# Include API routers
app.include_router(inbox.router, prefix="/api")
app.include_router(planner.router, prefix="/api")
app.include_router(actions.router, prefix="/api")
app.include_router(sync.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.api.server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
