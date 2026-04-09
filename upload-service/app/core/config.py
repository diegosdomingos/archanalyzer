import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://archanalyzer:archanalyzer@localhost:5432/archanalyzer")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/app/uploads")