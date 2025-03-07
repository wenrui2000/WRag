from pathlib import Path

from dataclasses import dataclass
import logging
from typing import Optional, List, Dict

from haystack.document_stores.types import DuplicatePolicy

# Import from haystack_integrations namespace as requested
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

# No fallback needed as we're using haystack_integrations directly
USING_DIRECT_IMPORTS = False

from fastapi import UploadFile

from common.document_store import initialize_document_store, get_qdrant_store
from common.file_manager import FileManager
from common.config import settings
from pipelines.index_pipeline import create_index_pipeline

logger = logging.getLogger(__name__)

"""@component
class FilePathRemover:
    @component.output_types(documents=List[Document])
    def run(self, docs: List[Document]):
        documents_copy = copy.deepcopy(documents)
    
        for doc in documents_copy:
            del doc.meta["file_path"]
        return {"documents": documents_copy}"""

@dataclass
class IndexingConfig:
    document_store: ElasticsearchDocumentStore
    qdrant_store: QdrantDocumentStore  # Required for dual indexing
    embedder_model: str = "intfloat/multilingual-e5-base"
    split_by: str = "word"
    split_length: int = 250
    split_overlap: int = 30
    respect_sentence_boundary: bool = True
    split_threshold: int = 10
    language: str = "en"
    writer_policy: DuplicatePolicy = DuplicatePolicy.SKIP


