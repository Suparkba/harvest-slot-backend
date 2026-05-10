from __future__ import annotations

from email.message import EmailMessage
import logging
import smtplib

from backend.app.core.config import settings


logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


class EmailService:
    SUBJECT = "[Harvest Slot] \uc774\uba54\uc77c \uc778\uc99d\ubc88\ud638 \uc548\ub0b4"

    @staticmethod
    def build_verification_message(code: str, expire_minutes: int) -> tuple[str, str]:
        subject = EmailService.SUBJECT
        body = (
            "\uc548\ub155\ud558\uc138\uc694. Harvest Slot\uc785\ub2c8\ub2e4.\n\n"
            "\uc774\uba54\uc77c \uc778\uc99d\ubc88\ud638\ub294 \uc544\ub798\uc640 \uac19\uc2b5\ub2c8\ub2e4.\n\n"
            f"\uc778\uc99d\ubc88\ud638: {code}\n\n"
            f"\ubcf8 \uc778\uc99d\ubc88\ud638\ub294 {expire_minutes}\ubd84 \ub3d9\uc548\ub9cc \uc720\ud6a8\ud569\ub2c8\ub2e4.\n"
            "\ubcf8\uc778\uc774 \uc694\uccad\ud558\uc9c0 \uc54a\uc558\ub2e4\uba74 \uc774 \uba54\uc77c\uc744 \ubb34\uc2dc\ud574\uc8fc\uc138\uc694.\n"
        )
        return subject, body

    def send_verification_email(self, email: str, code: str, expire_minutes: int) -> None:
        if settings.email_dev_mode:
            logger.info("EMAIL_DEV_MODE verification code email=%s code=%s", email, code)
            return

        if not settings.smtp_host or not settings.smtp_from:
            raise EmailDeliveryError("smtp configuration missing")

        subject, body = self.build_verification_message(code, expire_minutes)
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_from
        message["To"] = email
        message.set_content(body)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        except Exception as exc:
            logger.exception("failed to send verification email to %s", email)
            raise EmailDeliveryError("failed to send verification email") from exc
