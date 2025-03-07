from typing import List, Dict, Any, Optional, Union
import json
import mysql.connector
from mysql.connector import Error
import logging
from io import BytesIO

from haystack import component
from haystack.dataclasses import Document

logger = logging.getLogger(__name__)

@component
class MySQLDocumentWriter:
    """
    A component for writing Haystack Document objects to a MySQL database.
    
    This component writes documents to the `wrag_documents` table, extracting
    the source_id from the document's metadata.
    
    Attributes:
        host: MySQL server hostname
        user: MySQL username
        password: MySQL password
        database: MySQL database name
        port: MySQL server port (default: 3306)
    """
    
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
    ):
        """
        Initialize the MySQL Document Writer.
        
        Args:
            host: MySQL server hostname
            user: MySQL username
            password: MySQL password
            database: MySQL database name
            port: MySQL server port (default: 3306)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.conn = None
        
    def _get_connection(self):
        """
        Get a MySQL database connection.
        
        Returns:
            A MySQL connection object
        """
        if self.conn is None or not self.conn.is_connected():
            try:
                self.conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    port=self.port
                )
            except Error as e:
                logger.error(f"Error connecting to MySQL: {e}")
                raise
        return self.conn
    
    def _convert_embedding_to_blob(self, embedding: Optional[List[float]]) -> Optional[bytes]:
        """
        Convert a dense embedding to binary format for storage.
        
        Args:
            embedding: List of float values representing the embedding
            
        Returns:
            Binary representation of the embedding or None if input is None
        """
        if embedding is None:
            return None
        
        try:
            # Convert the list of floats to bytes
            embedding_bytes = BytesIO()
            # Simple format: store as JSON
            # In production, consider using a more efficient binary format like numpy.save
            embedding_bytes.write(json.dumps(embedding).encode('utf-8'))
            return embedding_bytes.getvalue()
        except Exception as e:
            logger.error(f"Error converting embedding to blob: {e}")
            return None
    
    def _convert_sparse_embedding(self, sparse_embedding) -> tuple:
        """
        Convert sparse embedding to JSON serializable format.
        
        Args:
            sparse_embedding: The sparse embedding object
            
        Returns:
            Tuple of (indices_json, values_json) or (None, None) if input is None
        """
        if sparse_embedding is None:
            return None, None
        
        try:
            indices_json = json.dumps(sparse_embedding.indices)
            values_json = json.dumps(sparse_embedding.values)
            return indices_json, values_json
        except Exception as e:
            logger.error(f"Error converting sparse embedding: {e}")
            return None, None
    
    @component.output_types(written_documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """
        Write documents to the MySQL database.
        
        Args:
            documents: List of Document objects to write to the database
            
        Returns:
            Dict with key 'written_documents' containing the list of documents that were written
        """
        if not documents:
            return {"written_documents": []}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        written_docs = []
        
        for doc in documents:
            try:
                # Extract source_id from doc.meta
                source_id = doc.meta.get("source_id")
                
                # Convert embedding to binary format
                embedding_blob = self._convert_embedding_to_blob(doc.embedding)
                
                # Convert sparse embedding to JSON
                sparse_indices_json, sparse_values_json = self._convert_sparse_embedding(doc.sparse_embedding)
                
                # Convert metadata to JSON
                metadata_json = json.dumps(doc.meta) if doc.meta else None
                
                # Insert document into wrag_documents table
                query = """
                INSERT INTO wrag_documents (
                    id, source_id, content, score, embedding_vector, 
                    sparse_embedding_indices, sparse_embedding_values, 
                    metadata, creation_date, last_modified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content),
                    score = VALUES(score),
                    embedding_vector = VALUES(embedding_vector),
                    sparse_embedding_indices = VALUES(sparse_embedding_indices),
                    sparse_embedding_values = VALUES(sparse_embedding_values),
                    metadata = VALUES(metadata),
                    last_modified = NOW()
                """
                
                cursor.execute(
                    query,
                    (
                        doc.id,
                        source_id,
                        doc.content,
                        doc.score,
                        embedding_blob,
                        sparse_indices_json,
                        sparse_values_json,
                        metadata_json
                    )
                )
                written_docs.append(doc)
            except Exception as e:
                logger.error(f"Error writing document {doc.id} to MySQL: {e}")
                continue
        
        conn.commit()
        cursor.close()
        
        return {"written_documents": written_docs}
    
    def close(self):
        """Close the database connection if it's open."""
        if self.conn and self.conn.is_connected():
            self.conn.close() 