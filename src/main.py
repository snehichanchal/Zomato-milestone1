"""
Entry point for the Zomato Restaurant Recommendation System.

Initializes the FastAPI application, loads the dataset into the repository,
configures CORS for the frontend, and mounts the API routes.

Usage:
    uvicorn src.main:app --reload
"""

import logging
import os
import threading
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
# Background data loader
# ---------------------------------------------------------------------------

def _load_data_background(app: FastAPI) -> None:
    """Load the dataset in a background thread so the server can start
    immediately and respond to Railway health checks while data loads."""
    try:
        repo.load()
        logger.info("Successfully loaded %d restaurants.", repo.count())
    except Exception as exc:
        logger.error("Failed to initialize repository: %s", exc)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the data loader in a background thread, then yield immediately
    so the server can begin accepting requests (including health checks)."""
    logger.info("Initializing Zomato Recommendation System…")
    app.state.repo = repo  # attach early (is_loaded will be False until done)

    loader_thread = threading.Thread(
        target=_load_data_background,
        args=(app,),
        daemon=True,
        name="data-loader",
    )
    loader_thread.start()

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
    """Health check endpoint — always returns 200 so Railway considers
    the deployment healthy. The ``repo_loaded`` field indicates whether
    the background data load has finished."""
    return {
        "status": "healthy",
        "repo_loaded": repo.is_loaded,
        "detail": "ready" if repo.is_loaded else "loading data",
    }


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
