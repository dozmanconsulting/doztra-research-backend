#!/bin/bash

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DEPLOYING GOOGLE OAUTH INTEGRATION ===${NC}"

# 1. Run database migrations
echo -e "\n${YELLOW}1. Running database migrations...${NC}"
alembic upgrade head

# 2. Set environment variables for Google OAuth
echo -e "\n${YELLOW}2. Setting environment variables...${NC}"

# Check if .env file exists
if [ -f .env ]; then
  # Check if Google OAuth variables already exist in .env
  if grep -q "GOOGLE_OAUTH_CLIENT_ID" .env; then
    echo -e "${GREEN}Google OAuth variables already exist in .env file${NC}"
  else
    # Add Google OAuth variables to .env
    echo -e "\n# Google OAuth Configuration" >> .env
    echo "GOOGLE_OAUTH_CLIENT_ID=your-client-id-here" >> .env
    echo "GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here" >> .env
    echo "BASE_URL=https://doztra-research.onrender.com" >> .env
    echo -e "${GREEN}Added Google OAuth variables to .env file${NC}"
    echo -e "${YELLOW}Please update the client ID and secret in the .env file${NC}"
  fi
else
  # Create .env file with Google OAuth variables
  echo "# Google OAuth Configuration" > .env
  echo "GOOGLE_OAUTH_CLIENT_ID=your-client-id-here" >> .env
  echo "GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here" >> .env
  echo "BASE_URL=https://doztra-research.onrender.com" >> .env
  echo -e "${GREEN}Created .env file with Google OAuth variables${NC}"
  echo -e "${YELLOW}Please update the client ID and secret in the .env file${NC}"
fi

# 3. Restart the application
echo -e "\n${YELLOW}3. Restarting the application...${NC}"
# Add your restart command here, e.g.:
# systemctl restart doztra-backend
# or
# pm2 restart doztra-backend
# or
# docker-compose restart

echo -e "\n${GREEN}=== GOOGLE OAUTH INTEGRATION DEPLOYED SUCCESSFULLY ===${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update the Google OAuth client ID and secret in the .env file"
echo -e "2. Configure the authorized redirect URIs in the Google Cloud Console:"
echo -e "   - https://doztra-research.onrender.com/api/auth/oauth/google/callback"
echo -e "3. Test the integration by clicking the Google sign-in button"
