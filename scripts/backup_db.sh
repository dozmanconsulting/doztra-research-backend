#!/bin/bash
# Database backup script for Doztra Auth Service

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
RETENTION_DAYS=7
COMPRESS=true

# Print usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --backup-dir DIR     Backup directory (default: ./backups)"
    echo "  -n, --db-name NAME       Database name (default: doztra_auth)"
    echo "  -u, --db-user USER       Database user (default: postgres)"
    echo "  -p, --db-password PASS   Database password (default: postgres)"
    echo "  -h, --db-host HOST       Database host (default: localhost)"
    echo "  -P, --db-port PORT       Database port (default: 5432)"
    echo "  -r, --retention DAYS     Retention period in days (default: 7)"
    echo "  -c, --compress           Compress backup (default: true)"
    echo "  -nc, --no-compress       Don't compress backup"
    echo "  --help                   Show this help message"
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
        -r|--retention)
            RETENTION_DAYS="$2"
            shift
            shift
            ;;
        -c|--compress)
            COMPRESS=true
            shift
            ;;
        -nc|--no-compress)
            COMPRESS=false
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}Error: pg_dump command not found.${NC}"
    echo "Please make sure PostgreSQL client tools are installed."
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"

# Set PGPASSWORD environment variable
export PGPASSWORD="$DB_PASSWORD"

# Perform backup
echo -e "${BLUE}Starting backup of database $DB_NAME...${NC}"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F p > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup completed successfully: $BACKUP_FILE${NC}"
    
    # Compress backup if requested
    if [ "$COMPRESS" = true ]; then
        echo -e "${BLUE}Compressing backup...${NC}"
        gzip "$BACKUP_FILE"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Compression completed: ${BACKUP_FILE}.gz${NC}"
            BACKUP_FILE="${BACKUP_FILE}.gz"
        else
            echo -e "${YELLOW}Warning: Compression failed.${NC}"
        fi
    fi
    
    # Calculate backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${BLUE}Backup size: $BACKUP_SIZE${NC}"
    
    # Delete old backups
    echo -e "${BLUE}Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"
    find "$BACKUP_DIR" -name "${DB_NAME}_*.sql*" -type f -mtime +$RETENTION_DAYS -delete
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Cleanup completed.${NC}"
    else
        echo -e "${YELLOW}Warning: Cleanup failed.${NC}"
    fi
else
    echo -e "${RED}Error: Backup failed.${NC}"
    exit 1
fi

# Unset PGPASSWORD
unset PGPASSWORD

echo -e "${GREEN}Backup process completed.${NC}"
