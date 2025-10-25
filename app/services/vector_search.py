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

# Pinecone SDK availability (new v5 and legacy client)
PINECONE_V5_AVAILABLE = False
PINECONE_LEGACY_AVAILABLE = False
try:  # Preferred new SDK
    from pinecone import Pinecone as PineconeClient
    from pinecone import ServerlessSpec as PineconeServerlessSpec
    PINECONE_V5_AVAILABLE = True
except Exception:
    try:  # Legacy SDK
        import pinecone as pinecone_legacy
        PINECONE_LEGACY_AVAILABLE = True
    except Exception:
        pass

logger = logging.getLogger(__name__)

class MilvusVectorService:
    def __init__(self):
        # Fall back to defaults if env vars are unset or blank
        self.host = os.getenv("MILVUS_HOST") or "localhost"
        self.port = int(os.getenv("MILVUS_PORT") or "19530")
        self.user = os.getenv("MILVUS_USER")
        self.password = os.getenv("MILVUS_PASSWORD")
        self.use_secure = os.getenv("MILVUS_USE_SECURE", "false").lower() == "true"
        self.db_name = os.getenv("MILVUS_DB_NAME") or "default"
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
            # Prefer URI + token if provided (best for Zilliz Cloud Serverless)
            env_uri = os.getenv("MILVUS_URI")
            env_token = os.getenv("MILVUS_TOKEN")
            if env_uri:
                connections.connect(alias="default", uri=env_uri, token=env_token, db_name=self.db_name)
            else:
                # Build URI automatically when secure=true (Zilliz)
                if self.use_secure:
                    uri = f"https://{self.host}:{self.port}"
                    token = env_token or (f"{self.user}:{self.password}" if self.user and self.password else None)
                    connections.connect(alias="default", uri=uri, token=token, db_name=self.db_name)
                else:
                    # Local Milvus host/port
                    connections.connect(alias="default", host=self.host, port=self.port, db_name=self.db_name)
            self.connected = True
            
            connection_type = "Zilliz Cloud" if self.use_secure else "Local Milvus"
            logger.info(f"Connected to {connection_type} at {self.host}:{self.port}")
            
            # Create collection if it doesn't exist
            await self._create_collection()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False


