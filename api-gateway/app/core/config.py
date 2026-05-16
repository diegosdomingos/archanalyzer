import os
import logging
import json
import logging_loki
from datetime import datetime

UPLOAD_SERVICE_URL = os.getenv("UPLOAD_SERVICE_URL", "http://localhost:8001")
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://localhost:8003")
LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "api-gateway",
            "module": record.module,
            "message": record.getMessage()
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)


def setup_logging():
    # Handler console
    console = logging.StreamHandler()
    console.setFormatter(JsonFormatter())

    # Handler Loki
    try:
        loki_handler = logging_loki.LokiHandler(
            url=LOKI_URL,
            tags={"service": "api-gateway"},
            version="1",
        )
        logging.root.handlers = [console, loki_handler]
    except Exception:
        logging.root.handlers = [console]

    logging.root.setLevel(logging.INFO)