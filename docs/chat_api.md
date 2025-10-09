# Chat API Documentation

This document provides detailed information about the Chat API endpoints in the Doztra Auth Service.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
   - [Send Message](#send-message)
   - [List Conversations](#list-conversations)
   - [Create Conversation](#create-conversation)
   - [Get Conversation Details](#get-conversation-details)
   - [Update Conversation](#update-conversation)
   - [Delete Conversation](#delete-conversation)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)

## Overview

The Chat API provides endpoints for interacting with the Doztra AI assistant. It allows users to send messages, manage conversations, and retrieve conversation history.

## Authentication

All Chat API endpoints require authentication using a JWT token. Include the token in the `Authorization` header as follows:

```
Authorization: Bearer <token>
```

## Endpoints

### Send Message

Send a message to the AI assistant and get a response.

**URL:** `/api/chat/message`

**Method:** `POST`

**Request Body:**

```json
{
  "message": "Hello, how can you help me with research?",
  "conversation_id": "optional-conversation-id",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000,
  "attachments": []
}
```

**Parameters:**

- `message` (required): The message content to send
- `conversation_id` (optional): ID of an existing conversation
- `model` (optional): AI model to use (default: "gpt-3.5-turbo")
- `temperature` (optional): Controls randomness (0-1)
- `max_tokens` (optional): Maximum tokens in the response
- `attachments` (optional): List of attachment IDs

**Response:**

```json
{
  "conversation_id": "conv123",
  "message_id": "msg456",
  "content": "I can help you with research by providing information on various topics...",
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 42,
    "total_tokens": 67
  }
}
```

### List Conversations

Get a list of the user's conversations.

**URL:** `/api/chat/conversations`

**Method:** `GET`

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 20, max: 100)

**Response:**

```json
[
  {
    "id": "conv123",
    "title": "Research on AI Ethics",
    "created_at": "2025-10-06T07:30:00.000Z",
    "updated_at": "2025-10-06T07:35:22.000Z",
    "is_active": true
  },
  {
    "id": "conv456",
    "title": "Climate Change Discussion",
    "created_at": "2025-10-05T14:22:10.000Z",
    "updated_at": "2025-10-05T14:45:30.000Z",
    "is_active": true
  }
]
```

### Create Conversation

Create a new conversation.

**URL:** `/api/chat/conversations`

**Method:** `POST`

**Request Body:**

```json
{
  "title": "New Research Topic",
  "initial_message": "Let's discuss quantum computing"
}
```

**Parameters:**

- `title` (optional): Title for the new conversation
- `initial_message` (optional): Initial message to start the conversation

**Response:**

```json
{
  "id": "conv789",
  "title": "New Research Topic",
  "created_at": "2025-10-06T07:40:00.000Z",
  "updated_at": "2025-10-06T07:40:00.000Z",
  "is_active": true
}
```

### Get Conversation Details

Get details of a specific conversation including messages.

**URL:** `/api/chat/conversations/{conversation_id}`

**Method:** `GET`

**Path Parameters:**

- `conversation_id`: ID of the conversation to retrieve

**Response:**

```json
{
  "id": "conv123",
  "title": "Research on AI Ethics",
  "created_at": "2025-10-06T07:30:00.000Z",
  "updated_at": "2025-10-06T07:35:22.000Z",
  "is_active": true,
  "messages": [
    {
      "id": "msg123",
      "conversation_id": "conv123",
      "content": "What are the main ethical concerns in AI development?",
      "role": "user",
      "created_at": "2025-10-06T07:30:00.000Z",
      "model": null,
      "metadata": null
    },
    {
      "id": "msg124",
      "conversation_id": "conv123",
      "content": "The main ethical concerns in AI development include...",
      "role": "assistant",
      "created_at": "2025-10-06T07:30:10.000Z",
      "model": "gpt-3.5-turbo",
      "metadata": null
    }
  ]
}
```

### Update Conversation

Update a conversation's details.

**URL:** `/api/chat/conversations/{conversation_id}`

**Method:** `PUT`

**Path Parameters:**

- `conversation_id`: ID of the conversation to update

**Request Body:**

```json
{
  "title": "Updated Conversation Title",
  "is_active": true
}
```

**Parameters:**

- `title` (optional): New title for the conversation
- `is_active` (optional): New active status for the conversation

**Response:**

```json
{
  "id": "conv123",
  "title": "Updated Conversation Title",
  "created_at": "2025-10-06T07:30:00.000Z",
  "updated_at": "2025-10-06T07:45:00.000Z",
  "is_active": true
}
```

### Delete Conversation

Delete a conversation (soft delete).

**URL:** `/api/chat/conversations/{conversation_id}`

**Method:** `DELETE`

**Path Parameters:**

- `conversation_id`: ID of the conversation to delete

**Response:**

```json
{
  "success": true,
  "message": "Conversation deleted successfully"
}
```

## Data Models

### Message

```json
{
  "id": "string",
  "conversation_id": "string",
  "content": "string",
  "role": "user | assistant | system",
  "created_at": "datetime",
  "model": "string | null",
  "metadata": "object | null"
}
```

### Conversation

```json
{
  "id": "string",
  "title": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "is_active": "boolean"
}
```

### ConversationDetail

```json
{
  "id": "string",
  "title": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "is_active": "boolean",
  "messages": [
    {
      "id": "string",
      "conversation_id": "string",
      "content": "string",
      "role": "user | assistant | system",
      "created_at": "datetime",
      "model": "string | null",
      "metadata": "object | null"
    }
  ]
}
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error responses follow this format:

```json
{
  "detail": "Error message describing the issue"
}
```
