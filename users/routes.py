# users/routes.py

from flask import Blueprint

from middlewares.admin_required import admin_required
from middlewares.verify_token import token_required
from users.controller import AdminUserController
from utils.db_connection import db

user_bp = Blueprint("user_bp", __name__, url_prefix="/admin")


@user_bp.route("/all-users", methods=["GET"])
@admin_required
def list_users():
    return AdminUserController.list_users(db)


@user_bp.route("/user/<user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    return AdminUserController.get_user(db, user_id)


@user_bp.route("/create-user", methods=["POST"])
@admin_required
def create_user():
    return AdminUserController.create_user(db)


@user_bp.route("/update-user", methods=["POST"])
@token_required
def update_user():
    return AdminUserController.update_user(db)


@user_bp.route("/delete-user", methods=["POST"])
@token_required
def delete_user():
    return AdminUserController.soft_delete_user(db)


@user_bp.route("/restore-user", methods=["POST"])
@admin_required
def restore_user():
    return AdminUserController.restore_user(db)


@user_bp.route("/activate-2fa", methods=["POST"])
@token_required
def activate_2fa():
    return AdminUserController.activate_2fa(db)
