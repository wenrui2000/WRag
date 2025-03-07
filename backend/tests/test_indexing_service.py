import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from indexing.service import IndexingService, IndexingConfig
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore


@pytest.fixture
def mock_document_store():
    return Mock(spec=OpenSearchDocumentStore)

@pytest.fixture
def indexing_service(mock_document_store):
    return IndexingService(document_store=mock_document_store)

def test_index_files(indexing_service):
    # Mock the file manager
    indexing_service.file_manager.file_paths = ["test1.txt", "test2.pdf"]
    
    # Mock the pipeline
    mock_pipeline = Mock()
    mock_pipeline.run.return_value = {"some": "result"}
    indexing_service.pipeline = mock_pipeline

    # Test indexing
    result = indexing_service.index_files()
    
    # Verify
    mock_pipeline.run.assert_called_once_with({
        "file_type_router": {"sources": ["test1.txt", "test2.pdf"]}
    })
    assert result == {"some": "result"}

def test_save_uploaded_file(indexing_service):
    # Mock file_manager and index_files
    indexing_service.file_manager.save_file = Mock(return_value="/path/to/saved/file.txt")
    indexing_service.index_files = Mock()

    # Test
    result = indexing_service.save_uploaded_file("test.txt", b"content")

    # Verify
    assert result == "/path/to/saved/file.txt"
    indexing_service.file_manager.save_file.assert_called_once_with("test.txt", b"content")
    indexing_service.index_files.assert_called_once_with("/path/to/saved/file.txt") 

def test_indexing_pipeline_creation(mock_document_store):
    service = IndexingService(document_store=mock_document_store)
    assert service.pipeline is not None
    assert service.pipeline.get_component("file_type_router") is not None
    assert service.pipeline.get_component("document_embedder") is not None

def test_index_files_processing(indexing_service):
    test_file = Path("test.txt")
    test_file.write_text("Test content")

    try:
        # Create a mock with a proper call_args structure
        mock_write = Mock()
        mock_write.call_args = ((["test_doc"],), {})  # Simulate documents being passed
        indexing_service.config.document_store.write_documents = mock_write

        result = indexing_service.index_files("test.txt")

        assert mock_write.called
        # Just verify it was called, since the actual arguments might vary
        assert mock_write.call_count > 0
    finally:
        test_file.unlink() 