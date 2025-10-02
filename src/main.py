"""
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routes
import logging
from dotenv import load_dotenv

# CRITICAL: Load .env BEFORE anything else
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hacker News API with AI",
    description="Scrape Hacker News and classify stories with OpenAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (if needed for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Hacker News API starting up...")
    logger.info("📚 API documentation available at /docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Hacker News API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
