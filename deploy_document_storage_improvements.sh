#!/bin/bash

# Script to deploy document storage and processing improvements
# This script will:
# 1. Apply database migrations
# 2. Migrate existing documents to the new structure
# 3. Update environment variables
# 4. Restart the application

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DOCUMENT STORAGE AND PROCESSING IMPROVEMENTS DEPLOYMENT ===${NC}"

# Check if running in production environment
if [ "$ENVIRONMENT" != "production" ]; then
    echo -e "${YELLOW}Not running in production environment. This script is intended for production deployment.${NC}"
    echo -e "${YELLOW}If you want to continue anyway, press Enter. Otherwise, press Ctrl+C to abort.${NC}"
    read -p ""
fi

# Step 1: Apply database migrations
echo -e "\n${YELLOW}1. Applying database migrations...${NC}"
python -m alembic upgrade head

if [ $? -ne 0 ]; then
    echo -e "${RED}Database migration failed. Aborting deployment.${NC}"
    exit 1
fi

echo -e "${GREEN}Database migrations applied successfully.${NC}"

# Step 2: Migrate existing documents
echo -e "\n${YELLOW}2. Migrating existing documents to new structure...${NC}"
python migrate_existing_documents.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Document migration failed. Check the logs for details.${NC}"
    echo -e "${YELLOW}Do you want to continue with the deployment? (y/n)${NC}"
    read -p "" continue_deployment
    
    if [ "$continue_deployment" != "y" ]; then
        echo -e "${RED}Aborting deployment.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Document migration completed successfully.${NC}"
fi

# Step 3: Update environment variables
echo -e "\n${YELLOW}3. Updating environment variables...${NC}"

# Check if .env file exists
if [ -f .env ]; then
    # Add new environment variables if they don't exist
    if ! grep -q "UPLOAD_DIR" .env; then
        echo "UPLOAD_DIR=./uploads" >> .env
    fi
    
    if ! grep -q "DOCUMENT_CHUNKS_DIR" .env; then
        echo "DOCUMENT_CHUNKS_DIR=./document_chunks" >> .env
    fi
    
    if ! grep -q "MAX_CONCURRENT_PROCESSING" .env; then
        echo "MAX_CONCURRENT_PROCESSING=3" >> .env
    fi
    
    # Storage configuration
    echo -e "${BLUE}Configuring storage backend...${NC}"
    echo -e "${YELLOW}Which storage backend do you want to use? (local/s3/gcs)${NC}"
    read -p "" storage_backend
    
    if [ "$storage_backend" = "gcs" ]; then
        # Configure GCS
        echo -e "${BLUE}Configuring Google Cloud Storage...${NC}"
        
        # Update environment variables
        if ! grep -q "USE_GCS_STORAGE" .env; then
            echo "USE_GCS_STORAGE=true" >> .env
        else
            sed -i '' 's/USE_GCS_STORAGE=.*/USE_GCS_STORAGE=true/' .env
        fi
        
        if ! grep -q "USE_S3_STORAGE" .env; then
            echo "USE_S3_STORAGE=false" >> .env
        else
            sed -i '' 's/USE_S3_STORAGE=.*/USE_S3_STORAGE=false/' .env
        fi
        
        # Ask for GCS bucket name
        echo -e "${YELLOW}Enter your GCS bucket name:${NC}"
        read -p "" gcs_bucket_name
        
        if ! grep -q "GCS_BUCKET_NAME" .env; then
            echo "GCS_BUCKET_NAME=$gcs_bucket_name" >> .env
        else
            sed -i '' "s/GCS_BUCKET_NAME=.*/GCS_BUCKET_NAME=$gcs_bucket_name/" .env
        fi
        
        # Ask for service account key path
        echo -e "${YELLOW}Enter the path to your Google service account key file:${NC}"
        read -p "" gcs_key_path
        
        if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS" .env; then
            echo "GOOGLE_APPLICATION_CREDENTIALS=$gcs_key_path" >> .env
        else
            sed -i '' "s|GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$gcs_key_path|" .env
        fi
        
        echo -e "${GREEN}GCS configuration updated successfully.${NC}"
        
    elif [ "$storage_backend" = "s3" ]; then
        # Configure S3
        echo -e "${BLUE}Configuring AWS S3...${NC}"
        
        # Update environment variables
        if ! grep -q "USE_S3_STORAGE" .env; then
            echo "USE_S3_STORAGE=true" >> .env
        else
            sed -i '' 's/USE_S3_STORAGE=.*/USE_S3_STORAGE=true/' .env
        fi
        
        if ! grep -q "USE_GCS_STORAGE" .env; then
            echo "USE_GCS_STORAGE=false" >> .env
        else
            sed -i '' 's/USE_GCS_STORAGE=.*/USE_GCS_STORAGE=false/' .env
        fi
        
        # Ask for AWS credentials
        echo -e "${YELLOW}Enter your AWS access key ID:${NC}"
        read -p "" aws_access_key
        
        echo -e "${YELLOW}Enter your AWS secret access key:${NC}"
        read -p "" aws_secret_key
        
        echo -e "${YELLOW}Enter your AWS region:${NC}"
        read -p "" aws_region
        
        echo -e "${YELLOW}Enter your S3 bucket name:${NC}"
        read -p "" s3_bucket_name
        
        # Update environment variables
        if ! grep -q "AWS_ACCESS_KEY_ID" .env; then
            echo "AWS_ACCESS_KEY_ID=$aws_access_key" >> .env
        else
            sed -i '' "s/AWS_ACCESS_KEY_ID=.*/AWS_ACCESS_KEY_ID=$aws_access_key/" .env
        fi
        
        if ! grep -q "AWS_SECRET_ACCESS_KEY" .env; then
            echo "AWS_SECRET_ACCESS_KEY=$aws_secret_key" >> .env
        else
            sed -i '' "s/AWS_SECRET_ACCESS_KEY=.*/AWS_SECRET_ACCESS_KEY=$aws_secret_key/" .env
        fi
        
        if ! grep -q "AWS_REGION" .env; then
            echo "AWS_REGION=$aws_region" >> .env
        else
            sed -i '' "s/AWS_REGION=.*/AWS_REGION=$aws_region/" .env
        fi
        
        if ! grep -q "AWS_BUCKET_NAME" .env; then
            echo "AWS_BUCKET_NAME=$s3_bucket_name" >> .env
        else
            sed -i '' "s/AWS_BUCKET_NAME=.*/AWS_BUCKET_NAME=$s3_bucket_name/" .env
        fi
        
        echo -e "${GREEN}S3 configuration updated successfully.${NC}"
        
    else
        # Configure local storage
        echo -e "${BLUE}Configuring local storage...${NC}"
        
        if ! grep -q "USE_S3_STORAGE" .env; then
            echo "USE_S3_STORAGE=false" >> .env
        else
            sed -i '' 's/USE_S3_STORAGE=.*/USE_S3_STORAGE=false/' .env
        fi
        
        if ! grep -q "USE_GCS_STORAGE" .env; then
            echo "USE_GCS_STORAGE=false" >> .env
        else
            sed -i '' 's/USE_GCS_STORAGE=.*/USE_GCS_STORAGE=false/' .env
        fi
        
        echo -e "${GREEN}Local storage configuration updated successfully.${NC}"
    fi
    
    # Add processing optimization variables
    if ! grep -q "PARALLEL_EMBEDDING_GENERATION" .env; then
        echo "PARALLEL_EMBEDDING_GENERATION=true" >> .env
    fi
    
    if ! grep -q "MAX_PARALLEL_EMBEDDINGS" .env; then
        echo "MAX_PARALLEL_EMBEDDINGS=5" >> .env
    fi
    
    if ! grep -q "OPTIMIZE_CHUNK_SIZE" .env; then
        echo "OPTIMIZE_CHUNK_SIZE=true" >> .env
    fi
    
    echo -e "${GREEN}Environment variables updated successfully.${NC}"
