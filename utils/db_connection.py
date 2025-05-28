import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient, errors

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "flask_jwt_auth")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()

    db = client[DB_NAME]

    logger.info("✅ MongoDB connected successfully")

except errors.ServerSelectionTimeoutError as err:
    logger.error("❌ Failed to connect to MongoDB: %s", err)
    db = None
