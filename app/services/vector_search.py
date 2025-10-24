"""
Milvus Vector Search Service
Advanced semantic search and RAG capabilities
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
from datetime import datetime

# Milvus client
try:
    from pymilvus import (
        connections, Collection, CollectionSchema, FieldSchema, DataType,
        utility, Index
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

# Embedding models
try:
    from sentence_transformers import SentenceTransformer
    import openai
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

logger = logging.getLogger(__name__)

class MilvusVectorService:
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = int(os.getenv("MILVUS_PORT", "19530"))
        self.user = os.getenv("MILVUS_USER")
        self.password = os.getenv("MILVUS_PASSWORD")
        self.use_secure = os.getenv("MILVUS_USE_SECURE", "false").lower() == "true"
        self.collection_name = "knowledge_base_vectors"
        self.dimension = 768  # Default for sentence-transformers
        self.connected = False
        
        # Initialize embedding model
        self.embedding_model = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if EMBEDDINGS_AVAILABLE:
            try:
                # Try to load sentence transformer model
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.dimension = 384  # Dimension for all-MiniLM-L6-v2
                logger.info("Loaded sentence-transformers model")
            except Exception as e:
                logger.warning(f"Failed to load sentence-transformers: {e}")
                if self.openai_api_key:
                    openai.api_key = self.openai_api_key
                    self.dimension = 1536  # OpenAI ada-002 dimension
                    logger.info("Using OpenAI embeddings")
    
    async def connect(self) -> bool:
        """Connect to Milvus server (local or Zilliz Cloud)"""
        if not MILVUS_AVAILABLE:
            logger.error("Milvus client not available. Install pymilvus.")
            return False
        
        try:
            # Prepare connection parameters
            connection_params = {
                "alias": "default",
                "host": self.host,
                "port": self.port
            }
            
            # Add authentication for Zilliz Cloud
            if self.user and self.password:
                connection_params["user"] = self.user
                connection_params["password"] = self.password
            
            # Add secure connection for Zilliz Cloud
            if self.use_secure:
                connection_params["secure"] = True
            
            connections.connect(**connection_params)
            self.connected = True
            
            connection_type = "Zilliz Cloud" if self.use_secure else "Local Milvus"
            logger.info(f"Connected to {connection_type} at {self.host}:{self.port}")
            
            # Create collection if it doesn't exist
            await self._create_collection()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    async def _create_collection(self):
        """Create the knowledge base collection"""
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists")
            return
        
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="content_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10000),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="created_at", dtype=DataType.INT64)
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Knowledge base vector embeddings"
        )
        
        # Create collection
        collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        # Create index for vector field
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        logger.info(f"Created collection {self.collection_name}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        if not EMBEDDINGS_AVAILABLE:
            raise Exception("Embedding models not available")
        
        if self.embedding_model:
            # Use sentence transformers
            embeddings = self.embedding_model.encode(texts)
            return embeddings.tolist()
        
        elif self.openai_api_key:
            # Use OpenAI embeddings
            embeddings = []
            for text in texts:
                response = await openai.Embedding.acreate(
                    model="text-embedding-ada-002",
                    input=text
                )
                embeddings.append(response['data'][0]['embedding'])
            return embeddings
        
        else:
            raise Exception("No embedding model available")
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    async def add_content(
        self,
        content_id: str,
        user_id: str,
        content_type: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add content to vector database"""
        if not self.connected:
            await self.connect()
        
        try:
            # Chunk the content
            chunks = self.chunk_text(content)
            if not chunks:
                return False
            
            # Generate embeddings
            embeddings = await self.generate_embeddings(chunks)
            
            # Prepare data for insertion
            data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                data.append({
                    "content_id": content_id,
                    "user_id": user_id,
                    "content_type": content_type,
                    "title": title,
                    "content": chunk,
                    "chunk_index": i,
                    "embedding": embedding,
                    "metadata": metadata or {},
                    "created_at": int(datetime.now().timestamp())
                })
            
            # Insert into collection
            collection = Collection(self.collection_name)
            collection.insert(data)
            collection.flush()
            
            logger.info(f"Added {len(chunks)} chunks for content {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add content to vector DB: {e}")
            return False
    
    async def search_similar(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        content_type: Optional[str] = None,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar content"""
        if not self.connected:
            await self.connect()
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embeddings([query])
            
            # Prepare search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Build filter expression
            filter_expr = f'user_id == "{user_id}"'
            if content_type:
                filter_expr += f' && content_type == "{content_type}"'
            
            # Search
            collection = Collection(self.collection_name)
            collection.load()
            
            results = collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=filter_expr,
                output_fields=["content_id", "title", "content", "content_type", "metadata", "chunk_index"]
            )
            
            # Process results
            search_results = []
            for hits in results:
                for hit in hits:
                    if hit.score >= score_threshold:
                        search_results.append({
                            "content_id": hit.entity.get("content_id"),
                            "title": hit.entity.get("title"),
                            "content": hit.entity.get("content"),
                            "content_type": hit.entity.get("content_type"),
                            "chunk_index": hit.entity.get("chunk_index"),
                            "similarity_score": hit.score,
                            "metadata": hit.entity.get("metadata", {})
                        })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    async def delete_content(self, content_id: str, user_id: str) -> bool:
        """Delete content from vector database"""
        if not self.connected:
            await self.connect()
        
        try:
            collection = Collection(self.collection_name)
            
            # Delete by content_id and user_id
            expr = f'content_id == "{content_id}" && user_id == "{user_id}"'
            collection.delete(expr)
            collection.flush()
            
            logger.info(f"Deleted content {content_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete content from vector DB: {e}")
            return False
    
    async def get_content_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's content in vector DB"""
        if not self.connected:
            await self.connect()
        
        try:
            collection = Collection(self.collection_name)
            collection.load()
            
            # Count total chunks
            expr = f'user_id == "{user_id}"'
            total_chunks = collection.query(
                expr=expr,
                output_fields=["count(*)"]
            )
            
            # Count by content type
            content_types = collection.query(
                expr=expr,
                output_fields=["content_type"],
                limit=1000  # Adjust as needed
            )
            
            type_counts = {}
            for item in content_types:
                content_type = item.get("content_type", "unknown")
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
            
            return {
                "total_chunks": len(content_types),
                "content_types": type_counts,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to get content stats: {e}")
            return {"error": str(e)}
    
    async def hybrid_search(
        self,
        query: str,
        user_id: str,
        keywords: List[str] = None,
        content_types: List[str] = None,
        date_range: Tuple[datetime, datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Advanced hybrid search with multiple filters"""
        if not self.connected:
            await self.connect()
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embeddings([query])
            
            # Build complex filter expression
            filter_parts = [f'user_id == "{user_id}"']
            
            if content_types:
                type_filter = " || ".join([f'content_type == "{ct}"' for ct in content_types])
                filter_parts.append(f"({type_filter})")
            
            if date_range:
                start_ts = int(date_range[0].timestamp())
                end_ts = int(date_range[1].timestamp())
                filter_parts.append(f"created_at >= {start_ts} && created_at <= {end_ts}")
            
            filter_expr = " && ".join(filter_parts)
            
            # Search with filters
            collection = Collection(self.collection_name)
            collection.load()
            
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=limit * 2,  # Get more results for keyword filtering
                expr=filter_expr,
                output_fields=["content_id", "title", "content", "content_type", "metadata", "chunk_index"]
            )
            
            # Post-process with keyword filtering
            search_results = []
            for hits in results:
                for hit in hits:
                    content_text = hit.entity.get("content", "").lower()
                    title_text = hit.entity.get("title", "").lower()
                    
                    # Keyword filtering
                    if keywords:
                        keyword_match = any(
                            keyword.lower() in content_text or keyword.lower() in title_text
                            for keyword in keywords
                        )
                        if not keyword_match:
                            continue
                    
                    search_results.append({
                        "content_id": hit.entity.get("content_id"),
                        "title": hit.entity.get("title"),
                        "content": hit.entity.get("content"),
                        "content_type": hit.entity.get("content_type"),
                        "chunk_index": hit.entity.get("chunk_index"),
                        "similarity_score": hit.score,
                        "metadata": hit.entity.get("metadata", {}),
                        "keyword_matches": keywords if keywords else []
                    })
                    
                    if len(search_results) >= limit:
                        break
            
            return search_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            return []

# Global service instance
vector_service = MilvusVectorService()
