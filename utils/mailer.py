import smtplib
from email.message import EmailMessage

from flask import current_app as app


def send_email(to, subject, body, html=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "no-reply@yourdomain.com"
    msg["To"] = to
    msg.set_content(body)

    if html:
        msg.add_alternative(html, subtype="html")

    mail_server = app.config["MAIL_SERVER"]
    mail_port = app.config["MAIL_PORT"]
    mail_username = app.config["MAIL_USERNAME"]
    mail_password = app.config["MAIL_PASSWORD"]

    with smtplib.SMTP(mail_server, mail_port) as smtp:
        smtp.starttls()
        smtp.login(mail_username, mail_password)
        smtp.send_message(msg)
