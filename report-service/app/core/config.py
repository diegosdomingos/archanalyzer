import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://archanalyzer:archanalyzer@localhost:5432/archanalyzer")