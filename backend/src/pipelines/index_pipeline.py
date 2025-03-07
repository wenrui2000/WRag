"""
Index Pipeline Builder Module

This module builds the indexing pipeline programmatically instead of using YAML
to avoid import and configuration issues.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from haystack import Pipeline
from haystack.components.routers import FileTypeRouter
from haystack.components.converters import TextFileToDocument, PyPDFToDocument, MarkdownToDocument
from haystack.components.joiners import DocumentJoiner
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.document_stores.types import DuplicatePolicy

# Import from haystack_integrations namespace
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from common.config import settings
from common.document_store import get_qdrant_store
from indexing.mysql_document_writer import MySQLDocumentWriter, MySQLSourceDocumentWriter

logger = logging.getLogger(__name__)

def create_index_pipeline(
    document_store: ElasticsearchDocumentStore,
    qdrant_store: Optional[QdrantDocumentStore] = None,
    embedder_model: str = "intfloat/multilingual-e5-base",
    split_by: str = "word",
    split_length: int = 250,
    split_overlap: int = 30,
    respect_sentence_boundary: bool = True,
    split_threshold: int = 10,
    language: str = "en",
    writer_policy: DuplicatePolicy = DuplicatePolicy.SKIP
) -> Pipeline:
    """
    Create and configure the indexing pipeline programmatically.
    
    Args:
        document_store: ElasticsearchDocumentStore for BM25 search
        qdrant_store: QdrantDocumentStore for vector search (required for dual indexing)
        embedder_model: Model to use for document embedding
        split_by: How to split documents ('word', 'sentence', 'passage', 'page', 'period', 'line')
        split_length: Maximum split length
        split_overlap: Overlap between splits
        respect_sentence_boundary: Whether to respect sentence boundaries when splitting
        split_threshold: Minimum split length
        language: Language for sentence boundary detection
        writer_policy: Policy for handling duplicates
    
    Returns:
        Pipeline: The configured Haystack pipeline
        
    Raises:
        Exception: If MySQL integration is enabled but fails to initialize or connect
    """
    logger.info("Creating indexing pipeline programmatically")
    
    # Ensure Qdrant store is provided
    if not qdrant_store:
        logger.warning("Qdrant store not provided. Creating one with default settings.")
        qdrant_store = get_qdrant_store()
    
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Initialize components
    logger.info("Creating pipeline components...")
    
    # Create document converters for different file types
    text_converter = TextFileToDocument()
    markdown_converter = MarkdownToDocument()
    pdf_converter = PyPDFToDocument()
    
    # Create file type router
    file_router = FileTypeRouter(
        mime_types={
            "text/plain": "text_converter",
            "text/markdown": "markdown_converter", 
            "application/pdf": "pdf_converter"
        }
    )
    
    # Create document splitter and cleaner
    document_cleaner = DocumentCleaner()
    document_splitter = DocumentSplitter(
        split_by=split_by,
        split_length=split_length,
        split_overlap=split_overlap,
        split_threshold=split_threshold,
        respect_sentence_boundary=respect_sentence_boundary,
        language=language,
        use_split_rules=True,
        extend_abbreviations=True
    )
    
    # Create document joiner (for multiple files)
    document_joiner = DocumentJoiner()
    
    # Create document writers
    es_writer = DocumentWriter(document_store=document_store, policy=writer_policy)
    
    # Create embedder - always use SentenceTransformers
    logger.info(f"Using SentenceTransformers embedder with model: {embedder_model}")
    document_embedder = SentenceTransformersDocumentEmbedder(
        model=embedder_model,
        device=None
    )
    
    # Create Qdrant writer
    qdrant_writer = DocumentWriter(document_store=qdrant_store, policy=writer_policy)
    
    # Create MySQL writers if enabled
    mysql_source_writer = None
    mysql_document_writer = None
    mysql_enabled = settings.mysql_enabled
    
    if mysql_enabled:
        logger.info(f"Creating MySQL document writers for host: {settings.mysql_host}")
        # No try/except here - if MySQL fails to initialize, we want the pipeline to fail
        mysql_source_writer = MySQLSourceDocumentWriter(
            host=settings.mysql_host,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            port=settings.mysql_port
        )
        
        mysql_document_writer = MySQLDocumentWriter(
            host=settings.mysql_host,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            port=settings.mysql_port
        )
        logger.info("MySQL document writers created successfully")
    
    # Add components to pipeline
    logger.info("Adding components to pipeline...")
    pipeline.add_component("file_router", file_router)
    pipeline.add_component("text_converter", text_converter)
    pipeline.add_component("markdown_converter", markdown_converter)
    pipeline.add_component("pdf_converter", pdf_converter)
    pipeline.add_component("document_joiner", document_joiner)
    pipeline.add_component("document_cleaner", document_cleaner)
    pipeline.add_component("document_splitter", document_splitter)
    pipeline.add_component("es_writer", es_writer)
    pipeline.add_component("document_embedder", document_embedder)
    pipeline.add_component("qdrant_writer", qdrant_writer)
    
    # Add MySQL components if enabled
    if mysql_enabled and mysql_source_writer and mysql_document_writer:
        # No try/except here - if MySQL components fail to be added, we want the pipeline to fail
        pipeline.add_component("mysql_source_writer", mysql_source_writer)
        pipeline.add_component("mysql_document_writer", mysql_document_writer)
        logger.info("MySQL components added to pipeline")
    
    # Connect the components
    logger.info("Connecting pipeline components...")
    
    # Pass files to router
    pipeline.connect("file_router.text/plain", "text_converter.sources")
    pipeline.connect("file_router.text/markdown", "markdown_converter.sources")
    pipeline.connect("file_router.application/pdf", "pdf_converter.sources")
    
    # Join documents from different converters
    pipeline.connect("text_converter.documents", "document_joiner.documents")
    pipeline.connect("markdown_converter.documents", "document_joiner.documents")
    pipeline.connect("pdf_converter.documents", "document_joiner.documents")
    
    # Process flow with MySQL integration (if enabled)
    if mysql_enabled and mysql_source_writer and mysql_document_writer:
        # First save original documents to source_documents table
        # This is crucial for foreign key relationships to work correctly
        pipeline.connect("document_joiner.documents", "mysql_source_writer.documents")
        
        # Then process the written documents with source_id properly set
        pipeline.connect("mysql_source_writer.written_documents", "document_cleaner.documents")
        logger.info("Connected document_joiner -> mysql_source_writer -> document_cleaner")
    else:
        # Standard path if MySQL is not enabled
        pipeline.connect("document_joiner.documents", "document_cleaner.documents")
    
    # Continue with standard processing
    pipeline.connect("document_cleaner.documents", "document_splitter.documents")
    
    # Write to Elasticsearch
    pipeline.connect("document_splitter.documents", "es_writer.documents")
    
    # Embed and write to Qdrant (separate flow for vector search)
    pipeline.connect("document_splitter.documents", "document_embedder.documents")
    pipeline.connect("document_embedder.documents", "qdrant_writer.documents")
    
    # Connect MySQL document writer to the embedded documents (if enabled)
    if mysql_enabled and mysql_source_writer and mysql_document_writer:
        # No try/except here - if MySQL connection fails, we want the pipeline to fail
        pipeline.connect("document_embedder.documents", "mysql_document_writer.documents")
        logger.info("Connected document_embedder to mysql_document_writer")
    
    logger.info("Pipeline connections established.")
    
    return pipeline 