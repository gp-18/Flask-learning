from authentication.model import User


class UserAdmin(User):
    """
    Extends the base User class with admin-level user management functionality.
    """

    @staticmethod
    def list_all_users(db):
        """
        List all users that are not soft-deleted (is_deleted = False).
        """
        return list(db["users"].find({"is_deleted": False}))

    def create_user_by_admin(self, admin_email):
        """
        Create a user, setting the created_by field to the admin's email.
        """
        self.created_by = admin_email
        self.updated_by = admin_email
        return self.create()
