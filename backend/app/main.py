"""
NFL Momentum Analyzer - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import games_router, momentum_router, share_router, stats_router

settings = get_settings()

app = FastAPI(
    title="NFL Momentum Analyzer",
    description="Analyze NFL game momentum through play-by-play data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games_router)
app.include_router(momentum_router)
app.include_router(share_router)
app.include_router(stats_router)


@app.on_event("startup")
async def startup():
    """Initialize database tables on startup."""
    init_db()


@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": "NFL Momentum Analyzer",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Health check for deployment."""
    return {"status": "healthy"}
