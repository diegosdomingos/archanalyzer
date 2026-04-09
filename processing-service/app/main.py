import asyncio
import json
import logging
import aio_pika
from datetime import datetime
from app.core.config import RABBITMQ_URL
from app.core.database import get_session, create_tables
from app.core.ai_analyzer import analyze_diagram
from app.models.job import Job
from app.models.report import Report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = json.loads(message.body.decode())
        job_id = body["job_id"]
        file_path = body["file_path"]

        logger.info(f"Processando job {job_id}")
        db = get_session()

        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} não encontrado no banco.")
                return

            job.status = "processing"
            job.updated_at = datetime.utcnow()
            db.commit()

            result = analyze_diagram(file_path)

            report = Report(
                job_id=job_id,
                components=json.dumps(result["components"]),
                risks=json.dumps(result["risks"]),
                recommendations=json.dumps(result["recommendations"]),
                raw_response=result["raw"]
            )
            db.add(report)

            job.status = "analyzed"
            job.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Job {job_id} analisado com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao processar job {job_id}: {e}")
            if job:
                job.status = "error"
                job.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


async def main():
    create_tables()
    logger.info("Processing Service iniciado. Aguardando mensagens...")

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue("analysis_queue", durable=True)
    await queue.consume(process_message)

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())