import os

QUEUE_NAME = os.environ.get("QUEUE_NAME", "stats-queue")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "./data/serverless.db")
DEFAULT_SENSORS = int(os.environ.get("DEFAULT_SENSORS", "100"))
DEFAULT_SAMPLES = int(os.environ.get("DEFAULT_SAMPLES", "100"))
