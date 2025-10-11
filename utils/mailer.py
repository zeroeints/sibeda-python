from __future__ import annotations
import smtplib
from email.message import EmailMessage
from typing import Iterable, Tuple
from config import get_settings

class MailSendError(Exception):
    pass

def _build_message(subject: str, body_text: str, body_html: str | None, to: list[str], from_addr: str, from_name: str | None = None) -> EmailMessage:
        msg = EmailMessage()
        display_from = f"{from_name} <{from_addr}>" if from_name else from_addr
        msg["From"] = display_from
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg.set_content(body_text)
        if body_html:
                msg.add_alternative(body_html, subtype="html")
        return msg

def _otp_templates(kind: str, otp: str) -> Tuple[str, Tuple[str, str]]:
        if kind == "register":
                subject = "Kode Verifikasi Akun"
                plain = (
                        "Halo,\n\n"
                        f"Berikut kode verifikasi akun Anda: {otp}\n"
                        "Kode berlaku selama 2 menit.\n\n"
                        "Terima kasih."
                )
                html = f"""
<html>
    <body style='font-family: Arial, sans-serif; line-height:1.5;'>
        <p>Halo,</p>
        <p>Berikut kode verifikasi akun Anda:</p>
        <p style='font-size:24px;font-weight:bold;letter-spacing:4px;'>{otp}</p>
    <p>Kode berlaku selama <strong>2 menit</strong>.</p>
        <p>Terima kasih.</p>
    </body>
</html>
""".strip()
                return subject, (plain, html)
      
        subject = "Kode Reset Password"
        plain = (
                "Halo,\n\n"
                f"Berikut kode reset password Anda: {otp}\n"
                "Kode berlaku selama 2 menit.\n\n"
                "Terima kasih."
        )
        html = f"""
<html>
    <body style='font-family: Arial, sans-serif; line-height:1.5;'>
        <p>Halo,</p>
        <p>Berikut kode <strong>reset password</strong> Anda:</p>
        <p style='font-size:24px;font-weight:bold;letter-spacing:4px;'>{otp}</p>
    <p>Kode berlaku selama <strong>2 menit</strong>.</p>
        <p>Jika Anda tidak meminta reset, abaikan email ini.</p>
        <p>Terima kasih.</p>
    </body>
</html>
""".strip()
        return subject, (plain, html)

def send_email(subject: str, body_text: str, to: Iterable[str], body_html: str | None = None):
    settings = get_settings()
    if not settings.smtp_host or not settings.mail_from:
        raise MailSendError("SMTP not configured (SMTP_HOST or MAIL_FROM missing)")
    to_list = list(to)
    if not to_list:
        raise ValueError("Recipient list empty")

    msg = _build_message(subject, body_text, body_html, to_list, settings.mail_from, settings.mail_from_name)

    try:
        if settings.smtp_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 587, timeout=15) as server:
                server.ehlo()
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 25, timeout=15) as server:
                server.ehlo()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
    except Exception as e:
        raise MailSendError(str(e)) from e

def send_registration_otp(email: str, otp: str):
    subject, (plain, html) = _otp_templates("register", otp)
    send_email(subject, plain, [email], html)

def send_password_reset_otp(email: str, otp: str):
    subject, (plain, html) = _otp_templates("reset", otp)
    send_email(subject, plain, [email], html)
