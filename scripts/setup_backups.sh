#!/bin/bash
# Setup backup directory and cron job for Doztra Auth Service

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BACKUP_DIR="$HOME/doztra_backups"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_db.sh"
CRON_SCHEDULE="0 2 * * *"  # 2:00 AM every day

# Print usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --backup-dir DIR     Backup directory (default: $HOME/doztra_backups)"
    echo "  -s, --schedule CRON      Cron schedule (default: 0 2 * * *)"
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
        -s|--schedule)
            CRON_SCHEDULE="$2"
            shift
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

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}Error: Backup script not found at $BACKUP_SCRIPT.${NC}"
    exit 1
fi

# Make sure backup script is executable
chmod +x "$BACKUP_SCRIPT"

# Create backup directory
echo -e "${BLUE}Creating backup directory: $BACKUP_DIR${NC}"
mkdir -p "$BACKUP_DIR"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup directory created successfully.${NC}"
else
    echo -e "${RED}Error: Failed to create backup directory.${NC}"
    exit 1
fi

# Create cron job
echo -e "${BLUE}Setting up cron job to run backups at schedule: $CRON_SCHEDULE${NC}"

# Check if crontab is available
if ! command -v crontab &> /dev/null; then
    echo -e "${RED}Error: crontab command not found.${NC}"
    echo "Please make sure cron is installed on your system."
    exit 1
fi

# Create temporary file for crontab
TEMP_CRON=$(mktemp)

# Export current crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "" > "$TEMP_CRON"

# Check if backup job already exists
if grep -q "$BACKUP_SCRIPT" "$TEMP_CRON"; then
    echo -e "${YELLOW}Warning: Backup job already exists in crontab.${NC}"
    echo -e "${BLUE}Updating existing job...${NC}"
    
    # Remove existing job
    sed -i.bak "/$(basename "$BACKUP_SCRIPT")/d" "$TEMP_CRON"
fi

# Add new job
echo "$CRON_SCHEDULE $BACKUP_SCRIPT --backup-dir $BACKUP_DIR > $BACKUP_DIR/backup.log 2>&1" >> "$TEMP_CRON"

# Install new crontab
crontab "$TEMP_CRON"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Cron job installed successfully.${NC}"
else
    echo -e "${RED}Error: Failed to install cron job.${NC}"
    rm -f "$TEMP_CRON"
    exit 1
fi

# Clean up
rm -f "$TEMP_CRON"

echo -e "${GREEN}Backup setup completed.${NC}"
echo -e "${BLUE}Backups will run at: $CRON_SCHEDULE${NC}"
echo -e "${BLUE}Backup directory: $BACKUP_DIR${NC}"
echo -e "${BLUE}Backup script: $BACKUP_SCRIPT${NC}"
echo -e "${BLUE}To view your cron jobs, run: crontab -l${NC}"
