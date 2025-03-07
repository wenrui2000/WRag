import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, mock_open
from indexing.main import app
import io

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_document_store():
    return Mock()

@pytest.fixture
def mock_initialize_document_store(mock_document_store):
    with patch('indexing.main.initialize_document_store', return_value=mock_document_store):
        yield mock_document_store

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_index_file(client, mock_initialize_document_store):
    # Create a mock PDF file
    test_file_content = b"test PDF content"
    test_file = io.BytesIO(test_file_content)
    
    # Mock successful indexing
    mock_initialize_document_store.index.return_value = {"indexed": 1}

    # Test file upload endpoint
    response = client.post(
        "/index",
        files={"file": ("test.pdf", test_file, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "File indexed successfully"
    assert data["indexed_count"] == 1

def test_index_invalid_file_type(client):
    # Test with invalid file type
    test_file = io.BytesIO(b"test content")
    response = client.post(
        "/index",
        files={"file": ("test.txt", test_file, "text/plain")}
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_index_file_error_handling(client, mock_initialize_document_store):
    # Mock an error during indexing
    mock_initialize_document_store.index.side_effect = Exception("Indexing error")

    # Test error handling
    test_file = io.BytesIO(b"test PDF content")
    response = client.post(
        "/index",
        files={"file": ("test.pdf", test_file, "application/pdf")}
    )

    assert response.status_code == 500
    assert "Error indexing file" in response.json()["detail"]

@patch('indexing.main.os.path.exists')
@patch('indexing.main.os.makedirs')
def test_file_storage(mock_makedirs, mock_exists, client, mock_initialize_document_store):
    mock_exists.return_value = False
    test_file = io.BytesIO(b"test PDF content")
    
    with patch('builtins.open', mock_open()) as mock_file:
        response = client.post(
            "/index",
            files={"file": ("test.pdf", test_file, "application/pdf")}
        )
        
        assert response.status_code == 200
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once() 