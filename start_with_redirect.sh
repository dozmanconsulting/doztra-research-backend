#!/bin/bash
# Start script for Doztra Auth Service with redirect server

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
TARGET_PORT=8001
SOURCE_PORT=8000
HOST="0.0.0.0"

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Doztra Auth Service with Redirect   ${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# Function to start the redirect server
start_redirect_server() {
    echo -e "${BLUE}Starting redirect server from port $SOURCE_PORT to port $TARGET_PORT...${NC}"
    python3 redirect_server.py --source-port $SOURCE_PORT --target-port $TARGET_PORT --target-host $HOST &
    REDIRECT_PID=$!
    echo -e "${GREEN}Redirect server started with PID $REDIRECT_PID${NC}"
}

# Function to start the main service
start_main_service() {
    echo -e "${BLUE}Starting Doztra Auth Service on port $TARGET_PORT...${NC}"
    ./start.sh --port $TARGET_PORT --host $HOST --skip-deps &
    MAIN_PID=$!
    echo -e "${GREEN}Main service started with PID $MAIN_PID${NC}"
}

# Function to clean up on exit
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    if [ ! -z "$REDIRECT_PID" ]; then
        kill $REDIRECT_PID 2>/dev/null
        echo -e "${GREEN}Redirect server stopped${NC}"
    fi
    if [ ! -z "$MAIN_PID" ]; then
        kill $MAIN_PID 2>/dev/null
        echo -e "${GREEN}Main service stopped${NC}"
    fi
    exit 0
}

# Set up trap to catch SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Start the services
start_redirect_server
start_main_service

echo -e "${GREEN}All services started successfully${NC}"
echo -e "${BLUE}Main service is available at:${NC} ${GREEN}http://$HOST:$TARGET_PORT${NC}"
echo -e "${BLUE}Redirect server is running on:${NC} ${GREEN}http://$HOST:$SOURCE_PORT${NC}"
echo -e "${BLUE}API documentation:${NC} ${GREEN}http://$HOST:$TARGET_PORT/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for both processes
wait
