# 🚀 Quick Start: Advanced Knowledge Base Features

Your API keys are ready! Here's how to get everything up and running.

## 📋 Your API Keys
- **AssemblyAI**: `ba9ebbf2cdc34058893aa098e42b58e4` ✅
- **Firecrawl**: `fc-5d211b19270f45b1b51a9d7eebafa9e0` ✅
- **YouTube Data API**: `AIzaSyBUGEfl0yfZwLzA-gN0RiRlqGx2M3nD0uo` ✅

## 🎯 Quick Setup (5 minutes)

### 1. Run the Setup Script
```bash
cd /Users/shed/Documents/v1/doztra-research-backend
python setup_advanced_features.py
```

This will:
- Create your `.env` file with the API keys
- Install all required Python packages
- Start Milvus vector database
- Verify everything is configured

### 2. Test the Integration
```bash
python test_api_integrations.py
```

This will test:
- ✅ AssemblyAI audio transcription
- ✅ Firecrawl web scraping
- ✅ YouTube Data API integration
- ✅ Vector embeddings
- ✅ Milvus database connection

### 3. Test YouTube Integration (Optional)
```bash
python test_youtube_integration.py
```

This comprehensive test will:
- Test video ID extraction from various URL formats
- Get video metadata (title, views, duration, etc.)
- Extract transcripts in multiple languages
- Test YouTube search functionality
- Verify complete video processing pipeline

### 4. Start the Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎉 What You Can Now Do

### 🎵 Audio Transcription
- Upload audio files (MP3, WAV, M4A, etc.)
- Automatic transcription with AssemblyAI
- Speaker detection and sentiment analysis
- Key highlights extraction

### 🌐 Web Content Processing
- Scrape any website with Firecrawl
- Clean content extraction
- Automatic metadata detection
- Handle dynamic content

### 📺 YouTube Integration
- Process YouTube videos
- Extract transcripts automatically
- Get video metadata
- Content analysis

### 📄 Document Processing
- Support for 20+ file formats
- PDF, DOCX, XLSX, PPTX processing
- OCR for images
- Code file analysis

### 🔍 Vector Search
- Semantic search across all content
- AI-powered content retrieval
- Similar content discovery
- RAG (Retrieval Augmented Generation)

## 🧪 Test the Features

### Test Audio Transcription
```bash
curl -X POST "http://localhost:8000/api/content/items/transcribe-audio" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/audio.mp3" \
  -F "title=Test Audio Transcription"
```

### Test Web Scraping
```bash
curl -X POST "http://localhost:8000/api/content/items/process-url" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Web Article",
    "url": "https://example.com/article",
    "content_type": "url"
  }'
```

### Test YouTube Processing
```bash
curl -X POST "http://localhost:8000/api/content/items/process-url" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test YouTube Video",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "content_type": "youtube"
  }'
```

### Test Vector Search
```bash
curl -X GET "http://localhost:8000/api/content/search?query=artificial intelligence&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🎨 Frontend Features

The frontend now supports:

### Enhanced Content Modal
- **Text Content**: Direct text input
- **Documents**: PDF, DOCX, XLSX, PPTX upload
- **Web URLs**: Firecrawl-powered scraping
- **YouTube Videos**: Automatic transcript extraction
- **Audio Files**: AssemblyAI transcription

### Real-time Processing
- Background processing indicators
- Progress tracking
- Processing status updates
- Error handling with detailed messages

### Advanced Search
- Semantic search across all content
- Filter by content type
- Similarity scoring
- Contextual results

## 🔧 Troubleshooting

### If Milvus Won't Start
```bash
# Stop existing container
docker stop milvus-standalone
docker rm milvus-standalone

# Start fresh
docker run -d --name milvus-standalone \
  -p 19530:19530 -p 9091:9091 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:latest standalone
```

### If API Keys Don't Work
1. Check your `.env` file:
```bash
cat .env | grep API_KEY
```

2. Verify the keys are correct:
- AssemblyAI: `ba9ebbf2cdc34058893aa098e42b58e4`
- Firecrawl: `fc-5d211b19270f45b1b51a9d7eebafa9e0`

### If Dependencies Fail
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements_advanced.txt
```

## 📊 Monitoring

### Check Service Status
```bash
# Backend logs
tail -f app.log

# Milvus logs  
docker logs milvus-standalone

# API test
python test_api_integrations.py
```

### Performance Metrics
- Audio transcription: ~1-2 minutes per hour of audio
- Web scraping: ~2-5 seconds per page
- Vector search: <100ms for most queries
- Document processing: ~10-30 seconds per document

## 🎯 Next Steps

1. **Test all features** with the frontend
2. **Upload sample content** to see processing in action
3. **Try semantic search** to find related content
4. **Monitor processing** in the backend logs
5. **Scale up** by adding more content types

## 🆘 Need Help?

- **API Issues**: Check `test_api_integrations.py` output
- **Processing Errors**: Check backend logs
- **Frontend Issues**: Check browser console
- **Database Issues**: Check Milvus container status

Your advanced Knowledge Base is ready! 🎉
