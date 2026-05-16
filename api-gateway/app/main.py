from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.gateway import router
from app.core.config import setup_logging
from prometheus_fastapi_instrumentator import Instrumentator

setup_logging()

import logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ArchAnalyzer API Gateway",
    description="Gateway de entrada para o sistema de análise de arquiteturas",
    version="1.0.0"
)

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    logger.info("Health check realizado")
    return {"status": "ok", "service": "api-gateway"}