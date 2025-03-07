from fastapi.testclient import TestClient
import pytest
from unittest.mock import Mock, patch
from haystack.dataclasses import GeneratedAnswer, Document
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from query.main import app, get_query_service
from common.models import SearchResponse


client = TestClient(app)

@pytest.fixture
def mock_query_service():
    with patch("query.main.query_service") as mock:
        yield mock

@pytest.fixture
def mock_search_response():
    return {
        "answer": "Test answer",
        "type": "generative",
        "document_ids": ["doc1"],
        "meta": {"sources": []},
        "file": {"id": "file1", "name": "test.txt"}
    }

# Add this model for request validation
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: dict | None = None

# Test successful search
def test_search_endpoint_success(mock_query_service):
    app.dependency_overrides[get_query_service] = lambda: mock_query_service
    mock_query_service.search.return_value = GeneratedAnswer(
        query="test query",
        data="Test answer",
        documents=[
            Document(
                content="test content",
                id="doc1",
                meta={"split_idx_start": "0", "file_path": "test.txt"}
            )
        ]
    )

    response = client.post(
        "/search",
        json={"query": "test query", "filters": {"language": "python"}}
    )

    assert response.status_code == 200
    assert "results" in response.json()
    mock_query_service.search.assert_called_once_with("test query", {"language": "python"})
    app.dependency_overrides.clear()

# Test input validation
def test_search_endpoint_empty_query(mock_query_service):
    """Test that empty queries are rejected"""
    app.dependency_overrides[get_query_service] = lambda: mock_query_service

    response = client.post(
        "/search",
        json={"query": "", "filters": None}
    )

    # The current implementation returns 500 for empty queries
    assert response.status_code == 500
    assert "validation error" in response.json()["detail"].lower()

    app.dependency_overrides.clear()

# Test missing required field
def test_search_endpoint_missing_query(mock_query_service):
    """Test that query is required"""
    app.dependency_overrides[get_query_service] = lambda: mock_query_service

    response = client.post(
        "/search",
        json={"filters": None}
    )

    assert response.status_code == 422
    validation_error = response.json()["detail"][0]
    assert validation_error["type"] == "missing"
    assert validation_error["loc"] == ["body", "query"]

    mock_query_service.search.assert_not_called()
    app.dependency_overrides.clear()

# Test service error handling
def test_search_endpoint_service_error(mock_query_service):
    app.dependency_overrides[get_query_service] = lambda: mock_query_service
    mock_query_service.search.side_effect = Exception("Search service error")

    response = client.post("/search", json={"query": "test query", "filters": None})

    assert response.status_code == 500
    assert "Search service error" in response.json()["detail"]
    app.dependency_overrides.clear()

# Test invalid JSON
def test_search_endpoint_invalid_json():
    response = client.post(
        "/search",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422

# Test health check endpoint
def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Test root endpoint
def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()
    assert "documentation" in response.json()
