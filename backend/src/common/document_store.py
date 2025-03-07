import os
import logging

# Use the proper Haystack 2.x imports
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

# No fallback needed as we're using haystack_integrations directly
USING_DIRECT_IMPORTS = False

from common.config import settings


def initialize_document_store():
    # Initialize Elasticsearch document store for BM25 only (no embeddings)
    es_store = ElasticsearchDocumentStore(
        hosts=settings.elasticsearch_url,
        # Authentication can be added back if needed using basic_auth
        # basic_auth=(settings.elasticsearch_user, settings.elasticsearch_password),
        index="default",
        request_timeout=30,  # Updated from deprecated 'timeout' parameter
        verify_certs=False,  # For development only
    )
    
    # For backward compatibility, return only the Elasticsearch store
    return es_store

def get_qdrant_store():
    embedding_dim = settings.embedding_dim
    
    # Initialize Qdrant document store for vector search
    return QdrantDocumentStore(
        url=settings.qdrant_url,
        index=settings.qdrant_collection_name,
        embedding_dim=embedding_dim,
        recreate_index=False,  # Temporarily set to True to force recreation with the correct dimensions
        hnsw_config={
            "m": 16,
            "ef_construct": 100
        }
    )
