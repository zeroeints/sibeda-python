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
    <table align='center' width='100%' cellpadding='0' cellspacing='0' style='padding:20px 0'>
        <tbody>
            <tr>
                <td>
                    <table align='center' width='100%' cellpadding='0' cellspacing='0' style='max-width:800px;padding:28px 0;background:#ffffff;border-radius:12px'>
                        <tbody>
                            <tr>
                                <td align='center'>
                                    <div style='display:inline-block;background-color:#fafafa;border-radius:50%;padding:16px'>
                                        <img src='https://kelurahantanjungbenoa.badungkab.go.id/storage/kelurahantanjungbenoa/image/PEMKAB%20BADUNG.png' alt='Logo' style='width:120px;height:80px;display:block' data-image-whitelisted='' class='CToWUd' data-bit='iit'>
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
                                                                    <p class='text-align:center;'><b>{otp}</b></p>
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
