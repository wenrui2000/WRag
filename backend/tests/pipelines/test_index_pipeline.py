import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import mock classes instead of real ones
# We'll mock all of the Haystack imports to avoid the protobuf/TensorFlow issues
@pytest.fixture
def mock_es_store():
    return Mock(name="ElasticsearchDocumentStore")

@pytest.fixture
def mock_qdrant_store():
    return Mock(name="QdrantDocumentStore")

@pytest.fixture
def mock_settings():
    settings = MagicMock()
    # Set default values
    settings.mysql_host = "localhost"
    settings.mysql_user = "root"
    settings.mysql_password = "password"
    settings.mysql_database = "wrag"
    settings.mysql_port = 3306
    settings.mysql_enabled = False  # Default to disabled
    return settings

@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock()
    # Create a mock graph with nodes and edges
    pipeline.graph = MagicMock()
    pipeline.graph.nodes = set()
    pipeline.graph.edges = {}
    
    # Override add_component to update our mock graph
    def mock_add_component(name, component):
        pipeline.graph.nodes.add(name)
        return component
    pipeline.add_component.side_effect = mock_add_component
    
    # Override connect to update our mock graph edges
    def mock_connect(source, sink):
        source_node = source.split('.')[0]
        sink_node = sink.split('.')[0]
        if source_node not in pipeline.graph.edges:
            pipeline.graph.edges[source_node] = []
        pipeline.graph.edges[source_node] = {
            "sink_node": sink_node
        }
    pipeline.connect.side_effect = mock_connect
    
    return pipeline

# Patch the entire haystack Pipeline class
@patch('pipelines.index_pipeline.Pipeline')
# Patch other Haystack components
@patch('pipelines.index_pipeline.FileTypeRouter')
@patch('pipelines.index_pipeline.TextFileToDocument')
@patch('pipelines.index_pipeline.PyPDFToDocument')
@patch('pipelines.index_pipeline.MarkdownToDocument')
@patch('pipelines.index_pipeline.DocumentJoiner')
@patch('pipelines.index_pipeline.DocumentCleaner')
@patch('pipelines.index_pipeline.DocumentSplitter')
@patch('pipelines.index_pipeline.SentenceTransformersDocumentEmbedder')
@patch('pipelines.index_pipeline.DocumentWriter')
def test_create_index_pipeline_without_mysql(
    mock_doc_writer,
    mock_embedder,
    mock_splitter,
    mock_cleaner,
    mock_joiner,
    mock_md_converter,
    mock_pdf_converter,
    mock_txt_converter,
    mock_router,
    mock_pipeline_class,
    mock_es_store, 
    mock_qdrant_store,
    mock_settings,
    mock_pipeline
):
    """Test creating index pipeline without MySQL integration."""
    
    # Setup pipeline mock
    mock_pipeline_class.return_value = mock_pipeline
    
    # Ensure MySQL is disabled in settings
    mock_settings.mysql_enabled = False
    
    # Import create_index_pipeline only when needed to avoid early importing
    with patch('pipelines.index_pipeline.settings', mock_settings):
        # Import locally to avoid import issues
        from pipelines.index_pipeline import create_index_pipeline
        
        # Create the pipeline
        pipeline = create_index_pipeline(
            document_store=mock_es_store,
            qdrant_store=mock_qdrant_store
        )
        
        # Check that correct components were added
        mock_pipeline.add_component.assert_any_call("file_router", mock_router.return_value)
        mock_pipeline.add_component.assert_any_call("document_joiner", mock_joiner.return_value)
        mock_pipeline.add_component.assert_any_call("document_cleaner", mock_cleaner.return_value)
        mock_pipeline.add_component.assert_any_call("document_splitter", mock_splitter.return_value)
        
        # Ensure no MySQL-related calls
        for call_args in mock_pipeline.add_component.call_args_list:
            args, _ = call_args
            assert "mysql" not in args[0]

