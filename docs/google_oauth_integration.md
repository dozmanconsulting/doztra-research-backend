# Google OAuth Integration for Doztra

This document provides a comprehensive guide to the Google OAuth integration in the Doztra platform.

## Overview

The Google OAuth integration allows users to sign up and log in to Doztra using their Google accounts. This provides a seamless authentication experience and reduces friction in the user onboarding process.

## Architecture

The integration follows a standard OAuth 2.0 flow:

1. User clicks "Sign in with Google" button
2. User is redirected to Google's authentication page
3. After successful authentication, Google redirects back to our application with an authorization code
4. Our backend exchanges the authorization code for access and refresh tokens
5. Our backend creates or updates the user account and issues our own JWT tokens
6. User is redirected to the application dashboard

## Components

### Backend Components

- **OAuth Configuration** (`app/core/oauth_config.py`): Contains the configuration for Google OAuth
- **OAuth Service** (`app/services/oauth.py`): Handles the OAuth flow and token exchange
- **Auth OAuth Service** (`app/services/auth_oauth.py`): Integrates OAuth authentication with our existing auth system
- **OAuth Routes** (`app/api/routes/oauth.py`): Exposes endpoints for initiating OAuth flow and handling callbacks
- **User Model** (`app/models/user.py`): Extended with OAuth-related fields

### Frontend Components

- **Google Auth Service** (`src/services/googleAuthService.ts`): Handles the OAuth flow on the frontend
- **Google Callback Component** (`src/pages/GoogleCallback.tsx`): Handles the OAuth callback from Google
- **Login/Signup Components**: Updated with Google sign-in buttons

## Database Schema Changes

The following fields were added to the `users` table:

- `oauth_provider`: The OAuth provider (e.g., 'google')
- `oauth_user_id`: The user ID from the OAuth provider
- `oauth_access_token`: The OAuth access token
- `oauth_refresh_token`: The OAuth refresh token
- `oauth_token_expires_at`: The expiration time of the OAuth access token

Additionally, `hashed_password` was made nullable to support OAuth users who don't have a password.

## API Endpoints

### OAuth Login

- **Endpoint**: `/api/auth/oauth/login/google`
- **Method**: GET
- **Description**: Initiates the Google OAuth flow by redirecting to Google's authentication page
- **Response**: 302 Redirect to Google's authentication page

### OAuth Callback

- **Endpoint**: `/api/auth/oauth/google/callback`
- **Method**: GET
- **Parameters**: 
  - `code`: Authorization code from Google
  - `state`: Optional state parameter for CSRF protection
- **Description**: Handles the callback from Google, exchanges the code for tokens, and creates or updates the user
- **Response**: User data with access and refresh tokens

## Setup Instructions

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Select "Web application" as the application type
6. Add authorized JavaScript origins:
   - `https://doztra-research.onrender.com`
   - `http://localhost:8000` (for development)
7. Add authorized redirect URIs:
   - `https://doztra-research.onrender.com/api/auth/oauth/google/callback`
   - `http://localhost:8000/api/auth/oauth/google/callback` (for development)
8. Click "Create" and note your Client ID and Client Secret

### 2. Backend Configuration

1. Run the deployment script:
   ```
   ./deploy_google_auth.sh
   ```
2. Update the `.env` file with your Google OAuth credentials:
   ```
   GOOGLE_OAUTH_CLIENT_ID=your-client-id
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   BASE_URL=https://doztra-research.onrender.com
   ```
3. Restart the application

### 3. Testing

Run the test script to verify the integration:
```
./test_google_oauth_integration.sh
```

For a complete end-to-end test, visit:
```
https://doztra-research.onrender.com/api/auth/oauth/login/google
```

## Troubleshooting

### Common Issues

1. **Redirect URI mismatch**: Ensure the redirect URI in the Google Cloud Console exactly matches the one in your application
2. **Invalid client ID or secret**: Verify that the client ID and secret in the `.env` file are correct
3. **Missing environment variables**: Make sure the environment variables are properly loaded
4. **CORS issues**: Check that the frontend domain is allowed in the CORS configuration

### Debugging

- Check the server logs for error messages
- Use the Network tab in browser developer tools to inspect the OAuth flow
- Test the OAuth endpoints directly using curl or Postman

## Security Considerations

- **CSRF Protection**: The OAuth flow includes state parameters to prevent CSRF attacks
- **Token Storage**: OAuth tokens are stored securely in the database
- **Token Expiration**: Access tokens expire after a short period
- **Refresh Tokens**: Refresh tokens are rotated for security

## Future Improvements

- Add support for additional OAuth providers (e.g., GitHub, Microsoft)
- Implement account linking for users who sign up with email and later want to connect their Google account
- Add multi-factor authentication options for OAuth users
