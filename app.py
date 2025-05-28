import atexit
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from authentication.routes import auth_bp
from schedulers.clear_blacklist_token import clear_expired_tokens
from users.routes import user_bp
from utils.db_connection import db
from utils.response import failure, success

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["DB"] = db
app.config["FRONTEND_URL"] = os.getenv("FRONTEND_URL", "http://127.0.0.1:5000")
app.config["MAIL_SERVER"] = os.getenv("MAILTRAP_SERVER", "sandbox.smtp.mailtrap.io")
app.config["MAIL_PORT"] = int(os.getenv("MAILTRAP_PORT", 2525))
app.config["MAIL_USERNAME"] = os.getenv("MAILTRAP_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAILTRAP_PASSWORD")
app.config["MAIL_USE_TLS"] = os.getenv("MAILTRAP_USE_TLS", "True") == "True"
app.config["MAIL_USE_SSL"] = os.getenv("MAILTRAP_USE_SSL", "False") == "True"

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)


@app.route("/")
def home():
    if db is not None:
        return success(message="Server is running and connected to MongoDB")
    else:
        return failure(message="Server is running, but failed to connect to MongoDB")


scheduler = BackgroundScheduler(timezone="UTC")


scheduler.add_job(
    func=clear_expired_tokens,
    trigger=CronTrigger(hour=1, minute=0),
    id="clear_expired_tokens",
    replace_existing=True,
)


scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
