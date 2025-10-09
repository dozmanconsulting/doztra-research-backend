# New Features in Doztra Auth Service v0.2.0

This document provides an overview of the new features and API endpoints added in version 0.2.0 of the Doztra Auth Service.

## Token Usage Tracking

The service now tracks token usage for all AI model interactions, providing detailed analytics and enforcing usage limits based on subscription plans.

### New Endpoints

- `GET /api/tokens/me` - Get current user's token usage statistics
- `GET /api/tokens/me/history` - Get current user's token usage history with pagination
- `POST /api/tokens/me/track` - Track token usage for a request
- `GET /api/tokens/admin/usage` - Admin endpoint to get token usage analytics across all users

### Example Response for Token Usage Statistics

```json
{
  "current_period": {
    "start_date": "2025-10-01T00:00:00.000Z",
    "end_date": "2025-10-31T23:59:59.000Z",
    "tokens_used": 245678,
    "tokens_limit": 500000,
    "percentage_used": 49.14
  },
  "breakdown": {
    "chat": {
      "prompt_tokens": 45678,
      "completion_tokens": 150000,
      "total_tokens": 195678
    },
    "plagiarism": {
      "total_tokens": 35000
    },
    "prompt_generation": {
      "total_tokens": 15000
    }
  },
  "models": {
    "gpt-4": 180000,
    "gpt-3.5-turbo": 65678
  },
  "daily_usage": [
    {
      "date": "2025-10-01",
      "total_tokens": 12345
    },
    {
      "date": "2025-10-02",
      "total_tokens": 8765
    },
    {
      "date": "2025-10-04",
      "total_tokens": 15432
    }
  ]
}
```

## User Preferences

Users can now store and retrieve their preferences for theme, notifications, and default AI model.

### New Endpoints

- `GET /api/preferences/me` - Get current user's preferences
- `PUT /api/preferences/me` - Update current user's preferences

### Example Response for User Preferences

```json
{
  "id": "pref_123456",
  "user_id": "user123",
  "theme": "dark",
  "notifications": true,
  "default_model": "gpt-4",
  "created_at": "2025-10-04T15:00:00.000Z",
  "updated_at": "2025-10-04T15:00:00.000Z"
}
```

## Usage Statistics

The service now tracks and provides usage statistics for chat messages, plagiarism checks, prompts generated, and tokens used.

### New Endpoints

- `GET /api/usage/me` - Get current user's usage statistics
- `GET /api/users/me/usage` - Alternative endpoint for user's usage statistics

### Example Response for Usage Statistics

```json
{
  "chat_messages": {
    "used": 152,
    "limit": 500,
    "reset_date": "2025-11-01T00:00:00.000Z"
  },
  "plagiarism_checks": {
    "used": 8,
    "limit": 20,
    "reset_date": "2025-11-01T00:00:00.000Z"
  },
  "prompts_generated": {
    "used": 15,
    "limit": 50,
    "reset_date": "2025-11-01T00:00:00.000Z"
  },
  "tokens": {
    "used": 245678,
    "limit": 500000,
    "reset_date": "2025-11-01T00:00:00.000Z"
  }
}
```

## Enhanced Subscription Management

The subscription system has been enhanced to support different model tiers and token limits based on the subscription plan.

### New Endpoints

- `PUT /api/users/me/subscription` - Update current user's subscription
- `GET /api/users/me/subscription` - Get current user's subscription details

### Example Response for Subscription

```json
{
  "id": "sub_123456",
  "user_id": "user123",
  "plan": "professional",
  "status": "active",
  "start_date": "2025-10-04T15:00:00.000Z",
  "expires_at": "2026-10-04T15:00:00.000Z",
  "is_active": true,
  "auto_renew": true,
  "stripe_customer_id": "cus_123456",
  "stripe_subscription_id": "sub_stripe_123456",
  "payment_method_id": "pm_123456",
  "token_limit": null,
  "max_model_tier": "gpt-4-turbo",
  "created_at": "2025-10-04T15:00:00.000Z",
  "updated_at": "2025-10-04T15:00:00.000Z"
}
```

## Payment Integration

The service now integrates with Stripe for payment processing, allowing users to subscribe to paid plans.

### Updated Registration Endpoint

The registration endpoint now accepts subscription information:

```json
{
  "name": "John Doe",
  "email": "user@example.com",
  "password": "Password123!",
  "role": "user",
  "subscription": {
    "plan": "professional",
    "payment_method_id": "pm_1234567890"
  }
}
```

## Model Tier Access Control

The service now enforces access control to different AI models based on the user's subscription plan:

- Free: Access to gpt-3.5-turbo
- Basic: Access to gpt-4
- Professional: Access to gpt-4-turbo

## Database Schema Changes

The following new tables have been added:

- `token_usage` - Records individual token usage events
- `token_usage_summary` - Provides daily summaries of token usage
- `user_preferences` - Stores user preferences
- `usage_statistics` - Tracks usage statistics

The `subscriptions` table has been updated with the following new fields:

- `is_active` - Whether the subscription is active
- `stripe_customer_id` - Stripe customer ID
- `stripe_subscription_id` - Stripe subscription ID
- `payment_method_id` - Payment method ID
- `token_limit` - Token usage limit
- `max_model_tier` - Maximum AI model tier allowed

## Migration

A migration script has been provided to update the database schema:

```bash
alembic upgrade head
```

This will create the new tables and update the existing ones with the new fields.
