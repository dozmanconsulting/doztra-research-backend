from fastapi import APIRouter, HTTPException, status
import logging
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App imports
from app.schemas.contact import ContactRequest, ContactResponse
from app.utils.email import send_email

router = APIRouter()


@router.post("/contact", response_model=ContactResponse)
async def send_contact_message(request: ContactRequest) -> Any:
    """
    Send a contact form message via email.
    """
    try:
        logger.info(f"Received contact form submission from {request.email}")
        
        # Prepare email content
        subject = f"Contact Form: {request.subject}"
        
        # HTML content
        html_content = f"""
        <html>
        <body>
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {request.name}</p>
            <p><strong>Email:</strong> {request.email}</p>
            <p><strong>Subject:</strong> {request.subject}</p>
            <p><strong>Message:</strong></p>
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0;">
                {request.message.replace('\n', '<br>')}
            </div>
            <hr>
            <p><em>Sent from Doztra AI Contact Form</em></p>
        </body>
        </html>
        """
        
        # Plain text content
        text_content = f"""
        New Contact Form Submission
        
        Name: {request.name}
        Email: {request.email}
        Subject: {request.subject}
        
        Message:
        {request.message}
        
        ---
        Sent from Doztra AI Contact Form
        """
        
        # Send email
        send_email(
            email_to=request.to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        logger.info(f"Contact form message sent successfully to {request.to_email}")
        
        return ContactResponse(
            success=True,
            message="Message sent successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to send contact message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/contact/test")
def test_contact_endpoint():
    """Simple test endpoint to check if the contact service is responding."""
    logger.info("Contact test endpoint called")
    return {"status": "ok", "message": "Contact service is running"}
