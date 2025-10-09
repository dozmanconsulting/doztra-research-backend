#!/bin/bash
# Database restore script for Doztra Auth Service

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BACKUP_DIR="./backups"
DB_NAME="doztra_auth"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_FILE=""
CREATE_DB=false

# Print usage
usage() {
    echo "Usage: $0 [options] [backup_file]"
    echo "Options:"
    echo "  -d, --backup-dir DIR     Backup directory (default: ./backups)"
    echo "  -n, --db-name NAME       Database name (default: doztra_auth)"
    echo "  -u, --db-user USER       Database user (default: postgres)"
    echo "  -p, --db-password PASS   Database password (default: postgres)"
    echo "  -h, --db-host HOST       Database host (default: localhost)"
    echo "  -P, --db-port PORT       Database port (default: 5432)"
    echo "  -c, --create-db          Create database if it doesn't exist"
    echo "  --help                   Show this help message"
    echo ""
    echo "If backup_file is not specified, the most recent backup will be used."
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -d|--backup-dir)
            BACKUP_DIR="$2"
            shift
            shift
            ;;
        -n|--db-name)
            DB_NAME="$2"
            shift
            shift
            ;;
        -u|--db-user)
            DB_USER="$2"
            shift
            shift
            ;;
        -p|--db-password)
            DB_PASSWORD="$2"
            shift
            shift
            ;;
        -h|--db-host)
            DB_HOST="$2"
            shift
            shift
            ;;
        -P|--db-port)
            DB_PORT="$2"
            shift
            shift
            ;;
        -c|--create-db)
            CREATE_DB=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            if [ -z "$BACKUP_FILE" ]; then
                BACKUP_FILE="$1"
                shift
            else
                echo "Unknown option: $1"
                usage
            fi
            ;;
    esac
done

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found.${NC}"
    echo "Please make sure PostgreSQL client tools are installed."
    exit 1
fi

# If no backup file is specified, use the most recent one
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${BLUE}No backup file specified. Looking for the most recent backup...${NC}"
    
    # Find the most recent backup file (both compressed and uncompressed)
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql*" -type f | sort -r | head -n 1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        echo -e "${RED}Error: No backup files found in $BACKUP_DIR.${NC}"
        exit 1
    fi
    
    BACKUP_FILE="$LATEST_BACKUP"
    echo -e "${BLUE}Using most recent backup: $BACKUP_FILE${NC}"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file $BACKUP_FILE not found.${NC}"
    exit 1
fi

# Set PGPASSWORD environment variable
export PGPASSWORD="$DB_PASSWORD"

# Create database if requested
if [ "$CREATE_DB" = true ]; then
    echo -e "${BLUE}Checking if database $DB_NAME exists...${NC}"
    DB_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
    
    if [ -z "$DB_EXISTS" ]; then
        echo -e "${BLUE}Database $DB_NAME does not exist. Creating...${NC}"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Database created successfully.${NC}"
        else
            echo -e "${RED}Error: Failed to create database.${NC}"
            exit 1
        fi
    else
        echo -e "${BLUE}Database $DB_NAME already exists.${NC}"
    fi
fi

# Ask for confirmation before restoring
echo -e "${YELLOW}Warning: This will overwrite the current database $DB_NAME.${NC}"
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Restore cancelled.${NC}"
    exit 0
fi

# Check if the backup file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo -e "${BLUE}Decompressing backup file...${NC}"
    TEMP_FILE=$(mktemp)
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to decompress backup file.${NC}"
        rm -f "$TEMP_FILE"
        exit 1
    fi
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Perform restore
echo -e "${BLUE}Starting restore of database $DB_NAME...${NC}"
echo -e "${BLUE}This may take a while...${NC}"

# Drop connections to the database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME' AND pid <> pg_backend_pid();" postgres

# Drop and recreate the database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;" postgres
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" postgres

# Restore the database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$RESTORE_FILE"

# Check if restore was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Restore completed successfully.${NC}"
else
    echo -e "${RED}Error: Restore failed.${NC}"
    
    # Clean up temporary file if it exists
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        rm -f "$TEMP_FILE"
    fi
    
    exit 1
fi

# Clean up temporary file if it exists
if [[ "$BACKUP_FILE" == *.gz ]]; then
    rm -f "$TEMP_FILE"
fi

# Unset PGPASSWORD
unset PGPASSWORD

echo -e "${GREEN}Restore process completed.${NC}"
echo -e "${BLUE}You may need to run database migrations to ensure schema consistency.${NC}"
echo -e "${BLUE}Run: alembic upgrade head${NC}"