else
    echo -e "${RED}.env file not found. Please create it manually with the required variables.${NC}"
    echo -e "${YELLOW}Do you want to continue with the deployment? (y/n)${NC}"
    read -p "" continue_deployment
    
    if [ "$continue_deployment" != "y" ]; then
        echo -e "${RED}Aborting deployment.${NC}"
        exit 1
    fi
fi

# Step 4: Restart the application
echo -e "\n${YELLOW}4. Restarting the application...${NC}"

# Check if we're running on Render
if [ -n "$RENDER" ]; then
    echo -e "${BLUE}Running on Render. The application will be restarted automatically.${NC}"
else
    # Try to restart using systemd
    if command -v systemctl &> /dev/null; then
        echo -e "${BLUE}Restarting using systemd...${NC}"
        sudo systemctl restart doztra-backend
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to restart using systemd. Please restart the application manually.${NC}"
        else
            echo -e "${GREEN}Application restarted successfully.${NC}"
        fi
    else
        # Try to restart using the start script
        if [ -f "./start.sh" ]; then
            echo -e "${BLUE}Restarting using start.sh...${NC}"
            ./start.sh
            
            if [ $? -ne 0 ]; then
                echo -e "${RED}Failed to restart using start.sh. Please restart the application manually.${NC}"
            else
                echo -e "${GREEN}Application restarted successfully.${NC}"
            fi
        else
            echo -e "${RED}Could not determine how to restart the application. Please restart it manually.${NC}"
        fi
    fi
fi

echo -e "\n${YELLOW}=== DEPLOYMENT SUMMARY ===${NC}"
echo -e "${GREEN}✅ Database migrations applied${NC}"
echo -e "${GREEN}✅ Document migration completed${NC}"
echo -e "${GREEN}✅ Environment variables updated${NC}"
echo -e "${GREEN}✅ Application restart initiated${NC}"

echo -e "\n${YELLOW}=== NEXT STEPS ===${NC}"
echo -e "1. Verify that the application is running correctly"
echo -e "2. Test document upload and processing functionality"
echo -e "3. Monitor logs for any errors"
echo -e "4. Update frontend to use the new API endpoints at /api/v2/documents"

echo -e "\n${BLUE}For any issues, please check the logs or contact the development team.${NC}"
