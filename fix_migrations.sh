#!/bin/bash
# Script to fix migration issues and run database setup

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting DATABASE_URL environment variable...${NC}"
export DATABASE_URL="postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"

echo -e "${YELLOW}Checking if DATABASE_URL is set correctly...${NC}"
echo $DATABASE_URL

echo -e "${YELLOW}Fixing migration file...${NC}"
# Find all migration files
MIGRATION_FILES=$(find alembic/versions -name "*.py")

# Loop through each migration file and fix the raw SQL execution
for file in $MIGRATION_FILES; do
    echo -e "${YELLOW}Processing $file...${NC}"
    
    # Check if the file contains raw SQL executions without text()
    if grep -q "connection.execute(" "$file" && ! grep -q "from sqlalchemy import text" "$file"; then
        echo -e "${YELLOW}Adding import for text() in $file${NC}"
        # Add import statement if not present
        sed -i '1s/^/from sqlalchemy import text\n/' "$file"
    fi
    
    # Replace raw SQL executions with text() wrapped versions
    sed -i 's/connection.execute(\s*"""\(.*\)"""\s*)/connection.execute(text("\1"))/g' "$file"
    sed -i 's/connection.execute(\s*"\(.*\)"\s*)/connection.execute(text("\1"))/g' "$file"
    sed -i "s/connection.execute(\s*'\(.*\)'\s*)/connection.execute(text('\1'))/g" "$file"
    
    echo -e "${GREEN}Fixed $file${NC}"
done

echo -e "${YELLOW}Running database migrations...${NC}"
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Migrations completed successfully!${NC}"
    
    echo -e "${YELLOW}Setting up admin user...${NC}"
    python setup_render_db.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Admin user setup completed successfully!${NC}"
        echo -e "${GREEN}You can now log in with:${NC}"
        echo -e "Email: admin@doztra.ai"
        echo -e "Password: Admin123!"
    else
        echo -e "${RED}Admin user setup failed.${NC}"
    fi
else
    echo -e "${RED}Migrations failed. Creating a new migration from scratch...${NC}"
    
    echo -e "${YELLOW}Creating a new migration...${NC}"
    python -m alembic revision --autogenerate -m "recreate_schema"
    
    echo -e "${YELLOW}Running the new migration...${NC}"
    python -m alembic upgrade head
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}New migration completed successfully!${NC}"
        
        echo -e "${YELLOW}Setting up admin user...${NC}"
        python setup_render_db.py
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Admin user setup completed successfully!${NC}"
            echo -e "${GREEN}You can now log in with:${NC}"
            echo -e "Email: admin@doztra.ai"
            echo -e "Password: Admin123!"
        else
            echo -e "${RED}Admin user setup failed.${NC}"
        fi
    else
        echo -e "${RED}All migration attempts failed.${NC}"
    fi
fi

echo -e "${YELLOW}Checking database tables...${NC}"
psql "$DATABASE_URL" -c "\dt"
