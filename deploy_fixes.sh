#!/bin/bash

# Script to deploy fixes to the Doztra backend service
# This script applies database migrations and restarts the service

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DOZTRA BACKEND FIX DEPLOYMENT SCRIPT ===${NC}"
echo -e "${YELLOW}This script will apply database migrations and restart the service${NC}"
echo 

# Check if running in the correct directory
if [ ! -f "app/main.py" ]; then
  echo -e "${RED}Error: This script must be run from the root of the doztra-backend-service-v1 directory${NC}"
  exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  echo -e "${YELLOW}Activating virtual environment...${NC}"
  source .venv/bin/activate
  echo -e "${GREEN}Virtual environment activated${NC}"
else
  echo -e "${YELLOW}No virtual environment found, continuing with system Python${NC}"
fi

# Apply database migrations
echo -e "${YELLOW}Applying database migrations...${NC}"
python -m alembic upgrade head

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Database migrations applied successfully${NC}"
else
  echo -e "${RED}Error applying database migrations${NC}"
  exit 1
fi

# Run the debug script to verify fixes
echo -e "${YELLOW}Running debug script to verify fixes...${NC}"
chmod +x debug_auth.sh
./debug_auth.sh > debug_output.log 2>&1

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Debug script completed successfully${NC}"
  echo -e "${YELLOW}Debug output saved to debug_output.log${NC}"
else
  echo -e "${RED}Error running debug script${NC}"
  echo -e "${YELLOW}Check debug_output.log for details${NC}"
fi

# Restart the service (if running in a production environment)
if [ -n "$RENDER_SERVICE_ID" ]; then
  echo -e "${YELLOW}Restarting service on Render...${NC}"
  # Render automatically restarts on code changes, so we just need to touch a file
  touch app/main.py
  echo -e "${GREEN}Service restart triggered${NC}"
else
  echo -e "${YELLOW}Not running on Render, skipping service restart${NC}"
  echo -e "${YELLOW}To restart the service manually, run:${NC}"
  echo -e "  ${GREEN}uvicorn app.main:app --reload${NC}"
fi

echo -e "${YELLOW}=== DEPLOYMENT COMPLETE ===${NC}"
echo -e "${YELLOW}Check the logs for any errors${NC}"
