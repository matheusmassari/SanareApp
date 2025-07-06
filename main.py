from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db
from app.users.routes import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    print("🚀 Starting SanareApp...")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down SanareApp...")
    await close_db()
    print("✅ Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Modern Backend Application with FastAPI, SQLAlchemy and PostgreSQL",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health"
    }


# Include routers
app.include_router(
    users_router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"]
)

# Add more routers here as the application grows
# app.include_router(posts_router, prefix=f"{settings.API_V1_STR}/posts", tags=["posts"])
# app.include_router(llm_router, prefix=f"{settings.API_V1_STR}/llm", tags=["llm"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    ) 