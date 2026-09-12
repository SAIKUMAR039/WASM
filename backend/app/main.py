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

