#!/bin/bash
# Script to deploy CORS fix to Render

echo "Deploying CORS fix to Render..."

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed or not in PATH"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Add changes
git add app/core/config.py
git status

echo ""
echo "The following changes will be committed and pushed:"
git diff --cached

echo ""
read -p "Do you want to continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Commit changes
git commit -m "Fix: Update CORS configuration to allow Netlify domain"

# Push changes
echo "Pushing changes to remote repository..."
git push origin $CURRENT_BRANCH

echo ""
echo "Changes pushed successfully!"
echo ""
echo "IMPORTANT: You still need to update the CORS_ORIGINS environment variable in Render:"
echo "1. Log in to your Render dashboard"
echo "2. Navigate to your 'doztra-research' service"
echo "3. Go to the 'Environment' tab"
echo "4. Find the CORS_ORIGINS variable or add it if it doesn't exist"
echo "5. Update its value to: [\"http://localhost:3000\", \"http://localhost:8000\", \"https://doztra.ai\", \"https://doztra.netlify.app\", \"https://www.doztra.netlify.app\"]"
echo "6. Click 'Save Changes' and wait for the service to redeploy"

echo ""
echo "Done!"
