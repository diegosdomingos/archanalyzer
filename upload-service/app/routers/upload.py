import os
import uuid
import logging
import aio_pika
import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import RABBITMQ_URL, UPLOADS_DIR
from app.models.job import Job

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "application/pdf"}
MAX_SIZE_MB = 10


@router.post("/upload")
async def upload_diagram(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido. Use PNG, JPG ou PDF.")

    content = await file.read()

    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Arquivo muito grande. Máximo {MAX_SIZE_MB}MB.")

    job_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOADS_DIR, f"{job_id}{ext}")

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    job = Job(id=job_id, filename=file.filename, file_path=file_path, status="received")
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("analysis_queue", durable=True)
            message = aio_pika.Message(
                body=json.dumps({"job_id": job_id, "file_path": file_path}).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await channel.default_exchange.publish(message, routing_key=queue.name)

        job.status = "queued"
        db.commit()
        logger.info(f"Job {job_id} publicado na fila com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao publicar na fila: {e}")
        job.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail="Erro ao enfileirar análise.")

    return {"job_id": job_id, "status": job.status, "filename": file.filename}

@router.get("/status/{job_id}")
def get_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return {
        "job_id": job.id,
        "status": job.status,
        "agent_status": job.agent_status,
        "filename": job.filename,
        "created_at": job.created_at
    }