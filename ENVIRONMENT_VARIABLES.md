# Environment Variables Configuration

This document outlines all the environment variables required for the advanced Knowledge Base features.

## Core Application Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/doztra_db
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=doztra_db

# JWT Authentication
SECRET_KEY=your-super-secret-jwt-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
DEBUG=False
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
```

## Advanced Processing Services

### AssemblyAI (Audio Transcription)
```bash
# Required for audio transcription features
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
```

**How to get:**
1. Sign up at https://www.assemblyai.com/
2. Go to your dashboard
3. Copy your API key from the "API Keys" section

**Features enabled:**
- Audio file transcription
- Speaker diarization
- Sentiment analysis
- Auto-generated summaries
- Key phrase extraction

### Firecrawl (Web Scraping)
```bash
# Required for web content extraction
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

**How to get:**
1. Sign up at https://firecrawl.dev/
2. Get your API key from the dashboard
3. Choose a plan that fits your scraping needs

**Features enabled:**
- Advanced web scraping
- Content extraction from any website
- Automatic content cleaning
- Metadata extraction

### Milvus (Vector Database)
```bash
# Vector database configuration
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=your_milvus_user
MILVUS_PASSWORD=your_milvus_password
```

**Setup:**
1. Install Milvus using Docker:
```bash
docker run -d --name milvus-standalone \
  -p 19530:19530 -p 9091:9091 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:latest standalone
```

**Features enabled:**
- Semantic search across all content
- Vector similarity matching
- Advanced content retrieval
- RAG (Retrieval Augmented Generation)

### OpenAI (Embeddings - Alternative)
```bash
# Optional: Use OpenAI embeddings instead of sentence-transformers
OPENAI_API_KEY=your_openai_api_key_here
```

**How to get:**
1. Sign up at https://platform.openai.com/
2. Go to API Keys section
3. Create a new API key

**Note:** If not provided, the system will use sentence-transformers (free, local embeddings)

### YouTube Data API
```bash
# Required for YouTube video processing
YOUTUBE_API_KEY=your_youtube_api_key_here
```

**How to get:**
1. Go to Google Cloud Console
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Restrict the key to YouTube Data API

**Features enabled:**
- YouTube video metadata extraction
- Automatic transcript retrieval
- Video content analysis
- Channel video listing

## Optional Services

### Redis (Caching & Background Tasks)
```bash
# Optional: For caching and background job processing
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

### Monitoring & Logging
```bash
# Optional: Enhanced logging and monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_PORT=9090
```

### File Storage
```bash
# Optional: Cloud storage for uploaded files
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your-s3-bucket-name
AWS_REGION=us-east-1
```

## Development vs Production

### Development (.env.development)
```bash
DEBUG=True
ENVIRONMENT=development
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/doztra_dev
LOG_LEVEL=DEBUG

# Use free/local services for development
# ASSEMBLYAI_API_KEY=  # Optional for dev
# FIRECRAWL_API_KEY=   # Optional for dev
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### Production (.env.production)
```bash
DEBUG=False
ENVIRONMENT=production
DATABASE_URL=postgresql://prod_user:secure_pass@prod_host:5432/doztra_prod
LOG_LEVEL=INFO

# All API keys required for production
ASSEMBLYAI_API_KEY=your_production_assemblyai_key
FIRECRAWL_API_KEY=your_production_firecrawl_key
YOUTUBE_API_KEY=your_production_youtube_key
OPENAI_API_KEY=your_production_openai_key

# Production Milvus cluster
MILVUS_HOST=your_milvus_cluster_host
MILVUS_PORT=19530
MILVUS_USER=prod_user
MILVUS_PASSWORD=secure_password
```

## Security Best Practices

1. **Never commit .env files** to version control
2. **Use different API keys** for development and production
3. **Rotate API keys regularly**
4. **Use environment-specific configurations**
5. **Implement proper access controls** for production databases

## Service Costs (Approximate)

### AssemblyAI
- Free tier: 5 hours/month
- Pay-as-you-go: $0.37/hour of audio
- Pro plans available

### Firecrawl
- Free tier: 500 pages/month
- Starter: $29/month for 5,000 pages
- Growth: $99/month for 20,000 pages

### OpenAI Embeddings
- text-embedding-ada-002: $0.0001/1K tokens
- Approximately $0.01 per 10,000 words

### YouTube Data API
- Free quota: 10,000 units/day
- Additional quota: $0.05/1,000 units

### Milvus
- Self-hosted: Free (infrastructure costs only)
- Zilliz Cloud: Starting at $0.10/hour

## Fallback Behavior

The system is designed to gracefully handle missing API keys:

- **No AssemblyAI key:** Audio files won't be transcribed
- **No Firecrawl key:** Basic web scraping will be used
- **No YouTube key:** Only transcript extraction (no metadata)
- **No OpenAI key:** Local sentence-transformers will be used
- **No Milvus:** Vector search will be disabled

## Testing Configuration

For testing, create a `.env.test` file:

```bash
DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/doztra_test
SECRET_KEY=test-secret-key-not-for-production
DEBUG=True
ENVIRONMENT=test

# Mock API keys for testing
ASSEMBLYAI_API_KEY=test_key
FIRECRAWL_API_KEY=test_key
YOUTUBE_API_KEY=test_key
```

## Validation

The application will validate required environment variables on startup and provide clear error messages for missing configurations.
