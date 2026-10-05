from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.routes.dataset_routes import router as dataset_router
from backend.app.routes.analysis_routes import router as analysis_router

app = FastAPI(
    title="Google Photos AI-Powered Discovery Engine API",
    description="Backend API for Part 1 AI-Powered Discovery Engine — Problem discovery for vague memory photo retrieval.",
    version="1.0.0"
)

# CORS configuration to allow local frontend and remote deployment origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(dataset_router)
app.include_router(analysis_router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "Google Photos AI-Powered Discovery Engine",
        "version": "1.0.0",
        "model": settings.LLM_MODEL
    }

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "data_dir": settings.DATA_DIR,
        "output_dir": settings.OUTPUT_DIR
    }
