import logging
from fastapi import FastAPI
from app.routers.gateway import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ArchAnalyzer API Gateway",
    description="Gateway de entrada para o sistema de análise de arquiteturas",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}