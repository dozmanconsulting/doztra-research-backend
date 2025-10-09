# Chat API Documentation

This document provides an overview of the Chat API endpoints implemented in the Doztra Auth Service.

## Core Chat Functionality

The Chat API provides the following core functionality:

1. Send messages to the AI assistant
2. Create, retrieve, update, and delete conversations
3. Retrieve messages for a specific conversation

## API Endpoints

### Send Message

```
POST /api/messages
```

Sends a message to the AI assistant and gets a response.

**Request Body:**
```json
{
  "message": "Hello, how can you help me with research?",
  "conversation_id": "optional-existing-conversation-id",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000,
  "attachments": []
}
```

**Response:**
```json
{
  "conversation_id": "conversation-uuid",
  "message_id": "message-uuid",
  "content": "I can help you with research in several ways...",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 42,
    "total_tokens": 57
  },
  "created_at": "2025-10-06T13:30:00.000Z"
}
```

### List Conversations

```
GET /api/conversations
```

Gets all conversations for the current user.

**Query Parameters:**
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 20): Maximum number of records to return
- `sort_by` (string, default: "updated_at"): Field to sort by
- `sort_order` (string, default: "desc"): Sort order

**Response:**
```json
[
  {
    "id": "conversation-uuid",
    "title": "Research on AI Ethics",
    "created_at": "2025-10-06T13:00:00.000Z",
    "updated_at": "2025-10-06T13:30:00.000Z",
    "is_active": true,
    "message_count": 5,
    "last_message": "I can help you with research in several ways..."
  },
  // More conversations...
]
```

### Create Conversation

```
POST /api/conversations
```

Creates a new conversation.

**Request Body:**
```json
{
  "title": "Research on AI Ethics",
  "initial_message": "Let's discuss AI ethics",
  "metadata": {
    "category": "research",
    "tags": ["ethics", "AI"]
  }
}
```

**Response:**
```json
{
  "id": "conversation-uuid",
  "title": "Research on AI Ethics",
  "created_at": "2025-10-06T13:00:00.000Z",
  "updated_at": "2025-10-06T13:00:00.000Z",
  "is_active": true
}
```

### Get Conversation Messages

```
GET /api/conversations/{conversation_id}/messages
```

Gets messages for a specific conversation.

**Path Parameters:**
- `conversation_id` (string): ID of the conversation

**Query Parameters:**
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 50): Maximum number of records to return

**Response:**
```json
{
  "id": "conversation-uuid",
  "title": "Research on AI Ethics",
  "created_at": "2025-10-06T13:00:00.000Z",
  "updated_at": "2025-10-06T13:30:00.000Z",
  "is_active": true,
  "messages": [
    {
      "id": "message-uuid",
      "conversation_id": "conversation-uuid",
      "role": "user",
      "content": "Let's discuss AI ethics",
      "created_at": "2025-10-06T13:00:00.000Z"
    },
    {
      "id": "message-uuid-2",
      "conversation_id": "conversation-uuid",
      "role": "assistant",
      "content": "I'd be happy to discuss AI ethics...",
      "created_at": "2025-10-06T13:00:05.000Z",
      "model": "gpt-3.5-turbo"
    }
    // More messages...
  ],
  "total_messages": 5
}
```

### Update Conversation

```
PUT /api/conversations/{conversation_id}
```

Updates a conversation's details.

**Path Parameters:**
- `conversation_id` (string): ID of the conversation

**Request Body:**
```json
{
  "title": "Updated Title",
  "is_active": true
}
```

**Response:**
```json
{
  "id": "conversation-uuid",
  "title": "Updated Title",
  "created_at": "2025-10-06T13:00:00.000Z",
  "updated_at": "2025-10-06T13:35:00.000Z",
  "is_active": true
}
```

### Delete Conversation

```
DELETE /api/conversations/{conversation_id}
```

Deletes a conversation (soft delete).

**Path Parameters:**
- `conversation_id` (string): ID of the conversation

**Response:**
```json
{
  "success": true,
  "message": "Conversation deleted successfully",
  "id": "conversation-uuid"
}
```

## Database Models

### Conversation

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete")
    
    # Virtual properties (not stored in DB)
    message_count = None
    last_message = None
```

### Message

```python
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # AI model information
    model = Column(String, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Metadata for attachments or additional features
    message_metadata = Column(JSON, nullable=True)
```

## Recent Changes

1. Added metadata field to Conversation model
2. Added pagination to conversation messages endpoint
3. Added sorting options to conversations list endpoint
4. Added message count and last message preview to conversation responses
5. Updated API documentation with detailed descriptions
6. Created migration script for the metadata column
