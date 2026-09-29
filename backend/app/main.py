from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection, get_db
from app.routers import plugins, execution, metrics, settings as settings_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Startup and Shutdown events for MongoDB
@app.on_event("startup")
def startup_db_client():
    connect_to_mongo()

@app.on_event("shutdown")
def shutdown_db_client():
    close_mongo_connection()

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(plugins.router, prefix=settings.API_V1_STR)
app.include_router(execution.router, prefix=settings.API_V1_STR)
app.include_router(metrics.router, prefix=settings.API_V1_STR)
app.include_router(settings_router.router, prefix=settings.API_V1_STR)

# Root WebSocket streaming endpoint for real-time stdout
@app.websocket("/ws/execute")
async def root_websocket_execute(websocket: WebSocket):
    from app.routers.execution import handle_websocket_execution
    db = get_db()
    await handle_websocket_execution(websocket, db)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "database": "MongoDB",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {"status": "healthy", "sandbox": "wasmtime", "database": "mongodb"}

@app.get("/health/live")
def liveness_probe():
    """Kubernetes liveness probe: verifies the WasmBox process is healthy and active."""
    return {
        "status": "ALIVE",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/ready")
def readiness_probe():
    """Kubernetes readiness probe: verifies database availability and engine execution slots."""
    from app.routers.execution import get_concurrency_stats
    stats = get_concurrency_stats()
    db = get_db()
    db_connected = db is not None
    is_ready = stats["available_slots"] > 0
    return {
        "status": "READY" if is_ready else "BUSY",
        "ready": is_ready,
        "database_connected": db_connected,
        "concurrency": stats,
        "version": settings.VERSION
    }

@app.get("/health/startup")
def startup_probe():
    """Kubernetes startup probe: verifies services and compiler cache initialized."""
    return {
        "status": "STARTED",
        "service": settings.PROJECT_NAME,
        "compiler_cache": settings.ENABLE_COMPILER_CACHE,
        "version": settings.VERSION
    }

@app.get("/metrics")
def root_prometheus_metrics():
    """Direct root Prometheus exposition metric scraping endpoint."""
    from app.routers.metrics import prometheus_metrics
    db = get_db()
    return prometheus_metrics(tenant_id="tenant_default", db=db)



