import logging
from fastapi import FastAPI
from app.core.database import create_tables
from app.routers.upload import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Upload Service",
    description="Serviço responsável pelo upload e orquestração dos jobs",
    version="1.0.0"
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    create_tables()
    logger.info("Upload Service iniciado.")


@app.get("/health")
def health():
    return {"status": "ok", "service": "upload-service"}