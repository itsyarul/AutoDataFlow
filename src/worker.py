# src/worker.py
import os
import sys
import logging

# Ensure project root (/app) is on sys.path so `src` is importable by RQ
HERE = os.path.dirname(os.path.abspath(__file__))       # /app/src
PROJECT_ROOT = os.path.dirname(HERE)                    # /app
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from rq import Worker, Queue
from redis import Redis
from dotenv import load_dotenv

# Load env vars for local execution
load_dotenv()

# Initialize DB table so worker and api use same schema
from src import jobs_db
jobs_db.init_db()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
logger.info("Using REDIS_URL=%s", REDIS_URL)
redis_conn = Redis.from_url(REDIS_URL)

def main():
    try:
        logger.info("Connecting to Redis at %s", REDIS_URL)
        q = Queue("default", connection=redis_conn)
        logger.info("Starting worker listening on queue: %s", q.name)
        if sys.platform == "win32":
            logger.warning("Running on Windows: Using SimpleWorker (no fork). Job timeouts might not work accurately.")
            from rq import SimpleWorker
            worker = SimpleWorker([q], connection=redis_conn)
        else:
            worker = Worker([q], connection=redis_conn)
        
        worker.work()
    except Exception as exc:
        logger.exception("Worker crashed on startup: %s", exc)
        raise

if __name__ == "__main__":
    main()
