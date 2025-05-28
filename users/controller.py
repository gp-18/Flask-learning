from datetime import datetime, timezone

from bson import ObjectId
from flask import request

from authentication.model import User
from users.model import UserAdmin
from utils.pagination import paginate
from utils.response import failure, success
from utils.serialize_mongo_document import serialize_mongo_document


class AdminUserController:
    """
    Controller class to handle admin user management tasks such as:
    - List all users
    - Create a user
    - Update a user
    - Soft delete a user
    - Restore a deleted user (admin only)
    """

    @staticmethod
    def list_users(db):
        """
        Retrieve a paginated list of all users excluding passwords.
        """
        users = UserAdmin.list_all_users(db)
        for user in users:
            user["_id"] = str(user["_id"])
            user.pop("password", None)

        paginated = paginate(request, users)
        return success(
            message="Users fetched successfully",
            data=paginated["data"],
            meta=paginated["pagination"],
        )

    @staticmethod
    def get_user(db, user_id):
        """
        Get a specific user's details by user ID.
        """
        try:
            user = db["users"].find_one({"_id": ObjectId(user_id), "is_deleted": False})
            if not user:
                return failure(message="User not found", status_code=404)

            user["_id"] = str(user["_id"])
            user.pop("password", None)
            return success(data=user)
        except Exception as e:
            return failure(message=str(e), status_code=500)

    @staticmethod
    def create_user(db):
        """
        Create a new user by an admin.
        Requires email and password.
        """
        try:
            user_data = request.get_json()

            if not user_data.get("email") or not user_data.get("password"):
                return failure(message="Missing required fields", status_code=400)

            created_by_id = request.user.get("user_id")
            if not created_by_id:
                return failure(message="Unauthorized", status_code=401)

            admin_user = db.users.find_one({"_id": ObjectId(created_by_id)})
            if not admin_user:
                return failure(message="Admin user not found", status_code=404)

            created_by_email = admin_user.get("email")
            user_data["created_by"] = created_by_email

            user = UserAdmin(db, user_data)
            created_user = user.create_user_by_admin(created_by_email)
            created_user.pop("password", None)

            return success(
                message="User created successfully", data=created_user, status_code=201
            )

        except Exception as e:
            return failure(message=str(e), status_code=500)

    @staticmethod
    def update_user(db):
        """
        Update a user's profile.
        Admins can update any user; regular users can update themselves.
        """
        try:
            user_data = request.get_json()
            if not user_data:
                return failure(message="No data provided", status_code=400)

            current_user = request.user
            if not current_user:
                return failure(message="Unauthorized", status_code=401)

            current_user_id = current_user.get("user_id")
            current_user_email = current_user.get("email")
            current_user_role = current_user.get("role")

            target_user_id = (
                user_data.get("user_id")
                if current_user_role == "admin"
                else current_user_id
            )
            target_user = db.users.find_one({"_id": ObjectId(target_user_id)})
            if not target_user:
                return failure(message="Target user not found", status_code=404)

            new_email = user_data.get("email")
            if new_email and new_email != target_user.get("email"):
                if db.users.find_one({"email": new_email}):
                    return failure(message="Email already in use", status_code=400)

            user_data.pop("user_id", None)
            user_instance = User(db, target_user)
            updated_user = user_instance.update(
                user_data, updated_by=current_user_email
            )
            if not updated_user:
                return failure(message="Failed to update user", status_code=500)
            updated_user["_id"] = str(updated_user["_id"])
            updated_user.pop("password", None)

            return success(
                message="User updated successfully", data=updated_user, status_code=200
            )

        except Exception as e:
            return failure(message=str(e), status_code=500)

    @staticmethod
    def soft_delete_user(db):
        """
        Soft delete a user.
        Admins can delete any user; regular users can delete themselves.
        """
        try:
            user_data = request.get_json()
            if not user_data:
                return failure(message="No data provided", status_code=400)

            current_user = request.user
            if not current_user:
                return failure(message="Unauthorized", status_code=401)

            current_user_id = current_user.get("user_id")
            current_user_email = current_user.get("email")
            current_user_role = current_user.get("role")

            target_user_id = (
                user_data.get("user_id")
                if current_user_role == "admin"
                else current_user_id
            )
            target_user = db.users.find_one({"_id": ObjectId(target_user_id)})
            if not target_user:
                return failure(message="Target user not found", status_code=404)

            user_data.pop("user_id", None)
            user_instance = User(db, target_user)
            updated_user = user_instance.soft_delete(deleted_by=current_user_email)
            if not updated_user:
                return failure(message="Failed to delete user", status_code=500)
            updated_user["_id"] = str(updated_user["_id"])
            updated_user.pop("password", None)

            return success(
                message="User Deleted successfully", data=updated_user, status_code=200
            )

        except Exception as e:
            return failure(message=str(e), status_code=500)

    @staticmethod
    def restore_user(db):
        """
        Restore a previously soft-deleted user account.

        Requirements:
        - Only users with 'admin' role can perform the restoration.
        - The request must include the email of the user to be restored.
        - The target user must exist and be marked as 'is_deleted'.

        Returns:
        - 200 if successfully restored.
        - 403 if requester is not admin.
        - 404 if user not found.
        - 400 if user is not deleted or if email is missing.
        """
        try:
            user_data = request.get_json()
            if not user_data or not user_data.get("email"):
                return failure(message="Email is required", status_code=400)

            email = user_data["email"]

            if request.user.get("role") != "admin":
                return failure(
                    message="Only admins can restore user accounts", status_code=403
                )

            user = db.users.find_one({"email": email})
            if not user:
                return failure(message="User not found", status_code=404)

            if not user.get("is_deleted"):
                return failure(
                    message="User account is already active", status_code=400
                )

            db.users.update_one({"email": email}, {"$set": {"is_deleted": False}})

            return success(message="Account restored successfully", status_code=200)

        except Exception as e:
            return failure(
                message="Something went wrong", errors=str(e), status_code=500
            )

    @staticmethod
    def activate_2fa(db):
        """
        Activate or deactivate 2FA for a user.
        - Admins can modify 2FA for any user.
        - Regular users can only modify their own 2FA.
        """
        try:
            user_data = request.get_json()
            if not user_data:
                return failure(message="No data provided", status_code=400)

            current_user = request.user
            if not current_user:
                return failure(message="Unauthorized", status_code=401)

            is_2fa = user_data.get("is_2FA")
            if is_2fa is None:
                return failure(message="Missing 'is_2FA' in request", status_code=400)

            current_user_id = current_user.get("user_id")
            current_user_role = current_user.get("role")
            current_user_email = current_user.get("email")

            if current_user_role == "admin":
                target_user_id = user_data.get("user_id")
                if not target_user_id:
                    return failure(
                        message="Admin must provide user_id", status_code=400
                    )
            else:
                target_user_id = current_user_id

            if not ObjectId.is_valid(target_user_id):
                return failure(message="Invalid user ID", status_code=400)

            target_user = db.users.find_one({"_id": ObjectId(target_user_id)})
            if not target_user:
                return failure(message="Target user not found", status_code=404)

            if current_user_role != "admin" and str(target_user["_id"]) != str(
                current_user_id
            ):
                return failure(
                    message="Forbidden: Cannot modify other user's 2FA", status_code=403
                )

            update_data = {
                "is_2FA": True,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": current_user_email,
            }

            db.users.update_one(
                {"_id": ObjectId(target_user_id)}, {"$set": update_data}
            )
            updated_user = db.users.find_one({"_id": ObjectId(target_user_id)})

            if not updated_user:
                return failure(message="Failed to update user", status_code=500)

            return success(
                message="2FA updated successfully",
                data=serialize_mongo_document(updated_user),
                status_code=200,
            )

        except Exception as e:
            return failure(message=str(e), status_code=500)
