import pytest
from unittest.mock import Mock, patch
from haystack.dataclasses import Document, GeneratedAnswer

from query.service import QueryService, QueryConfig
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore


@pytest.fixture
def mock_document_store():
    return Mock(spec=OpenSearchDocumentStore)

@pytest.fixture
def query_service(mock_document_store):
    return QueryService(document_store=mock_document_store)

def test_search(query_service):
    # Mock the pipeline
    mock_pipeline = Mock()
    mock_pipeline.run.return_value = {
        'answer_builder': {
            'answers': [
                GeneratedAnswer(
                    query="test query",
                    data="Test answer",
                    documents=[
                        Document(content="Test content", id="test_doc")
                    ]
                )
            ]
        }
    }
    query_service.pipeline = mock_pipeline

    # Test search
    result = query_service.search("test query", {"filter": "value"})
    
    # Verify
    mock_pipeline.run.assert_called_once_with({
        "bm25_retriever": {"query": "test query", "filters": {"filter": "value"}},
        "query_embedder": {"text": "test query"},
        "answer_builder": {"query": "test query"},
        "prompt_builder": {"query": "test query"}
    })
    assert isinstance(result, GeneratedAnswer)
    assert result.data == "Test answer"
    assert len(result.documents) == 1

def test_query_pipeline_creation(mock_document_store):
    service = QueryService(document_store=mock_document_store)
    assert service.pipeline is not None
    # Check if specific components exist using get_component
    assert service.pipeline.get_component("bm25_retriever") is not None
    assert service.pipeline.get_component("embedding_retriever") is not None

@patch("query.service.load_pipeline")
def test_pipeline_yaml_loading(mock_load_pipeline, mock_document_store):
    mock_pipeline = Mock()
    mock_load_pipeline.return_value = mock_pipeline
    
    with patch("query.service.settings") as mock_settings:
        mock_settings.pipelines_from_yaml = True
        service = QueryService(document_store=mock_document_store)
        
        assert service.pipeline == mock_pipeline
        mock_load_pipeline.assert_called_once()

def test_search_with_no_results(query_service):
    mock_pipeline = Mock()
    mock_pipeline.run.return_value = {
        'answer_builder': {
            'answers': [
                GeneratedAnswer(
                    query="nonexistent query",
                    data="No relevant information found",
                    documents=[]
                )
            ]
        }
    }
    query_service.pipeline = mock_pipeline

    result = query_service.search("nonexistent query")
    assert isinstance(result, GeneratedAnswer)
    assert result.data == "No relevant information found"
    assert len(result.documents) == 0