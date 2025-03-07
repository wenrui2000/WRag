import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

# Add the src directory to the path if not already there
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from common.file_manager import FileManager
from common.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        file_storage_path=Path(tempfile.mkdtemp())
    )

@pytest.fixture
def temp_dir():
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Clean up temp directory after test
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)

@patch("common.file_manager.settings")
def test_file_manager_init_default(mock_settings_module, mock_settings):
    # Set up the mock settings
    mock_settings_module.file_storage_path = mock_settings.file_storage_path
    
    # Initialize file manager with default settings
    file_manager = FileManager()
    
    # Assert the file manager was initialized with correct path
    assert file_manager.path_to_files == mock_settings.file_storage_path
    assert file_manager.path_to_uploads == mock_settings.file_storage_path / "uploads"
    
    # Check that directories were created
    assert os.path.exists(file_manager.path_to_files)
    assert os.path.exists(file_manager.path_to_uploads)

def test_file_manager_init_with_path(temp_dir):
    # Initialize file manager with custom path
    file_manager = FileManager(temp_dir)
    
    # Assert the file manager was initialized with correct path
    assert file_manager.path_to_files == temp_dir
    assert file_manager.path_to_uploads == temp_dir / "uploads"
    
    # Check that directories were created
    assert os.path.exists(file_manager.path_to_files)
    assert os.path.exists(file_manager.path_to_uploads)

def test_file_manager_save_file(temp_dir):
    # Initialize file manager with custom path
    file_manager = FileManager(temp_dir)
    
    # Save a test file
    test_filename = "test_file.txt"
    test_content = b"This is a test file"
    file_path = file_manager.save_file(test_filename, test_content)
    
    # Check that the file was saved correctly
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        content = f.read()
        assert content == test_content
    
    # Check that the file was added to the lists
    assert test_filename in file_manager.files
    assert file_path in file_manager.file_paths 