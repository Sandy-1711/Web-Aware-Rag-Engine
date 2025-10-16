from typing import List, Tuple, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.utils.embedding_client import EmbeddingClient
from app.config import settings
import logging
import hashlib
import uuid

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages Qdrant vector store for document embeddings"""
    
    def __init__(self):
        self.collection_name = settings.qdrant_collection_name
        self.embedding_client = EmbeddingClient()
        
        # Initialize Qdrant client
        if settings.qdrant_api_key:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
        else:
            self.client = QdrantClient(url=settings.qdrant_url)
        
        self._ensure_collection()
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"Initialized Qdrant vector store: {settings.qdrant_url}")
    
    def _ensure_collection(self):
        """Ensure collection exists and has correct vector size"""
        try:
            # Get embedding dimension by creating a test embedding
            test_embedding = self.embedding_client.embed_text("test")
            embedding_dim = len(test_embedding)

            # Check if collection exists
            if self.client.collection_exists(self.collection_name):
                info = self.client.get_collection(self.collection_name)
                current_dim = info.config.params.vectors.size

                if current_dim != embedding_dim:
                    logger.warning(
                        f"Collection {self.collection_name} has wrong dimension {current_dim}, expected {embedding_dim}. Recreating..."
                    )
                    self.client.recreate_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=embedding_dim,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"✅ Recreated collection {self.collection_name} with correct dimension {embedding_dim}")
                else:
                    logger.info(f"Collection {self.collection_name} exists with correct dimension {embedding_dim}")
            else:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created new collection with dimension {embedding_dim}")

        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise

    def add_document(
        self,
        content: str,
        job_id: str,
        url: str,
        title: str
    ) -> int:
        """
        Add a document to the vector store
        
        Args:
            content: Document content
            job_id: Unique job identifier
            url: Source URL
            title: Document title
            
        Returns:
            Number of chunks created
        """
        try:
            # Create content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if already indexed
            existing = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="content_hash",
                            match=MatchValue(value=content_hash)
                        )
                    ]
                ),
                limit=1
            )
            
            if existing[0]:
                logger.info(f"Document already indexed: {url}")
                # Count existing chunks
                chunks_count = self.client.count(
                    collection_name=self.collection_name,
                    count_filter=Filter(
                        must=[
                            FieldCondition(
                                key="content_hash",
                                match=MatchValue(value=content_hash)
                            )
                        ]
                    )
                )
                return chunks_count.count
            
            # Split into chunks
            chunks = self.text_splitter.split_text(content)
            
            if not chunks:
                raise ValueError("No chunks created from content")
            
            # Generate embeddings for all chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = self.embedding_client.embed_batch(chunks)
            
            # Prepare points for Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid4())
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "content": chunk,
                            "source": url,
                            "job_id": job_id,
                            "title": title,
                            "chunk_index": i,
                            "content_hash": content_hash
                        }
                    )
                )
            
            # Upload points to Qdrant in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            logger.info(f"Added document to vector store: {url} ({len(chunks)} chunks)")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            raise
    
    def search(
        self,
        query: str,
        k: int = None
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (document_dict, score) tuples
        """
        k = k or settings.top_k_results
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_client.embed_text(query)
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k
            )
            
            # Convert to expected format
            formatted_results = []
            for result in results:
                doc_dict = {
                    "page_content": result.payload.get("content", ""),
                    "metadata": {
                        "source": result.payload.get("source", ""),
                        "title": result.payload.get("title", ""),
                        "job_id": result.payload.get("job_id", ""),
                        "chunk_index": result.payload.get("chunk_index", 0)
                    }
                }
                formatted_results.append((doc_dict, result.score))
            
            logger.info(f"Retrieved {len(formatted_results)} results for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "total_documents": collection_info.points_count,
                "collection_name": self.collection_name,
                "qdrant_url": settings.qdrant_url
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "qdrant_url": settings.qdrant_url
            }


# Singleton instance
vector_store_manager = VectorStoreManager()