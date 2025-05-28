import base64
import datetime
from io import BytesIO

import pyotp
import qrcode
from bson import ObjectId


def generate_2fa_secret():
    return pyotp.random_base32()


def save_user_2fa_secret(db, user_id, secret, user_email):
    """
    Stores the 2FA secret in the database for the user.

    Args:
        db (Database): MongoDB database object.
        user_id (str or ObjectId): ID of the user.
        secret (str): The 2FA secret key to be stored.
    """
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "2fa_secret": secret,
                "is_2FA": True,
                "updated_at": datetime.datetime.utcnow(),
                "updated_by": user_email,
            }
        },
    )


def generate_qr_code_url(secret, username, issuer="YourAppName"):
    """
    Generates a base64-encoded QR code image URI for use with an authenticator app.

    Args:
        secret (str): The TOTP secret.
        username (str): The user's name/email to show in the app.
        issuer (str): The issuer name (your app).

    Returns:
        str: Data URI of the QR code.
    """
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)
    qr = qrcode.make(uri)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{base64_img}"


def verify_2fa_token(secret, code):
    """
    Verifies the provided 2FA code against the stored secret.

    Args:
        secret (str): The TOTP secret.
        code (str): The 2FA code to verify.

    Returns:
        bool: True if the code is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
