"""KiranaFlow AI - FastAPI Application Entry Point"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import create_tables, get_db_session
from .database.seed import seed_database
from .api.agent import router as agent_router
from .api.products import router as products_router
from .api.orders import router as orders_router
from .api.customers import router as customers_router
from .api.dashboard import router as dashboard_router
from .api.delivery import router as delivery_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="KiranaFlow AI",
    description="Autonomous AI Store Operator for Neighborhood Kirana Stores",
    version="1.0.0",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(customers_router)
app.include_router(dashboard_router)
app.include_router(delivery_router)


@app.on_event("startup")
def startup():
    """Initialize database and seed data on startup."""
    logger.info("Starting KiranaFlow AI...")
    create_tables()
    with get_db_session() as db:
        seed_database(db)
    logger.info(f"KiranaFlow AI ready. AI Provider: {settings.ai_provider}")


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "store": settings.store_name,
        "ai_provider": settings.ai_provider,
        "version": "1.0.0",
    }