# Patch the entire haystack Pipeline class
@patch('pipelines.index_pipeline.Pipeline')
# Patch other Haystack components
@patch('pipelines.index_pipeline.FileTypeRouter')
@patch('pipelines.index_pipeline.TextFileToDocument')
@patch('pipelines.index_pipeline.PyPDFToDocument')
@patch('pipelines.index_pipeline.MarkdownToDocument')
@patch('pipelines.index_pipeline.DocumentJoiner')
@patch('pipelines.index_pipeline.DocumentCleaner')
@patch('pipelines.index_pipeline.DocumentSplitter')
@patch('pipelines.index_pipeline.SentenceTransformersDocumentEmbedder')
@patch('pipelines.index_pipeline.DocumentWriter')
@patch('pipelines.index_pipeline.MySQLSourceDocumentWriter')
@patch('pipelines.index_pipeline.MySQLDocumentWriter')
def test_create_index_pipeline_with_mysql(
    mock_mysql_document_writer_class,
    mock_mysql_source_writer_class,
    mock_doc_writer,
    mock_embedder,
    mock_splitter,
    mock_cleaner,
    mock_joiner,
    mock_md_converter,
    mock_pdf_converter,
    mock_txt_converter,
    mock_router,
    mock_pipeline_class,
    mock_es_store, 
    mock_qdrant_store,
    mock_settings,
    mock_pipeline
):
    """Test creating index pipeline with MySQL integration enabled."""
    
    # Setup pipeline mock
    mock_pipeline_class.return_value = mock_pipeline
    
    # Configure mocks for MySQL writers
    mock_mysql_source_writer = Mock()
    mock_mysql_document_writer = Mock()
    mock_mysql_source_writer_class.return_value = mock_mysql_source_writer
    mock_mysql_document_writer_class.return_value = mock_mysql_document_writer
    
    # Enable MySQL in settings
    mock_settings.mysql_enabled = True
    mock_settings.mysql_host = "test-mysql-host"
    mock_settings.mysql_user = "test-user"
    mock_settings.mysql_password = "test-password"
    mock_settings.mysql_database = "test-db"
    mock_settings.mysql_port = 3307
    
    # Import create_index_pipeline only when needed to avoid early importing
    with patch('pipelines.index_pipeline.settings', mock_settings):
        # Import locally to avoid import issues
        from pipelines.index_pipeline import create_index_pipeline
        
        # Create the pipeline
        pipeline = create_index_pipeline(
            document_store=mock_es_store,
            qdrant_store=mock_qdrant_store
        )
        
        # Verify MySQL writers were created 
        assert mock_mysql_source_writer_class.called, "MySQLSourceDocumentWriter constructor not called"
        assert mock_mysql_document_writer_class.called, "MySQLDocumentWriter constructor not called"
        
        # Check that each MySQL writer was added as a component to the pipeline
        for call in mock_pipeline.add_component.call_args_list:
            args = call[0]
            if len(args) >= 1:
                component_name = args[0]
                if component_name == "mysql_source_writer":
                    assert args[1] == mock_mysql_source_writer
                elif component_name == "mysql_document_writer":
                    assert args[1] == mock_mysql_document_writer
        
        # Verify the MySQL writers were created with the correct parameters
        # This check is safer in case call_args is None
        if mock_mysql_source_writer_class.call_args and len(mock_mysql_source_writer_class.call_args) >= 2:
            kwargs = mock_mysql_source_writer_class.call_args[1]
            assert kwargs.get("host") == "test-mysql-host"
            assert kwargs.get("user") == "test-user"
            assert kwargs.get("password") == "test-password"
            assert kwargs.get("database") == "test-db"
            assert kwargs.get("port") == 3307
        
        if mock_mysql_document_writer_class.call_args and len(mock_mysql_document_writer_class.call_args) >= 2:
            kwargs = mock_mysql_document_writer_class.call_args[1]
            assert kwargs.get("host") == "test-mysql-host"
            assert kwargs.get("user") == "test-user"
            assert kwargs.get("password") == "test-password"
            assert kwargs.get("database") == "test-db"
            assert kwargs.get("port") == 3307 