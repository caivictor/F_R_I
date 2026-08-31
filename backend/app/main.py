"""Main FastAPI application entry point for F.R.I."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.routers.chat import router as chat_router
from backend.app.routers.personas import router as personas_router
from backend.app.routers.portfolio import router as portfolio_router

app = FastAPI(
    title="F.R.I. Financial Research & Investment API",
    description="Multi-agent financial research, equity analysis, and portfolio paper trading assistant.",
    version="1.2.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(chat_router)
app.include_router(personas_router)
app.include_router(portfolio_router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": "F.R.I.",
        "version": "1.2.0",
    }


# Static frontend mounting (if pre-built dist directory exists)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists() and FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str) -> FileResponse:
        """Serve frontend static build or fallback to index.html with path traversal protection."""
        try:
            resolved_dist = FRONTEND_DIST.resolve()
            target_path = (resolved_dist / full_path).resolve()
            # Enforce canonical path boundary containment to prevent path traversal
            if str(target_path).startswith(str(resolved_dist)) and target_path.is_file():
                return FileResponse(target_path)
        except Exception:
            pass
        return FileResponse(FRONTEND_DIST / "index.html")
