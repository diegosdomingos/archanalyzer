import asyncio
import json
import logging
import aio_pika
from datetime import datetime
from app.core.config import RABBITMQ_URL, setup_logging
from app.core.database import get_session, create_tables
from app.core.orchestrator import run_pipeline
from app.core.rag import build_vectorstore
from app.models.job import Job
from app.models.report import Report

setup_logging()
logger = logging.getLogger(__name__)

# Constrói o vectorstore uma única vez na inicialização
vectorstore = None


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = json.loads(message.body.decode())
        job_id = body["job_id"]
        file_path = body["file_path"]
        job = None

        logger.info(json.dumps({"event": "job_started", "job_id": job_id}))
        db = get_session()

        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(json.dumps({"event": "job_not_found", "job_id": job_id}))
                return

            job.status = "processing"
            job.agent_status = "Iniciando pipeline de agentes..."
            job.updated_at = datetime.utcnow()
            db.commit()

            def update_agent_status(msg):
                job.agent_status = msg
                job.updated_at = datetime.utcnow()
                db.commit()

            result = run_pipeline(file_path, vectorstore=vectorstore, update_status=update_agent_status)

            report = Report(
                job_id=job_id,
                components=json.dumps(result["components"]),
                risks=json.dumps(result["risks"]),
                recommendations=json.dumps(result["recommendations"]),
                raw_response=result["raw"]
            )
            db.add(report)

            job.status = "analyzed"
            job.agent_status = "Pipeline concluído com sucesso."
            job.updated_at = datetime.utcnow()
            db.commit()
            logger.info(json.dumps({"event": "job_completed", "job_id": job_id}))

        except Exception as e:
            logger.error(json.dumps({"event": "job_error", "job_id": job_id, "error": str(e)}))
            if job:
                job.status = "error"
                job.agent_status = f"Erro: {str(e)}"
                job.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


async def main():
    global vectorstore
    create_tables()

    logger.info("Processing Service iniciado. Construindo base RAG...")
    vectorstore = build_vectorstore()
    logger.info("Base RAG construída com sucesso.")

    logger.info("Aguardando mensagens...")
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