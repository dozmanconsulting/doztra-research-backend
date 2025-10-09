import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any, Optional
import jinja2

from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Jinja2 environment for email templates
templates_dir = Path(__file__).parent.parent / "templates"
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(templates_dir),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render a template with the given context."""
    template = env.get_template(template_name)
    return template.render(**context)


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> None:
    """Send an email."""
    # For testing - just log the email instead of sending it
    if settings.ENVIRONMENT == "test" or not (settings.SMTP_USER and settings.SMTP_PASSWORD):
        logger.info(f"[MOCK EMAIL] To: {email_to}, Subject: {subject}")
        logger.info(f"[MOCK EMAIL] Content: {text_content or html_content[:100]}...")
        return
    
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message['To'] = email_to
    
    # Plain text version
    if text_content:
        message.attach(MIMEText(text_content, 'plain'))
    
    # HTML version
    message.attach(MIMEText(html_content, 'html'))
    
    try:
        logger.info(f"Attempting to connect to SMTP server: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        logger.info(f"Using SMTP user: {settings.SMTP_USER}")
        logger.info(f"From email: {settings.EMAILS_FROM_EMAIL}")
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            logger.info("SMTP connection established")
            if settings.SMTP_TLS:
                logger.info("Starting TLS")
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                logger.info(f"Logging in with user: {settings.SMTP_USER}")
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                logger.info("Login successful")
            
            logger.info(f"Sending email from {settings.EMAILS_FROM_EMAIL} to {email_to}")
            server.sendmail(
                settings.EMAILS_FROM_EMAIL,
                email_to,
                message.as_string()
            )
            logger.info(f"Email sent successfully to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


def send_verification_email(email_to: str, token: str) -> None:
    """Send an email verification email."""
    verification_url = f"https://doztra.ai/verify-email?token={token}"
    subject = "Verify your email address"
    
    context = {
        "verification_url": verification_url,
        "support_email": "support@doztra.ai",
        "company_name": "Doztra AI"
    }
    
    html_content = render_template("email_verification.html", context)
    text_content = f"""
    Please verify your email address by clicking the link below:
    {verification_url}
    
    If you didn't request this, please ignore this email.
    
    Doztra AI Support
    """
    
    send_email(email_to, subject, html_content, text_content)


def send_password_reset_email(email_to: str, token: str) -> None:
    """Send a password reset email."""
    reset_url = f"https://doztra.ai/reset-password?token={token}"
    subject = "Reset your password"
    
    context = {
        "reset_url": reset_url,
        "support_email": "support@doztra.ai",
        "company_name": "Doztra AI"
    }
    
    html_content = render_template("password_reset.html", context)
    text_content = f"""
    Reset your password by clicking the link below:
    {reset_url}
    
    If you didn't request this, please ignore this email.
    
    Doztra AI Support
    """
    
    send_email(email_to, subject, html_content, text_content)


def send_welcome_email(email_to: str, name: str) -> None:
    """Send a welcome email to new users."""
    subject = "Welcome to Doztra AI!"
    
    context = {
        "name": name,
        "login_url": "https://doztra.ai/login",
        "support_email": "support@doztra.ai",
        "company_name": "Doztra AI"
    }
    
    html_content = render_template("welcome.html", context)
    text_content = f"""
    Welcome to Doztra AI, {name}!
    
    Thank you for signing up. We're excited to have you on board.
    
    Get started by logging in at: https://doztra.ai/login
    
    If you have any questions, feel free to contact our support team at support@doztra.ai.
    
    Best regards,
    The Doztra AI Team
    """
    
    send_email(email_to, subject, html_content, text_content)
