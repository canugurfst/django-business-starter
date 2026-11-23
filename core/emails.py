import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def notify_contact_message(msg):
    """Email the site owner about a new contact message.

    Reply-To is the visitor, so the owner can answer straight from their inbox.
    Returns True on success. Failures are logged, never raised: the message is
    already saved in the database and the visitor should not see an error.
    """
    recipient = settings.CONTACT_EMAIL
    if not recipient:
        logger.warning("CONTACT_EMAIL is not set; contact message %s not emailed.", msg.pk)
        return False

    body = (
        f"Name: {msg.name}\n"
        f"Email: {msg.email}\n"
        f"Phone: {msg.phone or '-'}\n\n"
        f"{msg.message}\n"
    )
    email = EmailMessage(
        subject=f"New contact message from {msg.name}",
        body=body,
        to=[recipient],
        reply_to=[msg.email],
    )
    try:
        email.send()
    except Exception:
        logger.exception("Failed to send contact notification for message %s", msg.pk)
        return False
    return True
