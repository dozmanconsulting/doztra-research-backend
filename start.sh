#!/bin/bash
# Start script for Doztra Auth Service

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
PORT=8000
HOST="0.0.0.0"
RELOAD=true
WORKERS=1
DEBUG=false
FORCE_DB_INIT=false
FORCE_DB_RECREATE=false
SKIP_DEPS=false
SKIP_DB=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -p|--port)
            PORT="$2"
            shift
            shift
            ;;
        -h|--host)
            HOST="$2"
            shift
            shift
            ;;
        --no-reload)
            RELOAD=false
            shift
            ;;
        -w|--workers)
            WORKERS="$2"
            shift
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        --force-db-init)
            FORCE_DB_INIT=true
            shift
            ;;
        --force-db-recreate)
            FORCE_DB_RECREATE=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-db)
            SKIP_DB=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -p, --port PORT       Port to run the server on (default: 8000)"
            echo "  -h, --host HOST       Host to bind to (default: 0.0.0.0)"
            echo "  --no-reload           Disable auto-reload"
            echo "  -w, --workers N       Number of worker processes (default: 1)"
            echo "  -d, --debug           Enable debug mode"
            echo "  --force-db-init       Force database initialization"
            echo "  --force-db-recreate   Force database recreation (drops all tables)"
            echo "  --skip-deps           Skip dependency installation"
            echo "  --skip-db            Skip database setup"
            echo "  --help                Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}      Doztra Auth Service Starter     ${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q && [ "$SKIP_DB" = false ]; then
    echo -e "${YELLOW}Warning: PostgreSQL does not appear to be running.${NC}"
    echo -e "Please start PostgreSQL before continuing."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found.${NC}"
    echo -e "Creating .env file from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file from example. Please edit it with your configuration.${NC}"
        
        # Generate a random secret key
        echo -e "${BLUE}Generating a random secret key...${NC}"
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        sed -i.bak "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env && rm -f .env.bak
        echo -e "${GREEN}Secret key generated and added to .env file.${NC}"
    else
        echo -e "${RED}Error: .env.example file not found.${NC}"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate || { echo -e "${RED}Failed to activate virtual environment.${NC}"; exit 1; }

# Install dependencies if not skipped
if [ "$SKIP_DEPS" = false ]; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -r requirements.txt || { echo -e "${RED}Failed to install dependencies.${NC}"; exit 1; }
fi

# Database setup if not skipped
if [ "$SKIP_DB" = false ]; then
    # Check if database exists and create it if needed
    source .env
    DB_NAME=$(echo $DATABASE_URL | sed -E 's/.*\/([^?]*).*/\1/')
    DB_EXISTS=$(psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
    
    if [ -z "$DB_EXISTS" ]; then
        echo -e "${BLUE}Database $DB_NAME does not exist. Creating...${NC}"
        psql -U postgres -c "CREATE DATABASE $DB_NAME;" || { echo -e "${RED}Failed to create database.${NC}"; exit 1; }
        echo -e "${GREEN}Database created.${NC}"
    fi
    
    # Run database migrations
    echo -e "${BLUE}Running database migrations...${NC}"
    if [ "$FORCE_DB_RECREATE" = true ]; then
        echo -e "${YELLOW}Warning: Forcing database recreation. All data will be lost.${NC}"
        python setup_db.py --force || { echo -e "${RED}Failed to set up database.${NC}"; exit 1; }
    else
        python setup_db.py || { echo -e "${RED}Failed to set up database.${NC}"; exit 1; }
    fi
    echo -e "${GREEN}Database setup completed.${NC}"
    
    # Initialize database with seed data if requested
    if [ "$FORCE_DB_INIT" = true ]; then
        echo -e "${BLUE}Initializing database with seed data...${NC}"
        python init_db.py || { echo -e "${RED}Failed to initialize database.${NC}"; exit 1; }
        echo -e "${GREEN}Database initialized with seed data.${NC}"
    fi
fi

# Check if the port is already in use
if nc -z localhost $PORT 2>/dev/null; then
    echo -e "${YELLOW}Warning: Port $PORT is already in use.${NC}"
    
    # Find an available port
    for (( p=$PORT+1; p<$PORT+100; p++ )); do
        if ! nc -z localhost $p 2>/dev/null; then
            echo -e "${BLUE}Using available port: $p${NC}"
            PORT=$p
            break
        fi
    done
fi

# Build the command
CMD="python run.py --host $HOST --port $PORT"

if [ "$RELOAD" = true ]; then
    CMD="$CMD --reload"
fi

if [ "$DEBUG" = true ]; then
    CMD="$CMD --debug"
fi

if [ "$WORKERS" -gt 1 ]; then
    CMD="$CMD --workers $WORKERS"
fi

# Start the application
echo -e "${BLUE}Starting the application...${NC}"
echo -e "${GREEN}The API will be available at http://$HOST:$PORT${NC}"
echo -e "${GREEN}API documentation will be available at http://$HOST:$PORT/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the application.${NC}"

# Execute the command
eval $CMD
