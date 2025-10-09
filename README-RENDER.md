# Deploying Doztra Auth Service to Render.com

This guide provides instructions for deploying the Doztra Authentication Service to Render.com.

## Prerequisites

- A Render.com account
- Git repository with your Doztra Auth Service code

## Deployment Steps

### 1. Push Your Code to a Git Repository

Make sure your code is pushed to a Git repository (GitHub, GitLab, etc.) that Render.com can access.

### 2. Create a New Web Service on Render.com

1. Log in to your Render.com account
2. Click on the "New +" button and select "Blueprint"
3. Connect your Git repository
4. Render will automatically detect the `render.yaml` configuration file and set up the services

Alternatively, you can manually create the services:

1. Click on the "New +" button and select "Web Service"
2. Connect your Git repository
3. Configure the service:
   - Name: `doztra-auth-service`
   - Environment: `Python`
   - Build Command: `./render_build.sh`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3. Set Up Environment Variables

If you're not using the Blueprint approach, you'll need to manually set up the environment variables:

1. Go to the "Environment" tab of your web service
2. Add the following environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: A secure random string
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: 10080 (7 days)
   - `REFRESH_TOKEN_EXPIRE_MINUTES`: 43200 (30 days)
   - `CORS_ORIGINS`: ["https://doztra.onrender.com", "https://doztra.ai"]
   - `SMTP_TLS`: True
   - `SMTP_PORT`: 587
   - `SMTP_HOST`: Your SMTP host
   - `SMTP_USER`: Your SMTP username
   - `SMTP_PASSWORD`: Your SMTP password
   - `EMAILS_FROM_EMAIL`: noreply@doztra.ai
   - `EMAILS_FROM_NAME`: Doztra AI
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `OPENAI_API_URL`: https://api.openai.com/v1
   - `DEFAULT_AI_MODEL`: gpt-3.5-turbo
   - `MAX_TOKENS_PER_REQUEST`: 4000

### 4. Create a PostgreSQL Database

1. Click on the "New +" button and select "PostgreSQL"
2. Configure the database:
   - Name: `doztra-auth-db`
   - Database: `doztra_auth`
   - User: `doztra_admin`
   - Plan: Choose an appropriate plan (Free tier for testing)

### 5. Link the Database to the Web Service

1. Go to the "Environment" tab of your web service
2. Add a new environment variable:
   - Key: `DATABASE_URL`
   - Value: Internal Database URL of your PostgreSQL database

### 6. Deploy the Service

1. Click on the "Manual Deploy" button and select "Deploy latest commit"
2. Wait for the build and deployment to complete

## Monitoring and Logs

- You can monitor the status of your deployment in the "Events" tab
- View logs in the "Logs" tab to troubleshoot any issues

## Testing the Deployment

Once deployed, you can test the API using the following endpoints:

- Health check: `https://doztra-auth-service.onrender.com/health`
- API documentation: `https://doztra-auth-service.onrender.com/docs`

## Automatic Deployments

Render.com automatically deploys new commits to the branch you've configured. You can disable this in the "Settings" tab if you prefer manual deployments.

## Custom Domains

To use a custom domain:

1. Go to the "Settings" tab of your web service
2. Under "Custom Domains", click "Add Custom Domain"
3. Follow the instructions to set up DNS records for your domain

## Scaling

If you need to scale your application:

1. Go to the "Settings" tab of your web service
2. Under "Instance Type", select a more powerful instance
3. Click "Save Changes"
