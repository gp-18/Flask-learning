import logging
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from utils.db_connection import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin():
    """
    Creates an admin user in the MongoDB database if one does not already exist.

    This function checks the 'users' collection in MongoDB to see if a user with
    the role 'admin' already exists. If not, it creates a new admin user with
    default credentials and inserts it into the database.

    The default admin user has the username 'admin', email 'admin@example.com',
    and password 'admin123' (hashed).
    """
    if db.users.find_one({"role": "admin"}):
        logger.info("Admin user already exists.")
        return

    admin_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "is_deleted": False,
        "is_active": True,
        "is_2FA": False,
        "created_at": datetime.now(timezone.utc),
        "created_by": "admin@example.com",
        "updated_at": datetime.now(timezone.utc),
        "updated_by": None,
        "deleted_at": None,
        "deleted_by": None,
    }

    db.users.insert_one(admin_data)
    logger.info("Admin user created successfully.")


if __name__ == "__main__":
    create_admin()
