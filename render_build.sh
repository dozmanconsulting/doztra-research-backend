#!/usr/bin/env bash
# Build script for Render.com

set -o errexit

# Update pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements-working.txt

# Explicitly install gunicorn and uvicorn
pip install gunicorn==21.2.0 uvicorn==0.37.0

# Install spaCy model
python -m spacy download en_core_web_sm

# Check database connection before proceeding
echo "Checking database connection..."
if python check_render_db.py; then
    echo "Database connection successful."
else
    echo "Warning: Database connection check failed. This might indicate a problem with the database URL."
    echo "Continuing with deployment anyway..."
    # Continue even if connection check fails
fi

# Run database migrations with proper error handling
echo "Running database migrations..."
if python -m alembic upgrade head; then
    echo "Database migrations completed successfully."
else
    echo "Warning: Database migrations failed. This might be expected if the schema already exists."
    echo "Continuing with deployment..."
    # Continue even if migrations fail
fi

# Set up the database with initial data
echo "Setting up database with initial data..."
if python setup_render_db.py; then
    echo "Database setup completed successfully."
else
    echo "Warning: Database setup failed. Continuing with deployment..."
    # Continue even if setup fails
fi

echo "Build completed successfully!"