class IndexingService:
    def __init__(
        self,
        document_store: Optional[ElasticsearchDocumentStore] = None,
        qdrant_store: Optional[QdrantDocumentStore] = None,
        embedder_model: str = None,
        split_by: str = None,
        split_length: int = None,
        split_overlap: int = None,
        respect_sentence_boundary: bool = None,
        split_threshold: int = None,
        language: str = None,
        writer_policy: DuplicatePolicy = None
    ):
        # Initialize document stores if not provided
        self.document_store = document_store or initialize_document_store()
        self.qdrant_store = qdrant_store or get_qdrant_store()
        
        # Set up file management
        self.file_storage_path = Path(settings.file_storage_path)
        self.file_manager = FileManager(self.file_storage_path)
        
        # Use provided parameters or default to settings
        self.embedder_model = embedder_model or settings.embedding_model
        self.split_by = split_by or settings.split_by
        self.split_length = split_length or settings.split_length
        self.split_overlap = split_overlap or settings.split_overlap
        self.respect_sentence_boundary = respect_sentence_boundary or settings.get("respect_sentence_boundary", True)
        self.split_threshold = split_threshold or settings.get("split_threshold", 10)
        self.language = language or settings.get("language", "en")
        self.writer_policy = writer_policy or DuplicatePolicy.SKIP
        
        # Create the indexing pipeline using the code-based implementation
        self.config = IndexingConfig(
            document_store=self.document_store,
            qdrant_store=self.qdrant_store,
            embedder_model=self.embedder_model,
            split_by=self.split_by,
            split_length=self.split_length,
            split_overlap=self.split_overlap,
            respect_sentence_boundary=self.respect_sentence_boundary,
            split_threshold=self.split_threshold,
            language=self.language,
            writer_policy=self.writer_policy
        )
        
        # Create the pipeline with the config values
        self.pipeline = create_index_pipeline(
            document_store=self.config.document_store,
            qdrant_store=self.config.qdrant_store,
            embedder_model=self.config.embedder_model,
            split_by=self.config.split_by,
            split_length=self.config.split_length,
            split_overlap=self.config.split_overlap,
            respect_sentence_boundary=self.config.respect_sentence_boundary,
            split_threshold=self.config.split_threshold,
            language=self.config.language,
            writer_policy=self.config.writer_policy
        )
        logger.info("Indexing service initialized with dual indexing to Elasticsearch and Qdrant")

    async def index_file(self, file: UploadFile) -> Dict:
        # Save file to disk
        contents = await file.read()
        saved_path = self.save_uploaded_file(file.filename, contents)
        
        # Run the indexing pipeline
        try:
            # Get document count before indexing
            es_count_before = len(self.document_store.get_all_documents())
            qdrant_count_before = self._get_qdrant_document_count()
            
            # Run the indexing pipeline
            result = self.pipeline.run({"file_router": {"sources": [saved_path]}})
            
            # Get document count after indexing to determine the actual number of documents indexed
            es_count_after = len(self.document_store.get_all_documents())
            qdrant_count_after = self._get_qdrant_document_count()
            
            # Calculate the difference to get the actual number of documents indexed
            es_document_count = es_count_after - es_count_before
            qdrant_document_count = qdrant_count_after - qdrant_count_before
            
            # Use the maximum as the total document count (they should be equal, but this handles edge cases)
            total_document_count = max(es_document_count, qdrant_document_count)
            
            return {
                "filename": file.filename,
                "file_path": saved_path,
                "indexed_documents": total_document_count,
                "es_document_count": es_document_count,
                "qdrant_document_count": qdrant_document_count,
                "success": True,
                "message": f"File {file.filename} successfully indexed with {es_document_count} documents in Elasticsearch and {qdrant_document_count} documents in Qdrant"
            }
        except Exception as e:
            logging.error(f"Error indexing file {file.filename}: {str(e)}")
            return {
                "filename": file.filename,
                "file_path": saved_path,
                "error": str(e),
                "success": False
            }
    
    def _get_qdrant_document_count(self) -> int:
        """
        Get the total number of documents in the Qdrant document store
        
        Returns:
            int: The number of documents in Qdrant
        """
        try:
            # Attempt to count documents in Qdrant
            # First, check if the collection exists and is initialized
            collection_info = self.qdrant_store.client.get_collection(collection_name=self.qdrant_store.collection_name)
            if collection_info:
                count_result = self.qdrant_store.client.count(collection_name=self.qdrant_store.collection_name)
                return count_result.count
            return 0
        except Exception as e:
            logging.warning(f"Error counting documents in Qdrant: {str(e)}")
            return 0
    
    def index_files(self, path: Optional[str] = None):
        """
        Index all files in the specified path, or rescan and index all files in the default storage path
        to both Elasticsearch (for full-text search) and Qdrant (for embedding-based search)
        """
        file_paths = []
        
        if path and Path(path).exists():
            # Index files in a specific path
            file_paths = [str(p) for p in Path(path).glob("**/*") if p.is_file()]
        else:
            # Rescan and index all files in the default storage path
            file_paths = self.rescan_files_and_paths()
        
        results = []
        for file_path in file_paths:
            try:
                # Get document count before indexing
                es_count_before = len(self.document_store.get_all_documents())
                qdrant_count_before = self._get_qdrant_document_count()
                
                # Run the indexing pipeline
                result = self.pipeline.run({"file_router": {"sources": [file_path]}})
                
                # Get document count after indexing
                es_count_after = len(self.document_store.get_all_documents())
                qdrant_count_after = self._get_qdrant_document_count()
                
                # Calculate the difference
                es_document_count = es_count_after - es_count_before
                qdrant_document_count = qdrant_count_after - qdrant_count_before
                
                # Use the maximum as the total document count
                total_document_count = max(es_document_count, qdrant_document_count)
                
                results.append({
                    "file_path": file_path,
                    "indexed_documents": total_document_count,
                    "es_document_count": es_document_count,
                    "qdrant_document_count": qdrant_document_count,
                    "success": True,
                    "message": f"File {file_path} successfully indexed with {es_document_count} documents in Elasticsearch and {qdrant_document_count} documents in Qdrant"
                })
            except Exception as e:
                logging.error(f"Error indexing file {file_path}: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "error": str(e),
                    "success": False
                })
                
        return results
    
    def save_uploaded_file(self, filename: str, contents: bytes) -> str:
        """Save an uploaded file to the file storage path and return the full path"""
        return self.file_manager.save_file(filename, contents)
    
    def rescan_files_and_paths(self) -> List[str]:
        """Rescan the file storage path and return all file paths"""
        return self.file_manager.add_files_and_paths()
