from pydantic import BaseModel, EmailStr
from typing import Optional


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    to_email: Optional[str] = "info@doztra.co.uk"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "subject": "Technical Support",
                "message": "I need help with my account setup.",
                "to_email": "info@doztra.co.uk"
            }
        }


class ContactResponse(BaseModel):
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Message sent successfully"
            }
        }
