"""Email service for confirmation and newsletter delivery."""
from __future__ import annotations

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


def get_email_config() -> dict:
    """Get email configuration from environment variables."""
    return {
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("FROM_EMAIL", ""),
        "base_url": os.getenv("BASE_URL", "http://localhost:8000"),
    }


def send_confirmation_email(
    to_email: str,
    user_name: str,
    confirmation_token: str,
) -> bool:
    """
    Send double opt-in confirmation email.
    
    Returns True if email was sent successfully.
    """
    config = get_email_config()
    
    if not os.getenv("SENDGRID_API_KEY"):
        logger.warning("SENDGRID_API_KEY not set. Skipping confirmation email.")
        return False
    
    confirm_url = f"{config['base_url']}/api/confirm/{confirmation_token}"
    
    subject = "Confirm your AI News Digest subscription"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
            .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI News Digest</h1>
            </div>
            <div class="content">
                <h2>Welcome, {user_name}!</h2>
                <p>Thank you for signing up for the AI News Digest newsletter. You're just one click away from receiving personalized AI news updates.</p>
                <p>Please confirm your email address to activate your 3-day free trial:</p>
                <p style="text-align: center;">
                    <a href="{confirm_url}" class="button">Confirm My Email</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{confirm_url}</p>
                <p><strong>What's next?</strong></p>
                <ul>
                    <li>You'll receive personalized AI news based on your selected interests</li>
                    <li>Top 5 articles delivered to your inbox</li>
                    <li>Content from your favorite YouTube channels</li>
                </ul>
            </div>
            <div class="footer">
                <p>This link expires in 24 hours. If you didn't sign up for this newsletter, you can safely ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Welcome to AI News Digest, {user_name}!
    
    Please confirm your email address by visiting this link:
    {confirm_url}
    
    This link expires in 24 hours.
    
    If you didn't sign up for this newsletter, you can safely ignore this email.
    """
    
    return _send_email(to_email, subject, html_body, text_body)


def send_unsubscribe_confirmation(to_email: str, user_name: str) -> bool:
    """Send confirmation that user has been unsubscribed."""
    config = get_email_config()
    
    if not config["smtp_user"] or not config["smtp_password"]:
        return False
    
    subject = "You've been unsubscribed from AI News Digest"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 10px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="content">
                <h2>Goodbye, {user_name} 👋</h2>
                <p>You've been successfully unsubscribed from the AI News Digest newsletter.</p>
                <p>We're sorry to see you go! If you change your mind, you can always sign up again.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"Goodbye, {user_name}. You've been unsubscribed from AI News Digest."
    
    return _send_email(to_email, subject, html_body, text_body)


def _send_email(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """Internal helper that sends mail via SendGrid's Web API."""
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "AI News Digest <no-reply@example.com>")

    if not api_key:
        logger.error("SENDGRID_API_KEY not configured")
        return False

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=text_body,
            html_content=html_body,
        )
        sg = SendGridAPIClient(api_key)
        sg.send(message)
        logger.info("Email sent successfully to %s", to_email)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False
