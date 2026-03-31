# ANALYTICS
# MULTI_AGENT
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.env_routes import router as env_router
from routes.task_routes import router as task_router
from routes.grader_routes import router as grader_router
from routes.baseline_routes import router as baseline_router
from routes.panel_routes import router as panel_router
from routes.analytics_routes import router as analytics_router
from routes.cost_routes import router as cost_router
from routes.multimodal_routes import router as multimodal_router
from routes.sdk_routes import router as sdk_router

app = FastAPI(
    title="VerifAI",
    description=(
        "OpenEnv-compatible reinforcement-learning environment for evaluating "
        "and improving AI-generated writing quality."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — required for HF Spaces embedding and external agent access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(env_router, tags=["Environment"])
app.include_router(task_router, prefix="/tasks", tags=["Tasks"])
app.include_router(grader_router, prefix="/grader", tags=["Grader"])
app.include_router(baseline_router, prefix="/baseline", tags=["Baseline"])
app.include_router(panel_router, tags=["Panel"])
app.include_router(analytics_router, tags=["Analytics"])
app.include_router(cost_router, tags=["Cost"])
app.include_router(multimodal_router, tags=["Multimodal"])
app.include_router(sdk_router, tags=["SDK"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Liveness probe for Docker/HF Spaces."""
    return {"status": "ok", "service": "verifai"}


@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint — quick API summary."""
    return {
        "service": "VerifAI",
        "version": "1.0.0",
        "docs": "/docs",
        "tasks": ["classify", "rewrite", "iterative"],
    }
