from .auth import router as auth_router
from .events import router as events_router
from .websocket import router as websocket_router
from .admin import router as admin_router
from .emergency import router as emergency_router
from .special_features import router as special_features_router
from .advanced_features import router as advanced_features_router
from .analytics import router as analytics_router

api_router = None


def get_api_router():
    """Get the main API router with all sub-routers included."""
    global api_router
    
    if api_router is None:
        from fastapi import APIRouter
        
        api_router = APIRouter(prefix="/api/v1")
        
        # Include all routers
        api_router.include_router(auth_router)
        api_router.include_router(events_router)
        api_router.include_router(websocket_router)
        api_router.include_router(admin_router)
        api_router.include_router(emergency_router)
        api_router.include_router(special_features_router, prefix="/features", tags=["Special Features"])
        api_router.include_router(advanced_features_router, prefix="/advanced", tags=["Advanced Features"])
        api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
    
    return api_router
