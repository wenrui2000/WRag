from typing import List, Dict, Any, Optional
import json
import mysql.connector
from mysql.connector import Error
import logging
import time

from haystack import component
from haystack.dataclasses import Document

logger = logging.getLogger(__name__)

@component
class MySQLDocumentWriter:
    """
    A component for writing Haystack Document objects to a MySQL database.
    
    This component writes documents to the `wrag_documents` table, extracting
    the file_path from the document's metadata along with page_number, 
    split_idx_start, and split_id when available. The document's ID is preserved
    as a unique identifier.
    
    This component is MANDATORY - any failures will cause the entire indexing pipeline
    to fail. No errors are suppressed.
    
    Attributes:
        host: MySQL server hostname
        user: MySQL username
        password: MySQL password
        database: MySQL database name
        port: MySQL server port (default: 3306)
        max_retries: Maximum number of connection retries
        retry_delay: Delay between retries in seconds
        batch_size: Number of documents to insert in a batch (default: 1000)
    """
    
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
        max_retries: int = 3,
        retry_delay: int = 2,
        batch_size: int = 1000,
    ):
        """
        Initialize the MySQL Document Writer.
        
        Args:
            host: MySQL server hostname
            user: MySQL username
            password: MySQL password
            database: MySQL database name
            port: MySQL server port (default: 3306)
            max_retries: Maximum number of connection retries (default: 3)
            retry_delay: Delay between retries in seconds (default: 2)
            batch_size: Number of documents to insert in a batch (default: 1000)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.conn = None
        
    def _get_connection(self):
        """
        Get a MySQL database connection with retry logic.
        
        Returns:
            A MySQL connection object
        
        Raises:
            Error: If connection fails after maximum retries
        """
        if self.conn is None or not self.conn.is_connected():
            retries = 0
            last_error = None
            
            while retries < self.max_retries:
                try:
                    logger.info(f"Connecting to MySQL at {self.host}:{self.port} as {self.user}")
                    self.conn = mysql.connector.connect(
                        host=self.host,
                        user=self.user,
                        password=self.password,
                        database=self.database,
                        port=self.port
                    )
                    logger.info(f"Successfully connected to MySQL database '{self.database}'")
                    return self.conn
                except Error as e:
                    last_error = e
                    retries += 1
                    if retries < self.max_retries:
                        logger.warning(f"Failed to connect to MySQL (Attempt {retries}/{self.max_retries}): {e}")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(f"Error connecting to MySQL after {self.max_retries} attempts: {e}")
                        logger.error(f"Connection details: host={self.host}, user={self.user}, database={self.database}, port={self.port}")
                        raise Error(f"Failed to connect to MySQL after {self.max_retries} attempts: {e}")
        
        return self.conn
    
    @component.output_types(written_documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """
        Write documents to the MySQL database using batch insertion.
        
        This method handles all conversion logic and writes directly to the wrag_documents table.
        It extracts the file_path from the document's metadata which serves as a foreign key 
        to the source_documents table. It also extracts page_number, split_idx_start, and 
        split_id from metadata when available. The document's ID is stored as a unique identifier.
        
        Documents are inserted in batches to improve performance.
        
        Note: file_path is limited to 768 characters in the database and will be truncated if longer.
        
        Important: This is a MANDATORY component. Any errors will be propagated and will cause the
        entire indexing pipeline to fail.
        
        Args:
            documents: List of Document objects to write to the database
            
        Returns:
            Dict with key 'written_documents' containing the list of documents that were written
            
        Raises:
            Exception: Any database errors or issues with writing documents
        """
        if not documents:
            return {"written_documents": []}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        written_docs = []
        skipped_docs = []
        batch_params = []
        
        try:
            # First pass - validate all documents, check if source documents exist
            file_paths_to_check = []
            doc_index_map = {}  # Maps file_path to index in documents list
            
            for i, doc in enumerate(documents):
                # Extract file_path from doc.meta - required for foreign key
                file_path = doc.meta.get("file_path")
                
                if not file_path:
                    logger.warning(f"Document has no file_path in metadata. Skipping.")
                    skipped_docs.append(doc)
                    continue
                
                # Make sure document has an ID
                if not doc.id:
                    logger.warning(f"Document has no ID. Skipping.")
                    skipped_docs.append(doc)
                    continue
                
                # Truncate file_path if needed (database limit is 768 chars)
                original_file_path = file_path
                if len(file_path) > 768:
                    file_path = file_path[:768]
                    logger.warning(f"File path too long, truncated from {len(original_file_path)} to 768 characters: {file_path}")
                    
                    # Update document metadata with truncated file_path for consistency
                    doc.meta["file_path"] = file_path
                
                # Add file_path to list of paths to check
                if file_path not in file_paths_to_check:
                    file_paths_to_check.append(file_path)
                
                # Map document index to file_path
                if file_path not in doc_index_map:
                    doc_index_map[file_path] = []
                doc_index_map[file_path].append(i)
            
            # Check all source documents exist in a single query
            if file_paths_to_check:
                placeholders = ', '.join(['%s'] * len(file_paths_to_check))
                check_query = f"SELECT file_path FROM source_documents WHERE file_path IN ({placeholders})"
                cursor.execute(check_query, file_paths_to_check)
                existing_paths = [row[0] for row in cursor.fetchall()]
                
                # Find missing paths
                missing_paths = set(file_paths_to_check) - set(existing_paths)
                if missing_paths:
                    for missing_path in missing_paths:
                        logger.warning(f"Source document with file_path '{missing_path}' not found in database. Skipping related documents.")
                        # Skip all documents with this file_path
                        if missing_path in doc_index_map:
                            for idx in doc_index_map[missing_path]:
                                skipped_docs.append(documents[idx])
            
            # Second pass - prepare batch parameters for documents with valid source paths
            for i, doc in enumerate(documents):
                if doc in skipped_docs:
                    continue
                
                file_path = doc.meta.get("file_path")
                if file_path not in existing_paths:
                    continue
                
                # Extract additional fields from metadata
                page_number = doc.meta.get("page_number")
                split_idx_start = doc.meta.get("split_idx_start")
                split_id = doc.meta.get("split_id")
                
                # Convert metadata to JSON
                metadata_json = json.dumps(doc.meta) if doc.meta else None
                
                # Add parameters to batch
                batch_params.append((
                    doc.id,
                    file_path,
                    page_number,
                    split_idx_start,
                    split_id,
                    metadata_json
                ))
                written_docs.append(doc)
                
                # If batch is full, execute it
                if len(batch_params) >= self.batch_size:
                    self._execute_batch(cursor, batch_params)
                    batch_params = []
            
            # Execute any remaining documents in the batch
            if batch_params:
                self._execute_batch(cursor, batch_params)
            
            conn.commit()
            
            if len(skipped_docs) > 0:
                logger.info(f"Skipped {len(skipped_docs)} documents due to missing required fields")
                
            logger.info(f"Successfully wrote {len(written_docs)} documents to MySQL wrag_documents table")
            return {"written_documents": written_docs}
        except Exception as e:
            # Roll back transaction
            try:
                conn.rollback()
            except:
                pass
                
            # Propagate the error - this will cause the pipeline to fail
            logger.error(f"CRITICAL: Failed to write documents to MySQL: {e}")
            raise Exception(f"MySQL write operation failed: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def _execute_batch(self, cursor, batch_params):
        """
        Execute a batch insertion of documents.
        
        Args:
            cursor: MySQL cursor
            batch_params: List of parameter tuples for batch insertion
        """
        if not batch_params:
            return
            
        # Insert document into wrag_documents table using batch insert
        query = """
        INSERT INTO wrag_documents (
            id, file_path, page_number, split_idx_start, split_id, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            file_path = VALUES(file_path),
            page_number = VALUES(page_number),
            split_idx_start = VALUES(split_idx_start),
            split_id = VALUES(split_id),
            metadata = VALUES(metadata)
        """
        
        cursor.executemany(query, batch_params)
        logger.debug(f"Batch inserted {len(batch_params)} documents")
    
    def close(self):
        """Close the database connection if it's open."""
        if self.conn and self.conn.is_connected():
            self.conn.close()

@component
class MySQLSourceDocumentWriter:
    """
    A component for writing source documents to a MySQL database.
    
    This component writes documents to the `source_documents` table, extracting
    necessary fields like file_path and metadata from the provided documents.
    Document content is NOT stored to avoid database size limitations.
    
    This component is MANDATORY - any failures will cause the entire indexing pipeline
    to fail. No errors are suppressed.
    
    Attributes:
        host: MySQL server hostname
        user: MySQL username
        password: MySQL password
        database: MySQL database name
        port: MySQL server port (default: 3306)
        max_retries: Maximum number of connection retries
        retry_delay: Delay between retries in seconds
        batch_size: Number of documents to insert in a batch (default: 1000)
    """
    
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
        max_retries: int = 3,
        retry_delay: int = 2,
        batch_size: int = 1000,
    ):
        """
        Initialize the MySQL Source Document Writer.
        
        Args:
            host: MySQL server hostname
            user: MySQL username
            password: MySQL password
            database: MySQL database name
            port: MySQL server port (default: 3306)
            max_retries: Maximum number of connection retries (default: 3)
            retry_delay: Delay between retries in seconds (default: 2)
            batch_size: Number of documents to insert in a batch (default: 1000)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.conn = None
        
    def _get_connection(self):
        """
        Get a MySQL database connection with retry logic.
        
        Returns:
            A MySQL connection object
        
        Raises:
            Error: If connection fails after maximum retries
        """
        if self.conn is None or not self.conn.is_connected():
            retries = 0
            last_error = None
            
            while retries < self.max_retries:
                try:
                    logger.info(f"Connecting to MySQL at {self.host}:{self.port} as {self.user}")
                    self.conn = mysql.connector.connect(
                        host=self.host,
                        user=self.user,
                        password=self.password,
                        database=self.database,
                        port=self.port
                    )
                    logger.info(f"Successfully connected to MySQL database '{self.database}'")
                    return self.conn
                except Error as e:
                    last_error = e
                    retries += 1
                    if retries < self.max_retries:
                        logger.warning(f"Failed to connect to MySQL (Attempt {retries}/{self.max_retries}): {e}")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(f"Error connecting to MySQL after {self.max_retries} attempts: {e}")
                        logger.error(f"Connection details: host={self.host}, user={self.user}, database={self.database}, port={self.port}")
                        raise Error(f"Failed to connect to MySQL after {self.max_retries} attempts: {e}")
        
        return self.conn
    
    @component.output_types(written_documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """
        Write source documents to the MySQL database using batch insertion.
        
        This method handles extracting file_path and metadata from documents
        and writes directly to the source_documents table. Document content is NOT stored
        to avoid database size limitations. The ctime (creation timestamp)
        field is automatically set by MySQL when a new record is inserted.
        The table uses file_path as the unique key and auto-increment for primary keys.
        
        Documents are inserted in batches to improve performance.
        
        Note: file_path is limited to 768 characters in the database and will be truncated if longer.
        
        Important: This is a MANDATORY component. Any errors will be propagated and will cause the
        entire indexing pipeline to fail.
        
        Args:
            documents: List of Document objects to write to the database
            
        Returns:
            Dict with key 'written_documents' containing the list of documents that were written
            
        Raises:
            Exception: Any database errors or issues with writing documents
        """
        if not documents:
            return {"written_documents": []}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        written_docs = []
        skipped_docs = []
        batch_params = []
        
        try:
            for doc in documents:
                # Extract file_path from document metadata - this is now our unique key
                file_path = doc.meta.get("file_path", None) if doc.meta else None
                
                if not file_path:
                    logger.warning(f"Document has no file_path in metadata. Skipping.")
                    skipped_docs.append(doc)
                    continue
                
                # Truncate file_path if needed (database limit is 768 chars)
                original_file_path = file_path
                if len(file_path) > 768:
                    file_path = file_path[:768]
                    logger.warning(f"File path too long, truncated from {len(original_file_path)} to 768 characters: {file_path}")
                    
                    # Update document metadata with truncated file_path for consistency
                    doc.meta["file_path"] = file_path
                
                # Calculate content length if content exists
                content_length = len(doc.content) if doc.content else 0
                
                # Update metadata - no need to include file_path or content_length as they're separate fields now
                meta = doc.meta.copy() if doc.meta else {}
                
                # Convert metadata to JSON
                metadata_json = json.dumps(meta) if meta else None
                
                # Add parameters to batch
                batch_params.append((
                    file_path,
                    content_length,
                    metadata_json
                ))
                written_docs.append(doc)
                
                # If batch is full, execute it
                if len(batch_params) >= self.batch_size:
                    self._execute_batch(cursor, batch_params)
                    batch_params = []
            
            # Execute any remaining documents in the batch
            if batch_params:
                self._execute_batch(cursor, batch_params)
            
            conn.commit()
            
            if len(skipped_docs) > 0:
                logger.info(f"Skipped {len(skipped_docs)} documents due to missing required fields")
                
            logger.info(f"Successfully wrote {len(written_docs)} documents to MySQL source_documents table")
            return {"written_documents": written_docs}
        except Exception as e:
            # Roll back transaction
            try:
                conn.rollback()
            except:
                pass
                
            # Propagate the error - this will cause the pipeline to fail
            logger.error(f"CRITICAL: Failed to write source documents to MySQL: {e}")
            raise Exception(f"MySQL source document write operation failed: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def _execute_batch(self, cursor, batch_params):
        """
        Execute a batch insertion of source documents.
        
        Args:
            cursor: MySQL cursor
            batch_params: List of parameter tuples for batch insertion
        """
        if not batch_params:
            return
            
        # Insert document into source_documents table using batch insert
        query = """
        INSERT INTO source_documents (
            file_path, content_length, metadata
        ) VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            content_length = VALUES(content_length),
            metadata = VALUES(metadata)
        """
        
        cursor.executemany(query, batch_params)
        logger.debug(f"Batch inserted {len(batch_params)} source documents")
    
    def close(self):
        """Close the database connection if it's open."""
        if self.conn and self.conn.is_connected():
            self.conn.close() 