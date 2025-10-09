#!/bin/bash
# Development setup script for Doztra Auth Service

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   Doztra Auth Service Dev Setup     ${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    echo -e "${RED}Error: Python 3.8 or higher is required.${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}Warning: PostgreSQL is not installed or not in PATH.${NC}"
    echo "Please install PostgreSQL 12 or higher."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Docker is installed (optional)
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Warning: Docker is not installed.${NC}"
    echo "Docker is optional but recommended for containerized development."
    echo "You can install it later if needed."
fi

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv venv || { echo -e "${RED}Failed to create virtual environment.${NC}"; exit 1; }
echo -e "${GREEN}Virtual environment created.${NC}"

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate || { echo -e "${RED}Failed to activate virtual environment.${NC}"; exit 1; }

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip || { echo -e "${RED}Failed to upgrade pip.${NC}"; exit 1; }
pip install -r requirements.txt || { echo -e "${RED}Failed to install dependencies.${NC}"; exit 1; }

# Install development dependencies
echo -e "${BLUE}Installing development dependencies...${NC}"
pip install black flake8 mypy pytest pytest-cov isort || { echo -e "${RED}Failed to install development dependencies.${NC}"; exit 1; }

# Create .env file
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file from example.${NC}"
        echo -e "${YELLOW}Please edit .env file with your configuration.${NC}"
    else
        echo -e "${RED}Error: .env.example file not found.${NC}"
        exit 1
    fi
fi

# Create PostgreSQL database
echo -e "${BLUE}Setting up PostgreSQL database...${NC}"
read -p "Do you want to create a new PostgreSQL database for development? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter database name (default: doztra_auth): " DB_NAME
    DB_NAME=${DB_NAME:-doztra_auth}
    
    read -p "Enter PostgreSQL username (default: postgres): " DB_USER
    DB_USER=${DB_USER:-postgres}
    
    read -p "Enter PostgreSQL password (default: postgres): " DB_PASSWORD
    DB_PASSWORD=${DB_PASSWORD:-postgres}
    
    read -p "Enter PostgreSQL host (default: localhost): " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
    
    read -p "Enter PostgreSQL port (default: 5432): " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    
    # Update .env file with database configuration
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME|g" .env
    
    # Try to create the database
    echo -e "${BLUE}Creating database $DB_NAME...${NC}"
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" || {
        echo -e "${YELLOW}Warning: Failed to create database.${NC}"
        echo "You may need to create it manually or check your PostgreSQL configuration."
    }
fi

# Generate a random secret key
echo -e "${BLUE}Generating a random secret key...${NC}"
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
sed -i.bak "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env

# Run database migrations
echo -e "${BLUE}Running database migrations...${NC}"
read -p "Do you want to run database migrations? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    alembic upgrade head || {
        echo -e "${YELLOW}Warning: Database migration failed.${NC}"
        echo "You may need to create the database manually or check your PostgreSQL configuration."
    }
fi

# Initialize database with seed data
echo -e "${BLUE}Initializing database with seed data...${NC}"
read -p "Do you want to initialize the database with seed data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python init_db.py || {
        echo -e "${YELLOW}Warning: Failed to initialize database with seed data.${NC}"
        echo "You may need to check your database configuration."
    }
fi

# Setup pre-commit hooks (optional)
echo -e "${BLUE}Setting up pre-commit hooks...${NC}"
read -p "Do you want to set up pre-commit hooks for code quality? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install pre-commit || { echo -e "${RED}Failed to install pre-commit.${NC}"; exit 1; }
    
    # Create pre-commit configuration file
    cat > .pre-commit-config.yaml << EOF
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-docstrings]

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
        args: ["--profile", "black"]

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black
EOF
    
    pre-commit install || { echo -e "${RED}Failed to install pre-commit hooks.${NC}"; exit 1; }
    echo -e "${GREEN}Pre-commit hooks installed.${NC}"
fi

# Setup complete
echo -e "${GREEN}Development setup complete!${NC}"
echo -e "${BLUE}To start the application:${NC}"
echo -e "  1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Run the application: ${YELLOW}python run.py --reload${NC}"
echo -e "${BLUE}Or use the start script:${NC}"
echo -e "  ${YELLOW}./start.sh${NC}"
echo -e "${BLUE}Or use make:${NC}"
echo -e "  ${YELLOW}make run${NC}"
echo -e "${BLUE}The API will be available at:${NC} ${GREEN}http://localhost:8000${NC}"
echo -e "${BLUE}API documentation will be available at:${NC} ${GREEN}http://localhost:8000/docs${NC}"
