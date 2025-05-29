from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from flask import current_app as app
from flask import render_template, request

from authentication.helper import (
    generate_2fa_secret,
    generate_qr_code_url,
    save_user_2fa_secret,
    verify_2fa_token,
)
from utils.mailer import send_email
from utils.response import failure, success
from utils.webhook import send_webhook

from .model import User


class AuthController:
    """
    Controller class to handle user authentication related tasks such as:
    - User registration
    - User login
    - Token generation and validation
    - Change Password
    - Forgot password and reset via email
    """

    @staticmethod
    def register(db):
        """
        Handles user registration, including password validation and user creation.

        Args:
            db (Database): The MongoDB database connection.

        Returns:
            tuple: A JSON response with the status and message, along with HTTP status code.
        """
        data = request.get_json()

        if not data.get("email") or not data.get("password"):
            return failure(message="Missing required fields", status_code=400)

        user = User(db, data)

        user_exists = user.exists()

        if user_exists and user_exists.get("is_deleted", True):
            return failure(
                message="User with this email already exists but is deleted. Please contact admin to restore.",
                status_code=400,
            )

        if user_exists:
            return failure(
                message="User with this email already exists.", status_code=400
            )

        try:
            created_user = user.create()
            created_user.pop("password")

            send_webhook(
                "user.registered",
                {
                    "email": created_user.get("email"),
                    "role": created_user.get("role"),
                    "id": created_user.get("_id"),
                },
            )

            return success(
                message="User registered successfully",
                data=created_user,
                status_code=201,
            )

        except ValueError as e:
            return failure(message=str(e), status_code=400)

    @staticmethod
    def login(db):
        """
        Handles user login, verifies credentials, and returns a JWT token.
        """
        data = request.get_json()

        if not data.get("email") or not data.get("password"):
            return failure(message="Email and password are required", status_code=400)

        user = User.verify(db, data["email"], data["password"])
        if not user:
            return failure("Invalid credentials", status_code=401)

        if user.get("is_deleted", False):
            return failure(
                message="User account is deleted, please contact admin.",
                status_code=403,
            )

        user.pop("password", None)
        user.pop("is_deleted", None)

        if "_id" in user and isinstance(user["_id"], ObjectId):
            user["_id"] = str(user["_id"])

        access_token = AuthController.generate_access_token(user)
        refresh_token = AuthController.generate_refresh_token(user)

        return success(
            message="Login successful",
            data={
                "user": user,
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            status_code=200,
        )

    @staticmethod
    def generate_access_token(user):
        """
        Generates a JWT access token for the authenticated user.
        This token expires in 3 weeks (21 days).

        Args:
            user (dict): The user document from the database.

        Returns:
            str: The generated JWT access token.
        """
        expiration = timedelta(weeks=3)
        payload = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "exp": datetime.utcnow() + expiration,
        }

        access_token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        return access_token

    @staticmethod
    def generate_refresh_token(user):
        """
        Generates a JWT refresh token for the authenticated user.
        This token expires in 3 months.

        Args:
            user (dict): The user document from the database.

        Returns:
            str: The generated JWT refresh token.
        """
        expiration = timedelta(weeks=12)
        payload = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "exp": datetime.utcnow() + expiration,
        }

        refresh_token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        return refresh_token

    @staticmethod
    def refresh_token():
        """
        Refreshes the JWT token when the old one is still valid but about to expire.

        Returns:
            tuple: A JSON response with the new JWT access token.
        """
        data = request.get_json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return failure("Refresh token is required for refreshing", status_code=400)

        try:
            decoded_token = jwt.decode(
                refresh_token, app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            user_id = decoded_token["user_id"]

            user = {"_id": user_id, "role": decoded_token["role"]}

            new_access_token = AuthController.generate_access_token(user)

            return success(
                message="Access token refreshed successfully",
                data={"access_token": new_access_token},
                status_code=200,
            )

        except jwt.ExpiredSignatureError:
            return failure(
                "Refresh token has expired, please log in again.", status_code=401
            )
        except jwt.InvalidTokenError:
            return failure("Invalid refresh token", status_code=401)

    @staticmethod
    def change_password(db):
        """
        Handles password change for the authenticated user.
        Args:
            db (Database): The MongoDB database connection.
        Returns:
            tuple: A JSON response with the status and message, along with HTTP status code.
        """
        data = request.get_json()

        if not data.get("new_password"):
            return failure(message="New password is required", status_code=400)

        user_id = request.user.get("user_id")

        user_record = db.users.find_one({"_id": ObjectId(user_id)})
        if not user_record:
            return failure(message="User not found", status_code=404)

        user = User(
            db, {"email": user_record["email"], "password": data["new_password"]}
        )

        try:
            user.change_password()
            return success(message="Password reset successfully", status_code=200)
        except ValueError as e:
            return failure(message=str(e), status_code=400)

    @staticmethod
    def forgot_password(db):
        """
        Handles forgot password request. Generates a reset token and sends it via email.

        Args:
            db (Database): The MongoDB database connection.

        Returns:
            tuple: A JSON response indicating success or failure.
        """
        data = request.get_json()
        email = data.get("email")

        if not email:
            return failure(message="Email is required", status_code=400)

        user = db.users.find_one({"email": email})
        if not user:
            return failure(message="User not found", status_code=404)

        reset_token = jwt.encode(
            {
                "user_id": str(user["_id"]),
                "exp": datetime.utcnow() + timedelta(minutes=15),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        reset_link = f"{app.config['FRONTEND_URL']}/reset-password?token={reset_token}"

        subject = "Password Reset Request"
        body = f"Click the link below to reset your password:\n\n{reset_link}\n\nThis link expires in 15 minutes."

        try:
            html_body = render_template(
                "reset_password_email.html",
                RESET_LINK=reset_link,
                YEAR=datetime.now().year,
            )
            send_email(to=email, subject=subject, body=body, html=html_body)
            return success(message="Password reset link sent to email", status_code=200)
        except Exception as e:
            return failure(message=f"Failed to send email: {str(e)}", status_code=500)

    @staticmethod
    def logout(db):
        """
        Handles user logout by blacklisting the JWT token.Pass the refresh token to the logout function to invalidate it.
        Args:
            db (Database): The MongoDB database connection.
        Returns:
            tuple: A JSON response indicating success or failure.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return failure(
                message="Authorization header missing or invalid", status_code=401
            )

        token = auth_header.split(" ")[1]

        try:
            decoded = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            exp = datetime.fromtimestamp(decoded.get("exp"), tz=timezone.utc)

            db.token_blacklist.insert_one({"token": token, "exp": exp})

            return success(message="Successfully logged out", status_code=200)

        except Exception:
            return failure(message="Logout failed", status_code=500)

    @staticmethod
    def generate_2fa(db):
        user_id = request.user.get("user_id")
        user_email = request.user.get("email")
        if not user_id:
            return failure(message="User ID is required", status_code=400)

        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return failure(message="User not found", status_code=404)

        secret = generate_2fa_secret()
        save_user_2fa_secret(
            db=db, user_id=user_id, secret=secret, user_email=user_email
        )

        if not secret:
            return failure(message="Failed to generate 2FA secret", status_code=500)

        qr_code_url = generate_qr_code_url(secret, user_email)

        return success(
            message="2FA setup successful",
            data={"manual_code": secret, "qr_code_url": qr_code_url},
            status_code=200,
        )

    @staticmethod
    def verify_2fa(db):
        data = request.get_json()
        user_id = request.user.get("user_id")
        if not user_id:
            return failure(message="User ID is required", status_code=400)

        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return failure(message="User not found", status_code=404)

        secret = user.get("2fa_secret")
        if not secret:
            return failure(message="2FA is not set up for this user", status_code=400)

        token = data.get("otp_token")
        if not token:
            return failure(message="2FA Otp token is required", status_code=400)

        if not verify_2fa_token(secret, token):
            return failure(message="Invalid 2FA token", status_code=401)

        return success(message="2FA verification successful", status_code=200)
