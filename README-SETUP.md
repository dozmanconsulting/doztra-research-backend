# Doztra Auth Service Setup Guide

This guide provides instructions for setting up and running the Doztra Authentication Service with tested and working dependencies.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git

## Setup Instructions

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd doztra-backend-service-v1
   ```

2. **Set up the environment**:
   ```bash
   # Make the setup script executable
   chmod +x setup_working_deps.sh
   
   # Run the setup script
   ./setup_working_deps.sh
   ```

   This script will:
   - Create a virtual environment
   - Install all the required dependencies with tested versions
   - Install the spaCy language model

3. **Set up the environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Generate a secret key
   python -c 'import secrets; print(f"SECRET_KEY={secrets.token_urlsafe(32)}")' >> .env
   
   # Edit the .env file with your configuration
   nano .env
   ```

4. **Set up the database**:
   ```bash
   # Activate the virtual environment
   source venv/bin/activate
   
   # Run the database setup script
   python setup_db.py
   ```

## Running the Application

1. **Start the application**:
   ```bash
   # Activate the virtual environment (if not already activated)
   source venv/bin/activate
   
   # Run the application
   python run.py --reload
   ```

   Or use the start script:
   ```bash
   ./start.sh
   ```

2. **Access the API**:
   - The API will be available at http://localhost:8000
   - API documentation will be available at http://localhost:8000/docs

## Running Tests

To run the API tests:
```bash
# Activate the virtual environment
source venv/bin/activate

# Run the tests
python tests/api_tests.py --host localhost --port 8000
```

## Troubleshooting

### Port Already in Use
If the port is already in use, you can specify a different port:
```bash
python run.py --port 8001 --reload
```

### Database Connection Issues
- Make sure PostgreSQL is running
- Check the database connection string in the .env file
- Ensure the database exists and the user has the necessary permissions

### Dependencies Issues
If you encounter issues with dependencies, you can try reinstalling them:
```bash
source venv/bin/activate
pip install -r requirements-working.txt
```

## Notes on Dependencies

The `requirements-working.txt` file contains the specific versions of dependencies that have been tested and confirmed to work with this project. If you encounter any issues with the original `requirements.txt` file, please use the working version instead.

Key changes from the original requirements:
- Updated FastAPI to version 0.118.2
- Updated Pydantic to version 2.12.0
- Fixed bcrypt version to 4.0.1 to avoid password hashing issues
- Updated other dependencies to their latest compatible versions
