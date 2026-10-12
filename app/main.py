from fastapi import FastAPI
from app.api.routes.ingestion import router as ingestion_router
from app.core.exception_handlers import register_exception_handlers
from app.api.routes.ask import router as ask_router
from app.core.logging_config import configure_logging

configure_logging()
app = FastAPI(
    title = "pulseAI website RAG API",
    description = (
        "API for ingesting websites and answering questions "
        "using their content."
    ),
    version = "0.1.0",
)

register_exception_handlers(app)
app.include_router(ingestion_router)
app.include_router(ask_router)