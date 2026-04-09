import os

UPLOAD_SERVICE_URL = os.getenv("UPLOAD_SERVICE_URL", "http://localhost:8001")
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://localhost:8003")