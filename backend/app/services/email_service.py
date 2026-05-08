from __future__ import annotations

from email.message import EmailMessage
import logging
import smtplib

from backend.app.core.config import settings


logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


class EmailService:
    SUBJECT = "[Harvest Slot] 이메일 인증번호 안내"

    @staticmethod
    def build_verification_message(code: str, expire_minutes: int) -> tuple[str, str]:
        subject = EmailService.SUBJECT
        body = (
            "안녕하세요, Harvest Slot입니다.\n\n"
            "이메일 인증번호는 아래와 같습니다.\n\n"
            f"인증번호: {code}\n\n"
            f"이 인증번호는 {expire_minutes}분 동안만 유효합니다.\n"
            "본인이 요청하지 않았다면 이 메일을 무시해주세요.\n"
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
