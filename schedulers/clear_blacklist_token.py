import logging
from datetime import datetime, timezone

from dotenv import load_dotenv

from utils.db_connection import db

load_dotenv()
logger = logging.getLogger(__name__)


def clear_expired_tokens():
    logger.info("Running scheduled job to clear expired tokens...")

    result = db.token_blacklist.delete_many(
        {"exp": {"$lt": datetime.now(timezone.utc)}}
    )

    logger.info(
        f"[{datetime.now(timezone.utc)}] Deleted {result.deleted_count} expired tokens"
    )


if __name__ == "__main__":
    clear_expired_tokens()
