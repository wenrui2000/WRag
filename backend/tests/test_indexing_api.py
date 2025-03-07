from pathlib import Path
import sys
import os

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from indexing.main import app, get_indexing_service
from indexing.service import IndexingService
from common.models import SearchQuery, SearchResponse


client = TestClient(app)

@pytest.fixture
def mock_indexing_service():
    with patch("indexing.main.indexing_service") as mock:
        yield mock

# Test /files upload
def test_upload_files(mock_indexing_service):
    app.dependency_overrides[get_indexing_service] = lambda: mock_indexing_service
    mock_indexing_service.save_uploaded_file.return_value = "/path/to/files/test_file.txt"

    with open("test_file.txt", "w") as f:
        f.write("Test content")

    with open("test_file.txt", "rb") as f:
        response = client.post("/files", files={"files": ("test_file.txt", f)})

    assert response.status_code == 200
    assert response.json() == [{"file_id": "test_file.txt", "status": "success", "error": None}]
    mock_indexing_service.save_uploaded_file.assert_called_once_with("test_file.txt", b"Test content")
    app.dependency_overrides.clear()
    # Clean up the test file
    os.remove("test_file.txt")

# Test /files get
def test_get_files(mock_indexing_service):
    app.dependency_overrides[get_indexing_service] = lambda: mock_indexing_service
    mock_indexing_service.rescan_files_and_paths.return_value = ["file1.txt", "file2.txt"]

    response = client.get("/files")
    assert response.status_code == 200
    assert response.json() == {"files": ["file1.txt", "file2.txt"]}
    mock_indexing_service.rescan_files_and_paths.assert_called_once()
    app.dependency_overrides.clear()

# Test /
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "documentation" in response.json()

# Test /health
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
