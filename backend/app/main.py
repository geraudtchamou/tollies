from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import get_settings
from .db.session import engine, Base
from .api import get_api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("Starting up Community Events Verification App...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    yield
    
    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="A community-driven event verification platform with real-time capabilities",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    api_router = get_api_router()
    app.include_router(api_router)
    
    # Health check endpoint
    @app.get("/health")
    def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": "2.0.0"
        }
    
    # Root endpoint
    @app.get("/")
    def root():
        return {
            "message": "Welcome to Community Events Verification API",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