class PineconeVectorService:
    """Pinecone vector backend with optional serverless index creation.
    Requires env:
      - PINECONE_API_KEY
      - PINECONE_INDEX (e.g., knowledge-base)
      - PINECONE_CLOUD (aws|gcp) and PINECONE_REGION (e.g., us-east-1) for new SDK serverless
      - or PINECONE_ENVIRONMENT for legacy SDK
    """
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX", "knowledge-base")
        self.cloud = os.getenv("PINECONE_CLOUD", "aws")
        self.region = os.getenv("PINECONE_REGION", "us-east-1")
        self.dimension = 384  # default to MiniLM; will update on model load
        self.index = None
        self.connected = False
        self.collection_name = "knowledge_base_vectors"

        # Embeddings
        self.embedding_model = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.dimension = 384
                logger.info("Loaded sentence-transformers model for Pinecone")
            except Exception as e:
                logger.warning(f"Failed to load sentence-transformers: {e}")
        # Fallback to OpenAI client if sentence-transformers not available/loaded
        if self.openai_api_key and self.embedding_model is None:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                self.dimension = 1536  # text-embedding-3-small
                logger.info("Using OpenAI embeddings for Pinecone (text-embedding-3-small)")
            except Exception as oe:
                logger.error(f"Failed to init OpenAI client: {oe}")

    async def connect(self) -> bool:
        if not self.api_key:
            logger.error("Pinecone API key not set")
            return False
        try:
            if PINECONE_V5_AVAILABLE:
                pc = PineconeClient(api_key=self.api_key)
                existing = [idx.name for idx in pc.list_indexes()]
                if self.index_name not in existing:
                    pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine",
                        spec=PineconeServerlessSpec(cloud=self.cloud, region=self.region),
                    )
                self.index = pc.Index(self.index_name)
                logger.info(f"Connected to Pinecone v5 index {self.index_name}")
                self.connected = True
                return True
            elif PINECONE_LEGACY_AVAILABLE:
                # Legacy client expects environment instead of cloud/region
                env = os.getenv("PINECONE_ENVIRONMENT", f"{self.region}-{self.cloud}")
                pinecone_legacy.init(api_key=self.api_key, environment=env)
                if self.index_name not in pinecone_legacy.list_indexes():
                    pinecone_legacy.create_index(self.index_name, dimension=self.dimension, metric="cosine")
                self.index = pinecone_legacy.Index(self.index_name)
                logger.info(f"Connected to Pinecone legacy index {self.index_name}")
                self.connected = True
                return True
            else:
                logger.error("Pinecone SDK not installed. Run: pip install pinecone or pinecone-client")
                return False
        except Exception as e:
            logger.error(f"Failed to connect/create Pinecone index: {e}")
            self.connected = False
            return False

    async def generate_embeddings(self, texts):
        if self.embedding_model:
            return self.embedding_model.encode(texts).tolist()
        elif self.openai_client:
            resp = self.openai_client.embeddings.create(model="text-embedding-3-small", input=texts)
            return [d.embedding for d in resp.data]
        else:
            raise Exception("No embedding model available for Pinecone")

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50):
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = "".join([" ".join(words[i:i + chunk_size])])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    async def add_content(self, content_id, user_id, content_type, title, content, metadata=None) -> bool:
        if not self.index:
            ok = await self.connect()
            if not ok:
                return False
        try:
            chunks = self.chunk_text(content)
            if not chunks:
                return False
            embeddings = await self.generate_embeddings(chunks)
            vectors = []
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                meta = {
                    "content_id": content_id,
                    "user_id": user_id,
                    "content_type": content_type,
                    "title": title,
                    "chunk_index": i,
                }
                if metadata:
                    meta.update(metadata)
                vec_id = f"{content_id}:{i}"
                vectors.append({"id": vec_id, "values": emb, "metadata": meta})
            # Upsert
            namespace = str(user_id)
            if PINECONE_V5_AVAILABLE:
                self.index.upsert(vectors=vectors, namespace=namespace)
            else:
                self.index.upsert(vectors=vectors, namespace=namespace)
            return True
        except Exception as e:
            logger.error(f"Failed to upsert to Pinecone: {e}")
            return False

    async def search_similar(self, query, user_id, limit=10, content_type=None, score_threshold=0.7):
        if not self.index:
            ok = await self.connect()
            if not ok:
                return []
        try:
            q_emb = (await self.generate_embeddings([query]))[0]
            namespace = str(user_id)
            if PINECONE_V5_AVAILABLE:
                res = self.index.query(vector=q_emb, top_k=limit, include_metadata=True, namespace=namespace)
                matches = res.get("matches", []) if isinstance(res, dict) else res.matches
            else:
                res = self.index.query(vector=q_emb, top_k=limit, include_metadata=True, namespace=namespace)
                matches = res.get("matches", []) if isinstance(res, dict) else res.matches
            results = []
            for m in matches or []:
                score = m.get("score") if isinstance(m, dict) else m.score
                meta = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {})
                if score is None or (score_threshold and score < score_threshold):
                    continue
                results.append({
                    "content_id": meta.get("content_id"),
                    "title": meta.get("title"),
                    "content": None,  # we don't store chunk text by default
                    "content_type": meta.get("content_type"),
                    "chunk_index": meta.get("chunk_index"),
                    "similarity_score": score,
                    "metadata": meta or {},
                })
            return results
        except Exception as e:
            logger.error(f"Pinecone search failed: {e}")
            return []

    async def delete_content(self, content_id: str, user_id: str) -> bool:
        if not self.index:
            ok = await self.connect()
            if not ok:
                return False
        try:
            namespace = str(user_id)
            # Prefer filter deletion if supported
            try:
                self.index.delete(filter={"content_id": content_id}, namespace=namespace)
                return True
            except Exception:
                # Fallback: delete ids by prefix (requires listing ids – not available in v5 easily)
                # As a fallback, do nothing and report False
                logger.warning("Pinecone delete by filter not supported on this SDK; manual cleanup may be needed")
                return False
        except Exception as e:
            logger.error(f"Pinecone delete failed: {e}")
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

