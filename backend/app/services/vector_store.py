import logging
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
from typing import Dict
from typing import List, Tuple

logger = logging.getLogger(__name__)


class VectorStoreManager:
    def __init__(self):
        pass

    def _load_or_create_index(self) -> FAISS:
        pass

    def _load_metadata(self) -> Dict:
        pass

    def _save_metadata(self):
        pass

    def add_document(self, content: str, job_id: str, url: str, title: str) -> int:
        pass

    def search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        pass

    def get_stats():
        pass


vector_store_manager = VectorStoreManager()
