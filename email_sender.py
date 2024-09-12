import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from typing import List, Optional

def send_email(
    subject: str,
    body: str,
    sender_email: str,
    receiver_email: str,
    password: str,
    cc_emails: Optional[List[str]] = None
) -> None:
    """
    Send an email using Gmail SMTP.

    :param subject: Email subject
    :param body: Email body content
    :param sender_email: Sender's email address
    :param receiver_email: Primary recipient's email address
    :param password: Sender's email password or app password
    :param cc_emails: List of CC recipients (optional)
    """
    logger = logging.getLogger(__name__)

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    if cc_emails:
        message["Cc"] = ", ".join(cc_emails)

    message.attach(MIMEText(body, "plain"))

    all_recipients = [receiver_email] + (cc_emails or [])

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, all_recipients, message.as_string())
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"An error occurred while sending the email: {e}")