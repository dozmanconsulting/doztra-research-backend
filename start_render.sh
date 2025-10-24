#!/bin/bash
# Render.com startup script for Knowledge Base API

echo "🚀 Starting Doztra Knowledge Base API on Render.com"
echo "=================================================="

# Set Python path
export PYTHONPATH="${PYTHONPATH}:."

# Skip database migrations - using existing manual setup
echo "📊 Skipping database migrations (using existing manual setup)..."

# Test critical services
echo "🧪 Testing critical services..."
python -c "
import os
import sys

# Test environment variables
required_vars = ['DATABASE_URL', 'SECRET_KEY']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f'❌ Missing environment variables: {missing_vars}')
    sys.exit(1)

print('✅ Environment variables configured')

# Test database connection
try:
    from sqlalchemy import create_engine
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)

# Test Zilliz Cloud connection (optional)
try:
    from pymilvus import connections
    host = os.getenv('MILVUS_HOST')
    if host and 'zillizcloud.com' in host:
        connections.connect(
            alias='test',
            host=host,
            port=int(os.getenv('MILVUS_PORT', 19530)),
            user=os.getenv('MILVUS_USER'),
            password=os.getenv('MILVUS_PASSWORD'),
            secure=True
        )
        print('✅ Zilliz Cloud connection successful')
        connections.disconnect('test')
    else:
        print('⚠️  Zilliz Cloud not configured (optional)')
except Exception as e:
    print(f'⚠️  Zilliz Cloud connection warning: {e}')
    print('Vector search will be disabled')

print('🎉 All critical services ready!')
"

# Start the application
echo "🌟 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