# Clean re-definition of Pinecone service to avoid accidental overrides above
class PineconeVectorService:  # noqa: F811 (intentional redefinition)
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX", "knowledge-base")
        self.cloud = os.getenv("PINECONE_CLOUD", "aws")
        self.region = os.getenv("PINECONE_REGION", "us-east-1")
        self.index = None
        self.connected = False
        # Embeddings
        self.embedding_model = None
        self.openai_client = None
        self.dimension = 384
        # Prefer sentence-transformers if available
        try:
            from sentence_transformers import SentenceTransformer as _ST
            self.embedding_model = _ST('all-MiniLM-L6-v2')
            self.dimension = 384
        except Exception:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    from openai import OpenAI as _OpenAI
                    self.openai_client = _OpenAI(api_key=api_key)
                    self.dimension = 1536  # text-embedding-3-small
                except Exception:
                    self.openai_client = None

    async def connect(self) -> bool:
        if not self.api_key:
            return False
        try:
            if PINECONE_V5_AVAILABLE:
                pc = PineconeClient(api_key=self.api_key)
                names = [idx.name for idx in pc.list_indexes()]
                if self.index_name not in names:
                    pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine",
                        spec=PineconeServerlessSpec(cloud=self.cloud, region=self.region),
                    )
                self.index = pc.Index(self.index_name)
                self.connected = True
                return True
            elif PINECONE_LEGACY_AVAILABLE:
                env = os.getenv("PINECONE_ENVIRONMENT", f"{self.region}-{self.cloud}")
                pinecone_legacy.init(api_key=self.api_key, environment=env)
                if self.index_name not in pinecone_legacy.list_indexes():
                    pinecone_legacy.create_index(self.index_name, dimension=self.dimension, metric="cosine")
                self.index = pinecone_legacy.Index(self.index_name)
                self.connected = True
                return True
            return False
        except Exception:
            self.connected = False
            return False

    async def _emb(self, texts):
        if self.embedding_model is not None:
            return self.embedding_model.encode(texts).tolist()
        if self.openai_client is not None:
            resp = self.openai_client.embeddings.create(model="text-embedding-3-small", input=texts)
            return [d.embedding for d in resp.data]
        raise RuntimeError("Embedding models not available")

    def _chunks(self, text: str, chunk_size: int = 500, overlap: int = 50):
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            part = " ".join(words[i:i + chunk_size]).strip()
            if part:
                chunks.append(part)
        return chunks

    async def add_content(self, content_id, user_id, content_type, title, content, metadata=None) -> bool:
        if not self.connected:
            ok = await self.connect()
            if not ok:
                return False
        try:
            chunks = self._chunks(content)
            if not chunks:
                return False
            embs = await self._emb(chunks)
            namespace = str(user_id)
            vectors = []
            for i, (chunk, emb) in enumerate(zip(chunks, embs)):
                meta = {"content_id": content_id, "user_id": user_id, "content_type": content_type, "title": title, "chunk_index": i}
                if metadata:
                    meta.update(metadata)
                vectors.append({"id": f"{content_id}:{i}", "values": emb, "metadata": meta})
            self.index.upsert(vectors=vectors, namespace=namespace)
            return True
        except Exception:
            return False

    async def search_similar(self, query, user_id, limit=10, content_type=None, score_threshold=0.0):
        if not self.connected:
            ok = await self.connect()
            if not ok:
                return []
        try:
            q = (await self._emb([query]))[0]
            res = self.index.query(vector=q, top_k=limit, include_metadata=True, namespace=str(user_id))
            matches = res.get("matches", []) if isinstance(res, dict) else getattr(res, "matches", [])
            out = []
            for m in matches or []:
                score = m.get("score") if isinstance(m, dict) else getattr(m, "score", None)
                meta = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {})
                if score is None or score < score_threshold:
                    continue
                out.append({
                    "content_id": meta.get("content_id"),
                    "title": meta.get("title"),
                    "content": None,
                    "content_type": meta.get("content_type"),
                    "chunk_index": meta.get("chunk_index"),
                    "similarity_score": score,
                    "metadata": meta or {},
                })
            return out
        except Exception:
            return []

    async def delete_content(self, content_id: str, user_id: str) -> bool:
        # Best-effort delete by filter if supported; otherwise skip
        try:
            self.index.delete(filter={"content_id": content_id}, namespace=str(user_id))
            return True
        except Exception:
            return True


# Global service instance (switchable)
_backend = os.getenv("VECTOR_BACKEND", "milvus").lower()
if _backend == "pinecone":
    vector_service = PineconeVectorService()
else:
    vector_service = MilvusVectorService()
