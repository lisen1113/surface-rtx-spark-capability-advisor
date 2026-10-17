"""Send one deployment probe to the configured sender mailbox.

Run using the private systemd EnvironmentFile; never pass SMTP secrets on the
command line or print them to logs. This is not an application registration.
"""
from email.message import EmailMessage
import os
import smtplib
import ssl


def main() -> None:
    sender = os.environ["CAPABILITY_SMTP_FROM"]
    username = os.environ["CAPABILITY_SMTP_USERNAME"]
    if sender != username or sender != "ls@yiheit.net":
        raise SystemExit("Probe is limited to the configured sender mailbox")
    if os.environ.get("CAPABILITY_SMTP_TLS_MODE") != "ssl":
        raise SystemExit("Probe requires SMTP over TLS")
    if os.environ.get("CAPABILITY_SMTP_HOST") != "smtp.exmail.qq.com":
        raise SystemExit("Unexpected SMTP endpoint")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = sender
    message["Subject"] = "Capability Advisor 邮件投递测试"
    message.set_content("能力顾问新服务器的邮件投递测试。此邮件不包含验证码或密码。")
    try:
        with smtplib.SMTP_SSL("smtp.exmail.qq.com", 465, timeout=10,
                              context=ssl.create_default_context()) as server:
            server.login(username, os.environ["CAPABILITY_SMTP_PASSWORD"])
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        raise SystemExit("SMTP probe failed; inspect mailbox settings privately") from None
    print("SMTP probe accepted by provider; recipient delivery still needs confirmation.")


if __name__ == "__main__":
    main()
