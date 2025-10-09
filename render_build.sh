#!/usr/bin/env bash
# Build script for Render.com

set -o errexit

# Update pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements-working.txt

# Install spaCy model
python -m spacy download en_core_web_sm

# Run database migrations
python -m alembic upgrade head

echo "Build completed successfully!"
