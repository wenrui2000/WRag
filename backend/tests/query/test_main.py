import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from query.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_document_store():
    return Mock()

@pytest.fixture
def mock_initialize_document_store(mock_document_store):
    with patch('query.main.initialize_document_store', return_value=mock_document_store):
        yield mock_document_store

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_query_endpoint(client, mock_initialize_document_store):
    # Mock the query response
    mock_initialize_document_store.query.return_value = {
        "results": [
            {
                "content": "Test content",
                "score": 0.95,
                "metadata": {"source": "test.pdf"}
            }
        ]
    }

    # Test query endpoint
    response = client.post(
        "/query",
        json={"query": "test query", "filters": {"source": "test.pdf"}}
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["content"] == "Test content"
    assert data["results"][0]["score"] == 0.95
    assert data["results"][0]["metadata"]["source"] == "test.pdf"

def test_query_endpoint_validation(client):
    # Test empty query
    response = client.post("/query", json={"query": "", "filters": {}})
    assert response.status_code == 422

    # Test missing query field
    response = client.post("/query", json={"filters": {}})
    assert response.status_code == 422

def test_query_endpoint_error_handling(client, mock_initialize_document_store):
    # Mock an error in the document store
    mock_initialize_document_store.query.side_effect = Exception("Test error")

    response = client.post(
        "/query",
        json={"query": "test query", "filters": {}}
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error" 