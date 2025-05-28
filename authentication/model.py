import re
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash


class User:
    """
    A User model to handle user creation, password validation, and authentication.

    Attributes:
        db (Database): The MongoDB database connection.
        username (str): The user's username.
        email (str): The user's email address.
        password (str): The user's plain-text password.
        role (str): The role of the user (default is 'user').
    """

    def __init__(self, db, data):
        """
        Initializes a User instance with data from the input dictionary.

        Args:
            db (Database): The MongoDB connection object.
            data (dict): Dictionary containing user fields like username, email, password, and role.
        """

        self.db = db
        self.username = data.get("username")
        self.email = data.get("email")
        self.password = data.get("password")
        self.role = data.get("role", "user")
        self.is_deleted = data.get("is_deleted", False)
        self.is_active = data.get("is_active", True)
        self.is_2FA = data.get("is_2FA", False)
        self.created_by = data.get("created_by", self.email)
        self.created_at = data.get("created_at", datetime.now(timezone.utc))
        self.updated_by = data.get("updated_by")
        self.updated_at = data.get("updated_at", datetime.now(timezone.utc))
        self.deleted_by = data.get("deleted_by")
        self.deleted_at = data.get("deleted_at")

    def exists(self):
        """
        Checks if a user with the given email already exists in the database.

        Returns:
            dict or None: User document if found, otherwise None.
        """
        return self.db.users.find_one({"email": self.email})

    def is_valid_password(self):
        """
        Validates the password to ensure it meets the following criteria:
        - At least 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one special character

        Returns:
            bool: True if password is valid, False otherwise.
        """
        if len(self.password) < 8:
            return False
        if not re.search(r"[A-Z]", self.password):
            return False
        if not re.search(r"[a-z]", self.password):
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", self.password):
            return False
        return True

    def create(self):
        """
        Creates a new user in the database after validating the password.

        Returns:
            dict: The created user data (excluding MongoDB document ID).

        Raises:
            ValueError: If the password does not meet validation requirements.
        """
        if not self.is_valid_password():
            raise ValueError(
                "Password must be at least 8 characters long, "
                "contain an uppercase letter, a lowercase letter, and a special character."
            )

        hashed_pw = generate_password_hash(self.password)
        user_data = {
            "username": self.username,
            "email": self.email,
            "password": hashed_pw,
            "role": self.role,
            "is_deleted": self.is_deleted,
            "is_active": self.is_active,
            "is_2FA": self.is_2FA,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at,
            "deleted_by": self.deleted_by,
            "deleted_at": self.deleted_at,
        }
        result = self.db.users.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        return user_data

    @staticmethod
    def verify(db, email, password):
        """
        Verifies the provided credentials against stored user data.

        Args:
            db (Database): The MongoDB database connection.
            email (str): The user's email.
            password (str): The user's plain-text password.

        Returns:
            dict or None: User document if credentials are correct, otherwise None.
        """
        user = db.users.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            return user
        return None

    def change_password(self):
        if not self.is_valid_password():
            raise ValueError("Password must meet complexity requirements")

        hashed_pw = generate_password_hash(self.password)
        result = self.db.users.update_one(
            {"email": self.email}, {"$set": {"password": hashed_pw}}
        )
        return result.modified_count

    def update(self, update_data, updated_by):
        """
        Updates the user data in the database.

        Args:
            update_data (dict): Dictionary containing fields to update.
            updated_by (str): The email of the user who is updating the record.

        Returns:
            dict: The updated user data.
        """
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = updated_by
        self.db.users.update_one({"email": self.email}, {"$set": update_data})
        return self.db.users.find_one({"email": self.email})

    def soft_delete(self, deleted_by):
        """
        Soft deletes the user by setting is_deleted to True and recording the deletion details.

        Args:
            deleted_by (str): The email of the user who is deleting the record.

        Returns:
            dict: The updated user data after soft deletion.
        """
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by
        self.is_deleted = True
        ALLOWED_UPDATE_FIELDS = [
            "username",
            "email",
            "role",
            "is_2FA",
            "is_deleted",
            "is_active",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
            "deleted_by",
            "deleted_at",
        ]

        update_data = {key: getattr(self, key, None) for key in ALLOWED_UPDATE_FIELDS}
        self.db.users.update_one({"email": self.email}, {"$set": update_data})
        return self.db.users.find_one({"email": self.email})
