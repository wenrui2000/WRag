import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the path if not already there
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from common.document_store import initialize_document_store, get_qdrant_store
from common.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        elasticsearch_url="http://test:9200",
        elasticsearch_user="test_user",
        elasticsearch_password="test_pass",
        embedding_dim=384,
        qdrant_url="http://test-qdrant:6333",
        qdrant_collection_name="test_collection"
    )

@patch("common.document_store.settings")
@patch("common.document_store.ElasticsearchDocumentStore")
def test_initialize_document_store(mock_es_store, mock_settings_module, mock_settings):
    # Set up the mock settings
    mock_settings_module.elasticsearch_url = mock_settings.elasticsearch_url
    mock_settings_module.elasticsearch_user = mock_settings.elasticsearch_user
    mock_settings_module.elasticsearch_password = mock_settings.elasticsearch_password
    mock_settings_module.embedding_dim = mock_settings.embedding_dim

    # Mock the ElasticsearchDocumentStore constructor
    mock_instance = Mock()
    mock_es_store.return_value = mock_instance

    # Initialize document store
    doc_store = initialize_document_store()

    # Assert ElasticsearchDocumentStore was called with correct parameters
    mock_es_store.assert_called_once_with(
        hosts=mock_settings.elasticsearch_url,
        username=mock_settings.elasticsearch_user,
        password=mock_settings.elasticsearch_password,
        index="default",
        timeout=30,
        verify_certs=False
    )
    
    # Assert the function returns the instance
    assert doc_store == mock_instance

@patch("common.document_store.settings")
@patch("common.document_store.QdrantDocumentStore")
def test_get_qdrant_store(mock_qdrant_store, mock_settings_module, mock_settings):
    # Set up the mock settings
    mock_settings_module.qdrant_url = mock_settings.qdrant_url
    mock_settings_module.qdrant_collection_name = mock_settings.qdrant_collection_name
    mock_settings_module.embedding_dim = mock_settings.embedding_dim
    
    # Mock the QdrantDocumentStore constructor
    mock_instance = Mock()
    mock_qdrant_store.return_value = mock_instance
    
    # Call the function
    result = get_qdrant_store()
    
    # Assert QdrantDocumentStore was called with correct parameters
    mock_qdrant_store.assert_called_once_with(
        url=mock_settings.qdrant_url,
        index=mock_settings.qdrant_collection_name,
        embedding_dim=mock_settings.embedding_dim,
        recreate_index=False,
        hnsw_config={
            "m": 16,
            "ef_construct": 100
        }
    )
    
    # Assert the function returns the instance
    assert result == mock_instance 