"""
Entry point for the Zomato Restaurant Recommendation System.

Initializes the FastAPI application, loads the dataset into the repository,
configures CORS for the frontend, and mounts the API routes.

Usage:
    uvicorn src.main:app --reload
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router
from src.data.repository import RestaurantRepository

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-30s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global repository instance
# ---------------------------------------------------------------------------

repo = RestaurantRepository()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the dataset on startup, clean up on shutdown."""
    logger.info("Initializing Zomato Recommendation System…")

    try:
        repo.load()
        app.state.repo = repo
        logger.info("Successfully loaded %d restaurants.", repo.count())
    except Exception as exc:
        logger.error("Failed to initialize repository: %s", exc)
        # Let the app start so endpoints can return 503 rather than crash
        app.state.repo = repo  # still attach (is_loaded will be False)

    yield

    logger.info("Shutting down Zomato Recommendation System…")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Zomato Recommendation API",
    description="AI-Powered Restaurant Recommendation System",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach the repo early so test clients that skip lifespan can still
# access app.state.repo (even if is_loaded is False).
app.state.repo = repo

# ---------------------------------------------------------------------------
# CORS — configurable via CORS_ORIGINS env var (comma-separated)
# ---------------------------------------------------------------------------

_default_origins = [
    "http://localhost:3000",   # Next.js default
    "http://localhost:5173",   # Vite default
]

_env_origins = os.getenv("CORS_ORIGINS", "")
allowed_origins = (
    [o.strip() for o in _env_origins.split(",") if o.strip()]
    if _env_origins
    else _default_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "repo_loaded": repo.is_loaded}


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
