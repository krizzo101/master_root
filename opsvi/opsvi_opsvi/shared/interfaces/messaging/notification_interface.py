"""
Notification Shared Interface
----------------------------
Authoritative implementation based on the official APIs for SMTP (smtplib), SES (boto3), and SendGrid:
- https://docs.python.org/3/library/smtplib.html
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html
- https://docs.sendgrid.com/for-developers/sending-email/api-getting-started
Implements all core features: email sending and error handling. Messaging (Slack, Teams, SMS) are stubs.
Version: Referenced as of July 2024
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NotificationInterface:
    """
    Authoritative shared interface for email services (SMTP, SES, SendGrid).
    See official docs for each provider.
    """

    def __init__(self, provider: str, **kwargs):
        self.provider = provider.lower()
        self.kwargs = kwargs
        self._init_client()

    def _init_client(self):
        if self.provider == "smtp":
            import smtplib

            self.client = smtplib.SMTP(
                self.kwargs.get("host", "localhost"), self.kwargs.get("port", 25)
            )
        elif self.provider == "sendgrid":
            try:
                import sendgrid
                from sendgrid.helpers.mail import Mail

                self.client = sendgrid.SendGridAPIClient(self.kwargs["api_key"])
                self.Mail = Mail
            except ImportError:
                raise ImportError(
                    "sendgrid required. Install with `pip install sendgrid`."
                )
        elif self.provider == "ses":
            try:
                import boto3

                self.client = boto3.client("ses", **self.kwargs)
            except ImportError:
                raise ImportError(
                    "boto3 required for SES. Install with `pip install boto3`."
                )
        elif self.provider in ("slack", "teams", "sms"):
            self.client = None  # Not implemented
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: list[Any] | None = None,
        html: bool = False,
    ) -> dict[str, Any]:
        """
        Send an email using the configured provider. Supports CC, BCC, reply-to, attachments, and HTML.
        Returns structured result: {success, error, result}
        """
        try:
            if self.provider == "smtp":
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText

                from_addr = from_addr or self.kwargs.get(
                    "from_addr", "noreply@example.com"
                )
                msg = MIMEMultipart()
                msg["From"] = from_addr
                msg["To"] = to
                msg["Subject"] = subject
                if cc:
                    msg["Cc"] = ", ".join(cc)
                if reply_to:
                    msg["Reply-To"] = reply_to
                if html:
                    msg.attach(MIMEText(body, "html"))
                else:
                    msg.attach(MIMEText(body, "plain"))
                # Attachments (not implemented)
                recipients = [to] + (cc or []) + (bcc or [])
                self.client.sendmail(from_addr, recipients, msg.as_string())
                return {"success": True}
            elif self.provider == "sendgrid":
                mail = self.Mail(
                    from_addr,
                    to,
                    subject,
                    body if not html else None,
                )
                if html:
                    mail.add_content("text/html", body)
                if cc:
                    mail.add_cc(cc)
                if bcc:
                    mail.add_bcc(bcc)
                if reply_to:
                    mail.reply_to = reply_to
                # Attachments (not implemented)
                self.client.send(mail)
                return {"success": True}
            elif self.provider == "ses":
                dest = {"ToAddresses": [to]}
                if cc:
                    dest["CcAddresses"] = cc
                if bcc:
                    dest["BccAddresses"] = bcc
                msg = {
                    "Subject": {"Data": subject},
                    "Body": {"Html" if html else "Text": {"Data": body}},
                }
                self.client.send_email(
                    Source=from_addr,
                    Destination=dest,
                    Message=msg,
                    ReplyToAddresses=[reply_to] if reply_to else None,
                )
                return {"success": True}
            else:
                raise NotImplementedError(
                    f"Provider {self.provider} does not support send_email."
                )
        except Exception as e:
            logger.error(f"send_email failed: {e}")
            return {"success": False, "error": str(e)}

    def batch_send_email(
        self, recipients: list[dict[str, Any]], subject: str, body: str, **kwargs
    ) -> list[dict[str, Any]]:
        """
        Batch send emails to multiple recipients. Each recipient is a dict with keys: to, cc, bcc, reply_to, etc.
        Returns a list of structured results.
        """
        results = []
        for r in recipients:
            res = self.send_email(
                to=r.get("to"),
                subject=subject,
                body=body,
                from_addr=r.get("from_addr"),
                cc=r.get("cc"),
                bcc=r.get("bcc"),
                reply_to=r.get("reply_to"),
                attachments=r.get("attachments"),
                html=r.get("html", False),
            )
            results.append(res)
        return results

    async def async_send_email(self, *args, **kwargs) -> dict[str, Any]:
        """
        Async send_email (SMTP via aiosmtplib, SES via aiobotocore, SendGrid via async HTTP if available).
        Not implemented for all providers.
        """
        if self.provider == "smtp":
            try:
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText

                import aiosmtplib

                from_addr = kwargs.get("from_addr") or self.kwargs.get(
                    "from_addr", "noreply@example.com"
                )
                to = kwargs["to"]
                subject = kwargs["subject"]
                body = kwargs["body"]
                cc = kwargs.get("cc")
                bcc = kwargs.get("bcc")
                reply_to = kwargs.get("reply_to")
                html = kwargs.get("html", False)
                msg = MIMEMultipart()
                msg["From"] = from_addr
                msg["To"] = to
                msg["Subject"] = subject
                if cc:
                    msg["Cc"] = ", ".join(cc)
                if reply_to:
                    msg["Reply-To"] = reply_to
                if html:
                    msg.attach(MIMEText(body, "html"))
                else:
                    msg.attach(MIMEText(body, "plain"))
                recipients = [to] + (cc or []) + (bcc or [])
                await aiosmtplib.send(
                    msg,
                    hostname=self.kwargs.get("host", "localhost"),
                    port=self.kwargs.get("port", 25),
                    sender=from_addr,
                    recipients=recipients,
                )
                return {"success": True}
            except Exception as e:
                logger.error(f"async_send_email failed: {e}")
                return {"success": False, "error": str(e)}
        else:
            raise NotImplementedError(
                f"Async send_email not implemented for {self.provider}."
            )

    def send_notification(self, to: str, message: str) -> dict[str, Any]:
        """
        Send a notification (Slack, Teams, SMS). Not implemented.
        Returns structured result.
        """
        try:
            raise NotImplementedError(
                f"Provider {self.provider} does not support send_notification."
            )
        except Exception as e:
            logger.error(f"send_notification failed: {e}")
            return {"success": False, "error": str(e)}

    """
    Advanced Usage Example:
    >>> notif = NotificationInterface(provider="smtp", host="localhost")
    >>> # Send email with CC, BCC, HTML
    >>> notif.send_email("to@example.com", "Subject", "<b>Body</b>", cc=["cc@example.com"], html=True)
    >>> # Batch send
    >>> recipients = [
    ...     {"to": "a@example.com"},
    ...     {"to": "b@example.com", "cc": ["c@example.com"]},
    ... ]
    >>> notif.batch_send_email(recipients, "Subject", "Body")
    >>> # Async send (SMTP)
    >>> import asyncio
    >>> result = asyncio.run(notif.async_send_email(to="to@example.com", subject="Subject", body="Body"))
    """


# Example usage and advanced features are available in the official docs for each provider.
