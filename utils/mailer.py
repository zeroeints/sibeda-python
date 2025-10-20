from __future__ import annotations
import smtplib
import ssl
import logging
import time
from email.message import EmailMessage
from typing import Iterable, Tuple
from config import get_settings

logger = logging.getLogger(__name__)

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
    <table align='center' width='100%' cellpadding='0' cellspacing='0' style='padding:20px 0'>
        <tbody>
            <tr>
                <td>
                    <table align='center' width='100%' cellpadding='0' cellspacing='0' style='max-width:800px;padding:28px 0;background:#ffffff;border-radius:12px'>
                        <tbody>
                            <tr>
                                <td align='center'>
                                    <div style='display:inline-block;background-color:#fafafa;border-radius:50%;padding:16px'>
                                        <img src='https://upload.wikimedia.org/wikipedia/commons/d/d2/Lambang_Kabupaten_Badung.png' alt='Logo' style='width:120px;height:120px;display:block' data-image-whitelisted='' class='CToWUd' data-bit='iit'>
                                    </div>

                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <table align='center' width='100%' cellpadding='0' cellspacing='0' style='max-width:600px;padding:12px 24px'>
                                        <tbody>
                                            <tr>
                                                <td align='center' style='font-size:20px;font-weight:bold;margin-bottom:20px;color:#000'>
                                                    Kode OTP Kamu untuk Registrasi
                                                </td>
                                            </tr>

                                            <tr>
                                                <td style='padding-top:24px;font-size:16px;line-height:1.6;color:#333'><span class='im'>
                                                        Hai,<br>
                                                        Terima kasih telah mendaftar!<br>
                                                        Berikut adalah kode OTP kamu untuk menyelesaikan proses registrasi:<br><br></span>
                                                    <table align='center' width='100%' cellpadding='0' cellspacing='0' style='max-width:600px;padding:0 24px'>
                                                        <tbody>
                                                            <tr>
                                                                <td style='background-color:#f0f0f0;padding:16px;border-radius:12px;font-size:12px;color:#555;text-align:center'>
                                                                    <p class='text-align:center;' style='font-size:20px;font-weight:bold;color:#000'><b>{otp}</b></p>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>

                                                    <br>
                                                    Kode ini hanya berlaku selama 2 menit, jadi pastikan kamu segera menggunakannya ya.<br>
                                                    Kalau kamu tidak merasa melakukan registrasi, abaikan saja email ini.
                                                    </span>
                                                </td>
                                            </tr>

                                            <tr>
                                                <td style='padding-top:24px;font-size:14px;color:#777'>
                                                    Terima kasih,
                                                    Tim <span class='il'><span class='il'><span class='il'>SIBEDA</span></span></span>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    <div>
                                        <div class='adm'>
                                            <div id='q_79' class='ajR h4' data-tooltip='Sembunyikan konten yang diperluas' aria-label='Sembunyikan konten yang diperluas' aria-expanded='true'>
                                                <div class='ajT'></div>
                                            </div>
                                        </div>
                                        <div class='im'>


                                            <table align='center' width='100%' cellpadding='0' cellspacing='0' style='max-width:600px;padding:0 24px'>
                                                <tbody>
                                                    <tr>
                                                        <td style='background-color:#f0f0f0;padding:16px;border-radius:12px;font-size:12px;color:#555;text-align:center'>
                                                            This is an automated message from <span class='il'><span class='il'><span class='il'>SIBEDA</span></span></span>. This inbox is not monitored, so please do not reply. For support, contact us through our customer service.
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style='padding:16px;border-radius:12px;font-size:12px;color:#555;text-align:center'>
                                                            ©2025 <span class='il'><span class='il'><span class='il'>SIBEDA</span></span></span> - All Rights Reserved.
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
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
        logger.warning("SMTP not configured (SMTP_HOST or MAIL_FROM missing)")
        raise MailSendError("SMTP not configured (SMTP_HOST or MAIL_FROM missing)")
    to_list = list(to)
    if not to_list:
        raise ValueError("Recipient list empty")

    msg = _build_message(subject, body_text, body_html, to_list, settings.mail_from, settings.mail_from_name)
    
    # Gunakan timeout yang lebih panjang untuk menghindari timeout di network lambat
    smtp_timeout = getattr(settings, 'smtp_timeout', 30)
    start_time = time.time()
    
    # Buat SSL context yang lebih permissive untuk menghindari handshake errors
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    try:
        logger.info(f"Sending email to {to_list}: {subject}")
        
        # Port 465 menggunakan SMTP_SSL (lebih stabil daripada STARTTLS)
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, 465, context=context, timeout=smtp_timeout) as server:
                server.set_debuglevel(1 if settings.debug else 0)
                logger.debug(f"Connected via SMTP_SSL to {settings.smtp_host}:465")
                
                if settings.smtp_user and settings.smtp_password:
                    logger.debug(f"Logging in as {settings.smtp_user}")
                    server.login(settings.smtp_user, settings.smtp_password)
                    logger.debug("Login successful")
                
                logger.info(f"Sending message to {to_list}")
                server.send_message(msg)
                
                duration = time.time() - start_time
                logger.info(f"Email sent successfully to {to_list} in {duration:.2f}s")
        
        # Port 587 atau TLS mode menggunakan STARTTLS
        elif settings.smtp_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 587, timeout=smtp_timeout) as server:
                server.set_debuglevel(1 if settings.debug else 0)
                logger.debug(f"Connected to SMTP server {settings.smtp_host}:{settings.smtp_port or 587}")
                
                server.ehlo()
                logger.debug("STARTTLS negotiation...")
                server.starttls(context=context)
                server.ehlo()  # EHLO ulang setelah STARTTLS
                
                if settings.smtp_user and settings.smtp_password:
                    logger.debug(f"Logging in as {settings.smtp_user}")
                    server.login(settings.smtp_user, settings.smtp_password)
                    logger.debug("Login successful")
                
                logger.info(f"Sending message to {to_list}")
                server.send_message(msg)
                
                duration = time.time() - start_time
                logger.info(f"Email sent successfully to {to_list} in {duration:.2f}s")
        
        # Plain SMTP tanpa TLS (port 25, tidak direkomendasikan)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 25, timeout=smtp_timeout) as server:
                server.set_debuglevel(1 if settings.debug else 0)
                logger.debug(f"Connected to SMTP server {settings.smtp_host}:{settings.smtp_port or 25}")
                
                server.ehlo()
                
                if settings.smtp_user and settings.smtp_password:
                    logger.debug(f"Logging in as {settings.smtp_user}")
                    server.login(settings.smtp_user, settings.smtp_password)
                    logger.debug("Login successful")
                
                logger.info(f"Sending message to {to_list}")
                server.send_message(msg)
                
                duration = time.time() - start_time
                logger.info(f"Email sent successfully to {to_list} in {duration:.2f}s")
    
    # Exception handling: most specific first, then general
    except smtplib.SMTPAuthenticationError as e:
        duration = time.time() - start_time
        logger.error(f"SMTP authentication failed after {duration:.2f}s: {e}")
        raise MailSendError(f"SMTP authentication failed: {e}") from e
    except smtplib.SMTPException as e:
        duration = time.time() - start_time
        logger.error(f"SMTP error after {duration:.2f}s: {e}", exc_info=True)
        raise MailSendError(f"SMTP error: {e}") from e
    except (ConnectionResetError, ConnectionRefusedError, OSError) as e:
        duration = time.time() - start_time
        logger.error(f"Connection error after {duration:.2f}s: {e}. Possibly rate-limited by Gmail or firewall issue.")
        raise MailSendError(f"Connection error: {e}") from e
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Email send failed after {duration:.2f}s: {e}", exc_info=True)
        raise MailSendError(str(e)) from e

def send_registration_otp(email: str, otp: str):
    try:
        subject, (plain, html) = _otp_templates("register", otp)
        send_email(subject, plain, [email], html)
        logger.info(f"Registration OTP sent successfully to {email}")
    except MailSendError as e:
        logger.warning(f"Failed to send registration OTP to {email}: {e}")
        # Re-raise untuk beri tahu caller bahwa email gagal
        raise

def send_password_reset_otp(email: str, otp: str):
    try:
        subject, (plain, html) = _otp_templates("reset", otp)
        send_email(subject, plain, [email], html)
        logger.info(f"Password reset OTP sent successfully to {email}")
    except MailSendError as e:
        logger.warning(f"Failed to send password reset OTP to {email}: {e}")
        # Re-raise untuk beri tahu caller bahwa email gagal
        raise
