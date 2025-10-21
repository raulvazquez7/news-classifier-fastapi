"""
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routes
from src.config import settings  # ← Import settings (valida al import)
import logging
from dotenv import load_dotenv

# Load .env BEFORE importing settings
load_dotenv()

# Configure logging with level from settings
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
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

app.include_router(routes.router)

@app.on_event("startup")
async def startup_event():
    """
    Startup event - configuration already validated by settings import.
    """
    logger.info("🚀 Hacker News API starting up...")
    logger.info(f"✅ OpenAI Model: {settings.openai_model}")
    logger.info(f"✅ API Key configured: {settings.openai_api_key[:20]}...")
    logger.info("📚 API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Hacker News API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port
    )
