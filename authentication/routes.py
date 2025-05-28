from flask import Blueprint

from authentication.controller import AuthController
from middlewares.verify_token import token_required
from utils.db_connection import db

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    return AuthController.register(db)


@auth_bp.route("/login", methods=["POST"])
def login():
    return AuthController.login(db)


@auth_bp.route("/refresh-token", methods=["POST"])
def refresh_token():
    return AuthController.refresh_token()


@auth_bp.route("/change-password", methods=["POST"])
@token_required
def change_password():
    return AuthController.change_password(db)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    return AuthController.forgot_password(db)


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    return AuthController.logout(db)


@auth_bp.route("/generate-2fa", methods=["POST"])
@token_required
def setup_2fa():
    return AuthController.generate_2fa(db)


@auth_bp.route("/verify-2fa", methods=["POST"])
@token_required
def verify_2fa():
    return AuthController.verify_2fa(db)
