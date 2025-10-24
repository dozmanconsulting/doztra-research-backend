# 🚀 Deploying Knowledge Base to Render.com

Complete guide for deploying your advanced Knowledge Base system to Render.com with Zilliz Cloud (managed Milvus).

## 🎯 DEPLOYMENT ARCHITECTURE

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │  Zilliz Cloud   │
│   (Netlify)     │◄──►│   (Render.com)   │◄──►│   (Milvus)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   PostgreSQL     │
                       │   (Render.com)   │
                       └──────────────────┘
```

## 📋 PREREQUISITES

### 1. Render.com Account
- Sign up at https://render.com
- Connect your GitHub repository

### 2. Zilliz Cloud Account  
- Sign up at https://cloud.zilliz.com
- Create a free cluster (up to 1GB storage)

### 3. API Keys Ready
- ✅ AssemblyAI: `ba9ebbf2cdc34058893aa098e42b58e4`
- ✅ Firecrawl: `fc-5d211b19270f45b1b51a9d7eebafa9e0`
- ✅ YouTube: `AIzaSyBUGEfl0yfZwLzA-gN0RiRlqGx2M3nD0uo`

## 🗄️ STEP 1: Setup Zilliz Cloud (Milvus)

### 1.1 Create Zilliz Account
```bash
# Go to: https://cloud.zilliz.com/signup
# Use your email to create account
```

### 1.2 Create a Cluster
1. Click "Create Cluster"
2. Choose **"Starter"** plan (free tier)
3. Select region closest to Render (US East recommended)
4. Cluster name: `knowledge-base-vectors`
5. Click "Create Cluster"

### 1.3 Get Connection Details
After cluster creation, note down:
- **Endpoint**: `in01-xxx.zillizcloud.com`
- **Username**: Your Zilliz username
- **Password**: Generated password
- **Port**: `19530` (default)

### 1.4 Test Connection (Optional)
```python
# Test script
from pymilvus import connections

connections.connect(
    alias="default",
    host="your-endpoint.zillizcloud.com",
    port=19530,
    user="your_username", 
    password="your_password",
    secure=True
)
print("✅ Connected to Zilliz Cloud!")
```

## 🐘 STEP 2: Setup PostgreSQL on Render

### 2.1 Create PostgreSQL Database
1. Go to Render Dashboard
2. Click "New" → "PostgreSQL"
3. Database name: `doztra-knowledge-base`
4. Choose free tier or paid plan
5. Click "Create Database"

### 2.2 Get Database URL
After creation, copy the **External Database URL**:
```
postgresql://username:password@hostname:port/database
```

## 🚀 STEP 3: Deploy Backend to Render

### 3.1 Create Web Service
1. Go to Render Dashboard
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Choose the backend directory: `doztra-research-backend`

### 3.2 Configure Build Settings
```yaml
# Build Command
pip install -r requirements_advanced.txt

# Start Command  
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Environment
Python 3.11
```

### 3.3 Set Environment Variables
Add these in Render's Environment Variables section:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db  # From Step 2

# JWT Authentication
SECRET_KEY=your-super-secret-jwt-key-generate-new-one
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
ASSEMBLYAI_API_KEY=ba9ebbf2cdc34058893aa098e42b58e4
FIRECRAWL_API_KEY=fc-5d211b19270f45b1b51a9d7eebafa9e0
YOUTUBE_API_KEY=AIzaSyBUGEfl0yfZwLzA-gN0RiRlqGx2M3nD0uo

# Zilliz Cloud (Milvus)
MILVUS_HOST=your-endpoint.zillizcloud.com
MILVUS_PORT=19530
MILVUS_USER=your_zilliz_username
MILVUS_PASSWORD=your_zilliz_password
MILVUS_USE_SECURE=true

# Application Settings
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 3.4 Deploy
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Test the API endpoint: `https://your-app.onrender.com/docs`

## 🎨 STEP 4: Update Frontend Configuration

### 4.1 Update API Base URL
In your frontend `.env` file:
```bash
REACT_APP_API_URL=https://your-backend-app.onrender.com
```

### 4.2 Deploy Frontend to Netlify
```bash
# Build and deploy
npm run build
# Upload to Netlify or connect GitHub
```

## 🧪 STEP 5: Test the Deployment

### 5.1 Test API Health
```bash
curl https://your-app.onrender.com/health
```

### 5.2 Test Authentication
```bash
curl -X POST https://your-app.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'
```

### 5.3 Test Vector Database
```bash
curl -X GET https://your-app.onrender.com/api/content/search?query=test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5.4 Test Processing Services
```bash
# Test audio transcription
curl -X POST https://your-app.onrender.com/api/content/items/transcribe-audio \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test-audio.mp3"

# Test web scraping
curl -X POST https://your-app.onrender.com/api/content/items/process-url \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Article","url":"https://example.com","content_type":"url"}'
```

## 📊 STEP 6: Monitor and Scale

### 6.1 Monitor Performance
- Check Render logs for errors
- Monitor Zilliz Cloud usage
- Track API response times

### 6.2 Scale Resources
```bash
# Render scaling options:
# - Upgrade to paid plan for more CPU/RAM
# - Enable auto-scaling
# - Add Redis for caching

# Zilliz Cloud scaling:
# - Upgrade cluster size
# - Add more storage
# - Enable performance tier
```

## 🔧 TROUBLESHOOTING

### Common Issues

#### 1. Milvus Connection Fails
```bash
# Check environment variables
echo $MILVUS_HOST
echo $MILVUS_USER

# Test connection
python -c "
from pymilvus import connections
connections.connect('default', host='$MILVUS_HOST', port=19530, user='$MILVUS_USER', password='$MILVUS_PASSWORD', secure=True)
print('Connected!')
"
```

#### 2. API Keys Not Working
```bash
# Verify in Render environment variables
# Check API key formats
# Test individual services
```

#### 3. Database Connection Issues
```bash
# Check DATABASE_URL format
# Verify PostgreSQL is running
# Test connection string
```

#### 4. Build Failures
```bash
# Check requirements_advanced.txt
# Verify Python version (3.11+)
# Check build logs in Render
```

## 💰 COST ESTIMATION

### Free Tier (Development)
- **Render Web Service**: Free (with limitations)
- **Render PostgreSQL**: Free (1GB storage)
- **Zilliz Cloud**: Free (1GB vectors)
- **Total**: $0/month

### Production Tier
- **Render Web Service**: $7-25/month
- **Render PostgreSQL**: $7-20/month  
- **Zilliz Cloud**: $10-50/month
- **Total**: $24-95/month

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Zilliz Cloud cluster created
- [ ] PostgreSQL database created on Render
- [ ] All API keys ready
- [ ] Environment variables configured
- [ ] Code pushed to GitHub

### Deployment
- [ ] Backend deployed to Render
- [ ] Database migrations run
- [ ] API health check passes
- [ ] Vector database connected
- [ ] All processing services tested

### Post-Deployment
- [ ] Frontend updated with new API URL
- [ ] End-to-end testing completed
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Documentation updated

## 🎯 NEXT STEPS

1. **Deploy and Test**: Follow this guide step by step
2. **Monitor Performance**: Set up logging and alerts
3. **Scale as Needed**: Upgrade plans based on usage
4. **Optimize Costs**: Monitor usage and adjust resources
5. **Add Features**: Implement additional AI capabilities

Your Knowledge Base will be production-ready on Render with enterprise-grade vector search! 🎉

---

**Need Help?**
- Render Support: https://render.com/docs
- Zilliz Support: https://zilliz.com/support  
- Check logs in Render dashboard
- Test individual components first
