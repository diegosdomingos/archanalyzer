import os
import logging
import json
import logging_loki
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://archanalyzer:archanalyzer@localhost:5432/archanalyzer")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/app/uploads")
LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "upload-service",
            "module": record.module,
            "message": record.getMessage()
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)


def setup_logging():
    console = logging.StreamHandler()
    console.setFormatter(JsonFormatter())

    try:
        loki_handler = logging_loki.LokiHandler(
            url=LOKI_URL,
            tags={"service": "upload-service"},
            version="1",
        )
        logging.root.handlers = [console, loki_handler]
    except Exception:
        logging.root.handlers = [console]

    logging.root.setLevel(logging.INFO)