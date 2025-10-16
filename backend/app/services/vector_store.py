import logging
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
from typing import Dict
from typing import List, Tuple
from app.utils.embedding_client import EmbeddingClient
import os
import pickle
import hashlib

logger = logging.getLogger(__name__)


class CustomEmbeddings:
    """Custom embeddings wrapper for LangChain compatibility"""

    def __init__(self, embedding_client: EmbeddingClient):
        self.client = embedding_client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        return self.client.embed_batch(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed a query"""
        return self.client.embed_text(text)

class VectorStoreManager:
    def __init__(self):
        self.index_path = settings.faiss_index_path
        self.metadata_path = os.path.join(self.index_path, "metadata.pkl")
        self.embedding_client = EmbeddingClient()
        self.embeddings = CustomEmbeddings(self.embedding_client)
        self.vector_store = self._load_or_create_index()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.metadata_map = self._load_metadata()

    def _load_or_create_index(self) -> FAISS:
        index_file = os.path.join(self.index_path, "index.faiss")
        if os.path.exists(index_file):
            try:
                logger.info(f"Loading index from {self.index_path}")
                return FAISS.load_local(
                    self.index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception as e:
                logger.warning(
                    f"Could not load existing index: {e}. Creating new index."
                )
        logger.info(f"Creating new index at {self.index_path}")
        dummy_doc = Document(page_content="Initialization", metadata={"source", "init"})
        vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
        return vector_store

    def _load_metadata(self) -> Dict:
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "rb") as f:
                return pickle.load(f)
        else:
            return {}

    def _save_metadata(self):
        try:
            os.makedirs(self.index_path, exist_ok=True)
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata_map, f)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def add_document(self, content: str, job_id: str, url: str, title: str) -> int:
        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            if content_hash in self.metadata_map:
                logger.info(f"Document already indexed: {url}")
                return self.metadata_map[content_hash]

            chunks = self.text_splitter.split_text(content)
            if not chunks:
                raise ValueError("No chunks created from content")
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "source": url,
                        "job_id": job_id,
                        "title": title,
                        "content_hash": content_hash,
                        "chunk_index": i,
                    },
                )
                for i, chunk in enumerate(chunks)
            ]
            self.vector_store.add_documents(documents)
            self.vector_store.save_local(self.index_path)
            self.metadata_map[content_hash] = {
                "job_id": job_id,
                "url": url,
                "title": title,
                "num_chunks": len(chunks),
            }
            self._save_metadata()
            return len(chunks)

        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            return 0

    def search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        k = k or settings.top_k_results
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def get_stats(self):
        return {
            "total_documents": len(self.metadata_map),
            "index_path": self.index_path,
        }

vector_store_manager = VectorStoreManager()
