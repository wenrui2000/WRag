import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json

# Create a mock Document class to avoid importing Haystack
class MockDocument:
    def __init__(self, id, content=None, embedding=None, meta=None):
        self.id = id
        self.content = content
        self.embedding = embedding
        self.meta = meta or {}

# Now import our MySQL writer classes
from indexing.mysql_document_writer import MySQLDocumentWriter, MySQLSourceDocumentWriter

@pytest.fixture
def mock_mysql_connection():
    """Create a mock MySQL connection and cursor."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    return mock_conn, mock_cursor

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        MockDocument(
            id="doc1",
            content="This is document 1",
            meta={"source_id": "source1", "file_path": "/path/to/file1.txt"}
        ),
        MockDocument(
            id="doc2",
            content="This is document 2",
            meta={"source_id": "source2", "file_path": "/path/to/file2.txt"}
        )
    ]

class TestMySQLDocumentWriter:
    """Tests for the MySQLDocumentWriter class."""
    
    @patch('mysql.connector.connect')
    def test_initialization(self, mock_connect):
        """Test that the writer initializes correctly."""
        writer = MySQLDocumentWriter(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db",
            port=3307
        )
        
        assert writer.host == "test-host"
        assert writer.user == "test-user"
        assert writer.password == "test-pass"
        assert writer.database == "test-db"
        assert writer.port == 3307
        assert writer.conn is None
    
    @patch('mysql.connector.connect')
    def test_get_connection(self, mock_connect):
        """Test that the connection is created properly."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        writer = MySQLDocumentWriter(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db",
            port=3307
        )
        
        conn = writer._get_connection()
        
        assert conn == mock_conn
        mock_connect.assert_called_once_with(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db",
            port=3307
        )
    
    def test_run_with_empty_documents(self):
        """Test that run returns empty list when no documents provided."""
        writer = MySQLDocumentWriter(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db"
        )
        
        result = writer.run(documents=[])
        
        assert result == {"written_documents": []}
    
    def test_run_with_documents(self, mock_mysql_connection, sample_documents):
        """Test run method with sample documents."""
        mock_conn, mock_cursor = mock_mysql_connection
        
        writer = MySQLDocumentWriter(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db"
        )
        
        # Mock _get_connection to return our mock
        writer._get_connection = Mock(return_value=mock_conn)
        
        result = writer.run(documents=sample_documents)
        
        # Verify cursor was called correctly
        assert mock_cursor.execute.call_count == 2
        
        # Check that the query included the right parameters
        expected_args = [
            (
                "doc1",
                "source1",
                json.dumps({"source_id": "source1", "file_path": "/path/to/file1.txt"})
            ),
            (
                "doc2",
                "source2",
                json.dumps({"source_id": "source2", "file_path": "/path/to/file2.txt"})
            )
        ]
        
        # Verify each call to execute
        for i, doc in enumerate(sample_documents):
            args = mock_cursor.execute.call_args_list[i][0][1]
            assert args[0] == doc.id
            assert args[1] == doc.meta["source_id"]
            assert json.loads(args[2]) == doc.meta
        
        # Verify connection was committed and cursor closed
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        
        # Verify written documents returned
        assert result["written_documents"] == sample_documents
    
    def test_close(self, mock_mysql_connection):
        """Test close method."""
        mock_conn, _ = mock_mysql_connection
        
        writer = MySQLDocumentWriter(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db"
        )
        
        writer.conn = mock_conn
        writer.close()
        
        mock_conn.close.assert_called_once()


class TestMySQLSourceDocumentWriter:
    """Tests for the MySQLSourceDocumentWriter class."""
    
    @patch('mysql.connector.connect')
    def test_initialization(self, mock_connect):
        """Test that the writer initializes correctly."""
        writer = MySQLSourceDocumentWriter(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db",
            port=3307
        )
        
        assert writer.host == "test-host"
        assert writer.user == "test-user"
        assert writer.password == "test-pass"
        assert writer.database == "test-db"
        assert writer.port == 3307
        assert writer.conn is None
    
    def test_run_with_documents(self, mock_mysql_connection, sample_documents):
        """Test run method with sample documents."""
        mock_conn, mock_cursor = mock_mysql_connection
        
        writer = MySQLSourceDocumentWriter(
            host="test-host",
            user="test-user",
            password="test-pass",
            database="test-db"
        )
        
        # Mock _get_connection to return our mock
        writer._get_connection = Mock(return_value=mock_conn)
        
        result = writer.run(documents=sample_documents)
        
        # Verify cursor was called correctly
        assert mock_cursor.execute.call_count == 2
        
        # Check that the execute calls included the right parameters
        for i, doc in enumerate(sample_documents):
            args = mock_cursor.execute.call_args_list[i][0][1]
            assert args[0] == doc.id
            assert args[1] == doc.content
            assert args[2] == doc.meta.get("file_path")
            assert json.loads(args[3]) == doc.meta
        
        # Verify connection was committed and cursor closed
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        
        # Verify written documents returned
        assert result["written_documents"] == sample_documents 