#!/usr/bin/env python3
"""Send an email via SMTP over SSL.

Credentials are read from environment variables only, never hardcoded:
  SMTP_HOST   e.g. smtp.qq.com
  SMTP_PORT   e.g. 465
  SMTP_USER   login user (usually the sender mailbox)
  SMTP_AUTH   SMTP authorization code / password
  MAIL_FROM   sender address shown to recipient
  MAIL_TO     recipient address
  MAIL_SUBJECT  optional subject
  MAIL_BODY   message body
"""
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

REQUIRED = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_AUTH", "MAIL_FROM", "MAIL_TO", "MAIL_BODY")


def main() -> int:
    cfg = {k: os.environ.get(k, "").strip() for k in REQUIRED + ("MAIL_SUBJECT",)}
    missing = [k for k in REQUIRED if not cfg[k]]
    if missing:
        print(f"ERROR missing env: {', '.join(missing)}")
        return 2

    msg = EmailMessage()
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = cfg["MAIL_TO"]
    if cfg["MAIL_SUBJECT"]:
        msg["Subject"] = cfg["MAIL_SUBJECT"]
    msg.set_content(cfg["MAIL_BODY"])

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(cfg["SMTP_HOST"], int(cfg["SMTP_PORT"]), context=context, timeout=30) as server:
        server.login(cfg["SMTP_USER"], cfg["SMTP_AUTH"])
        server.send_message(msg)
    print(f"SENT from={cfg['MAIL_FROM']} to={cfg['MAIL_TO']} subject={cfg['MAIL_SUBJECT']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
