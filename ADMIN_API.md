# Doztra Auth Service - Admin API Documentation

This document provides detailed documentation for the admin-only API endpoints in the Doztra Auth Service.

## Authentication

All admin endpoints require authentication with an admin user token. Include the token in the `Authorization` header:

```
Authorization: Bearer <admin_token>
```

If a non-admin user attempts to access these endpoints, a `403 Forbidden` response will be returned.

## Admin Dashboard

### GET /api/admin/dashboard

Returns statistics and analytics for the admin dashboard.

**Response:**
```json
{
  "user_statistics": {
    "total_users": 1250,
    "active_users": 1100,
    "verified_users": 950,
    "subscription_distribution": {
      "free": 800,
      "basic": 300,
      "professional": 150
    },
    "registration_by_month": {
      "2025-09": 120,
      "2025-08": 105,
      "2025-07": 95
    },
    "active_users_last_30_days": 950,
    "user_growth_rate": 14.3
  },
  "token_usage_total": 12567890,
  "token_usage_by_plan": {
    "free": 2345678,
    "basic": 4567890,
    "professional": 5654322
  },
  "token_usage_by_model": {
    "gpt-4": 8765432,
    "gpt-3.5-turbo": 3802458
  },
  "token_usage_by_day": {
    "2025-10-01": 1234567,
    "2025-10-02": 987654,
    "2025-10-03": 876543,
    "2025-10-04": 765432
  }
}
```

## User Management

### GET /api/admin/users

Returns a list of users with filtering and sorting options.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)
- `filter_by`: Field to filter by (email, name, role, is_active, is_verified, subscription.plan)
- `filter_value`: Value to filter by
- `sort_by`: Field to sort by (id, email, name, created_at, updated_at)
- `sort_desc`: Sort in descending order if true, ascending if false (default: true)

**Response:**
```json
[
  {
    "id": "user123",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-10-01T12:00:00.000Z",
    "updated_at": "2025-10-02T14:30:00.000Z",
    "subscription": {
      "id": "sub123",
      "user_id": "user123",
      "plan": "basic",
      "status": "active",
      "start_date": "2025-10-01T12:00:00.000Z",
      "expires_at": "2026-10-01T12:00:00.000Z",
      "is_active": true,
      "auto_renew": true,
      "stripe_customer_id": "cus_123",
      "stripe_subscription_id": "sub_123",
      "payment_method_id": "pm_123",
      "token_limit": 500000,
      "max_model_tier": "gpt-4",
      "created_at": "2025-10-01T12:00:00.000Z",
      "updated_at": "2025-10-01T12:00:00.000Z"
    }
  },
  // More users...
]
```

### GET /api/admin/users/{user_id}

Returns a specific user by ID.

**Path Parameters:**
- `user_id`: ID of the user to retrieve

**Response:**
```json
{
  "id": "user123",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "user",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-10-01T12:00:00.000Z",
  "updated_at": "2025-10-02T14:30:00.000Z",
  "subscription": {
    "id": "sub123",
    "user_id": "user123",
    "plan": "basic",
    "status": "active",
    "start_date": "2025-10-01T12:00:00.000Z",
    "expires_at": "2026-10-01T12:00:00.000Z",
    "is_active": true,
    "auto_renew": true,
    "stripe_customer_id": "cus_123",
    "stripe_subscription_id": "sub_123",
    "payment_method_id": "pm_123",
    "token_limit": 500000,
    "max_model_tier": "gpt-4",
    "created_at": "2025-10-01T12:00:00.000Z",
    "updated_at": "2025-10-01T12:00:00.000Z"
  }
}
```

### POST /api/admin/users

Creates a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "StrongPassword123!",
  "role": "user",
  "is_active": true,
  "is_verified": true,
  "subscription": {
    "plan": "basic",
    "payment_method_id": "pm_1234567890"
  }
}
```

**Response:**
```json
{
  "id": "user456",
  "name": "John Doe",
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-10-04T20:00:00.000Z",
  "updated_at": "2025-10-04T20:00:00.000Z",
  "subscription": {
    "id": "sub456",
    "user_id": "user456",
    "plan": "basic",
    "status": "active",
    "start_date": "2025-10-04T20:00:00.000Z",
    "expires_at": "2026-10-04T20:00:00.000Z",
    "is_active": true,
    "auto_renew": true,
    "stripe_customer_id": null,
    "stripe_subscription_id": null,
    "payment_method_id": "pm_1234567890",
    "token_limit": 500000,
    "max_model_tier": "gpt-4",
    "created_at": "2025-10-04T20:00:00.000Z",
    "updated_at": "2025-10-04T20:00:00.000Z"
  }
}
```

### PATCH /api/admin/users/{user_id}/status

Updates a user's status (active, verified, role).

**Path Parameters:**
- `user_id`: ID of the user to update

**Request Body:**
```json
{
  "is_active": true,
  "is_verified": true,
  "role": "admin"
}
```

**Response:**
```json
{
  "id": "user123",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "admin",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-10-01T12:00:00.000Z",
  "updated_at": "2025-10-04T20:00:00.000Z",
  "subscription": {
    "id": "sub123",
    "user_id": "user123",
    "plan": "basic",
    "status": "active",
    "start_date": "2025-10-01T12:00:00.000Z",
    "expires_at": "2026-10-01T12:00:00.000Z",
    "is_active": true,
    "auto_renew": true,
    "stripe_customer_id": "cus_123",
    "stripe_subscription_id": "sub_123",
    "payment_method_id": "pm_123",
    "token_limit": 500000,
    "max_model_tier": "gpt-4",
    "created_at": "2025-10-01T12:00:00.000Z",
    "updated_at": "2025-10-01T12:00:00.000Z"
  }
}
```

### DELETE /api/admin/users/{user_id}

Deletes a user.

**Path Parameters:**
- `user_id`: ID of the user to delete

**Response:**
- Status code: 204 No Content

## User Statistics

### GET /api/admin/users/statistics

Returns user statistics.

**Response:**
```json
{
  "total_users": 1250,
  "active_users": 1100,
  "verified_users": 950,
  "subscription_distribution": {
    "free": 800,
    "basic": 300,
    "professional": 150
  },
  "registration_by_month": {
    "2025-09": 120,
    "2025-08": 105,
    "2025-07": 95
  },
  "active_users_last_30_days": 950,
  "user_growth_rate": 14.3
}
```

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "timestamp": "2025-10-04T20:00:00.000Z"
  }
}
```

Common error codes:
- `UNAUTHORIZED`: Authentication required or invalid credentials
- `FORBIDDEN`: User doesn't have permission for the requested action
- `NOT_FOUND`: Requested resource not found
- `VALIDATION_ERROR`: Invalid request parameters
- `INTERNAL_ERROR`: Server-side error

## Security Considerations

1. **Access Control**: Only users with the `admin` role can access these endpoints.
2. **Self-Protection**: Admins cannot deactivate or delete their own accounts.
3. **Role Management**: Admins cannot change their own roles.
4. **Audit Logging**: All admin actions are logged for security auditing purposes.
