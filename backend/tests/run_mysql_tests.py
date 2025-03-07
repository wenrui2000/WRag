#!/usr/bin/env python
"""
Run MySQL-related unit tests.
"""
import sys
import os
import pytest

def set_environment_variables():
    """Set environment variables that help avoid import issues."""
    # Avoid TensorFlow warnings on machines without GPU
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    # Fix protobuf version issues by using Python implementation
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

if __name__ == '__main__':
    # Set environment variables
    set_environment_variables()
    
    # Add src directory to path
    sys.path.append('src')
    
    print("Running MySQL writer tests...")
    print("Note: We're using selective imports and mocking to avoid dependency issues")
    
    try:
        # Start with the MySQL document writer tests which don't need Haystack imports
        mysql_writer_result = pytest.main([
            'tests/indexing/test_mysql_document_writer.py',
            '-v'
        ])
        
        if mysql_writer_result != 0:
            print("MySQL document writer tests failed! Fix these issues first.")
            sys.exit(mysql_writer_result)
        
        # Now run the pipeline tests with heavy mocking
        pipeline_result = pytest.main([
            'tests/pipelines/test_index_pipeline.py',
            '-v'
        ])
        
        # Return the combined result
        if pipeline_result != 0:
            sys.exit(pipeline_result)
            
        print("\n✅ All MySQL tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        sys.exit(1) 