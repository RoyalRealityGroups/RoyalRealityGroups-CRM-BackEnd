"""
Email service that reads SMTP credentials from the SMTPConfig database table.

Usage:
    from Core.System.email_service import send_email

    send_email(
        to=['user@example.com'],
        subject='Password Reset OTP',
        body='Your OTP is 12345',
    )

    # Or HTML email:
    send_email(
        to=['user@example.com'],
        subject='Welcome',
        html_body='<h1>Welcome!</h1>',
    )
"""
import logging
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger('Common')


def get_smtp_config():
    """Get the active SMTP configuration from the database."""
    from Core.System.models import SMTPConfig
    config = SMTPConfig.objects.filter(is_active=True, is_deleted=False).first()
    return config


def get_email_backend():
    """Create an SMTP email backend from the active database config."""
    config = get_smtp_config()
    if not config:
        return None, None

    backend = EmailBackend(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        use_tls=config.use_tls,
        use_ssl=config.use_ssl,
        fail_silently=False,
    )

    from_email = f'"{config.from_name}" <{config.from_email}>' if config.from_name else config.from_email
    return backend, from_email


def send_email(to, subject, body='', html_body=None, cc=None, bcc=None, attachments=None):
    """
    Send an email using the SMTP config stored in the database.

    Args:
        to: list of recipient emails
        subject: email subject
        body: plain text body
        html_body: optional HTML body
        cc: list of CC emails
        bcc: list of BCC emails
        attachments: list of (filename, content, mimetype) tuples

    Returns:
        True if sent successfully, False otherwise
    """
    if isinstance(to, str):
        to = [to]

    backend, from_email = get_email_backend()

    if not backend:
        # No SMTP configured — log to console
        print("\n" + "=" * 50)
        print("  EMAIL (SMTP not configured)")
        print("=" * 50)
        print(f"  To:      {', '.join(to)}")
        print(f"  Subject: {subject}")
        print(f"  Body:    {body[:200]}")
        print("=" * 50 + "\n")
        logger.warning(f"SMTP not configured. Email to {to} with subject '{subject}' was NOT sent.")
        return False

    try:
        if html_body:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body or 'Please view this email in an HTML-capable client.',
                from_email=from_email,
                to=to,
                cc=cc,
                bcc=bcc,
                connection=backend,
            )
            msg.attach_alternative(html_body, 'text/html')
        else:
            msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_email,
                to=to,
                cc=cc,
                bcc=bcc,
                connection=backend,
            )

        if attachments:
            for filename, content, mimetype in attachments:
                msg.attach(filename, content, mimetype)

        msg.send()
        logger.info(f"Email sent to {to} — Subject: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        print(f"\n  EMAIL SEND FAILED: {e}\n")
        return False
