from pydantic import BaseModel


class Message(BaseModel):
    """Simple message response schema."""
    message: str
