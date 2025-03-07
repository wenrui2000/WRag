from pathlib import Path
import sys
import os
from typing import Dict

from contextlib import asynccontextmanager
import logging
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from common.api_utils import create_api
from common.models import FilesUploadResponse, FilesListResponse
from common.document_store import initialize_document_store, get_qdrant_store
from common.config import settings
from indexing.service import IndexingService
from utils.tracing import instrument_fastapi, patch_haystack_tracing
from utils.metrics import instrument_fastapi_with_metrics, setup_metrics, create_counter, create_histogram


logging.basicConfig(
    format="%(levelname)s - %(name)s - [%(process)d] - %(message)s",
    level=settings.log_level
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Set Haystack logger to INFO level
logging.getLogger("haystack").setLevel(settings.haystack_log_level)

# Create a single instance of IndexingService
indexing_service = IndexingService(
    document_store=initialize_document_store(),
    qdrant_store=get_qdrant_store(),
    embedder_model=settings.embedding_model,
    split_by=settings.split_by,
    split_length=settings.split_length,
    split_overlap=settings.split_overlap,
    respect_sentence_boundary=getattr(settings, "respect_sentence_boundary", True),
    split_threshold=getattr(settings, "split_threshold", 10),
    language=getattr(settings, "language", "en")
)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add OpenTelemetry tracing if enabled
if settings.tracing_enabled:
    instrument_fastapi(app, "indexing_service")
    # Also ensure Haystack tracing integration is patched
    patch_haystack_tracing()

# Add Prometheus metrics if enabled
if hasattr(settings, 'metrics_enabled') and settings.metrics_enabled:
    instrument_fastapi_with_metrics(app, "indexing_service")
    # Create some basic metrics
    upload_counter = create_counter(
        name="indexing_file_uploads_total",
        description="Number of files uploaded for indexing",
        labels=["operation"]
    )
    index_counter = create_counter(
        name="indexing_operations_total",
        description="Number of indexing operations performed",
        labels=["operation"]
    )
    upload_latency = create_histogram(
        name="indexing_file_upload_latency_seconds",
        description="Latency of file upload and indexing operations in seconds",
        labels=["file_type"],
        buckets=[1, 5, 10, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
    )
    # Initialize component metrics
    setup_metrics("indexing_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    # Index all files on startup
    if settings.index_on_startup and indexing_service.index_files():
        logger.info("Indexing completed successfully")

    yield
    # Shutdown
    logger.info("Shutting down")
    # Add any cleanup code here if needed

def get_indexing_service():
    if indexing_service.pipeline is None:
        raise HTTPException(status_code=500, detail="IndexingService not initialized")
    return indexing_service

@app.post("/files", response_model=List[FilesUploadResponse])
async def upload_files(
    files: List[UploadFile] = File(...),
    service: IndexingService = Depends(get_indexing_service)
) -> JSONResponse:
    """
    Upload and index multiple files to both Elasticsearch and Qdrant.

    This endpoint allows uploading multiple files simultaneously. Each file is saved and indexed 
    to both Elasticsearch (for full-text search) and Qdrant (for embedding-based search).

    Parameters:
    - files (List[UploadFile]): A list of files to be uploaded and indexed.

    Returns:
    - JSONResponse: A list of FilesUploadResponse objects, one for each uploaded file.
      Each response includes the file_id (filename) and status ("success" or "failed").
      If a file upload fails, an error message is included.

    Raises:
    - HTTPException(400): If no files are provided.
    - HTTPException(500): If the IndexingService is not initialized.

    The response status code is 200 if all files are uploaded successfully, or 500 if any file upload fails.
    """
    if not files:
        logger.info("No files uploaded")
        raise HTTPException(status_code=400, detail="No files uploaded")

    logger.info(f"Uploading {len(files)} files...")

    responses = []
    all_successful = True
    total_files = 0
    
    for file in files:
        try:
            # Start timing the upload operation for metrics
            import time
            start_time = time.time()
            
            # Use the index_file method, which already handles saving and indexing
            result = await service.index_file(file)
            
            # Get file type for metrics labeling
            file_type = "unknown"
            if file.filename:
                file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"
                if file_ext in ["pdf"]:
                    file_type = "pdf"
                elif file_ext in ["txt", "text"]:
                    file_type = "text"
                elif file_ext in ["md", "markdown"]:
                    file_type = "markdown"
                
            # Record upload latency if metrics are enabled
            if hasattr(settings, 'metrics_enabled') and settings.metrics_enabled and upload_latency:
                latency_seconds = (time.time() - start_time)  # Time in seconds
                upload_latency.labels(file_type=file_type).observe(latency_seconds)
                
            total_files += 1
            
            if result["success"]:
                logger.info(f"File uploaded and indexed successfully: {result['file_path']} - ES: {result['es_document_count']} documents, Qdrant: {result['qdrant_document_count']} documents indexed")
                responses.append(FilesUploadResponse(file_id=file.filename, status="success"))
            else:
                all_successful = False
                logger.error(f"Error indexing file {file.filename}: {result.get('error', 'Unknown error')}")
                responses.append(FilesUploadResponse(
                    file_id=file.filename, 
                    status="failed", 
                    error=result.get('error', 'Unknown error')
                ))
                
        except Exception as e:
            all_successful = False
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            responses.append(
                FilesUploadResponse(file_id=file.filename, status="failed", error=str(e))
            )

    # Record metrics for file uploads if enabled
    if hasattr(settings, 'metrics_enabled') and settings.metrics_enabled and upload_counter:
        upload_counter.labels(operation="upload").inc(total_files)

    status_code = 200 if all_successful else 500
    return JSONResponse(content=[response.dict() for response in responses], status_code=status_code)

@app.get("/files", response_model=FilesListResponse)
async def get_files(
    service: IndexingService = Depends(get_indexing_service)
) -> FilesListResponse:
    """
    Retrieve a list of all indexed files.

    This endpoint rescans the files directory and returns an updated list of all indexed files.

    Returns:
    - FilesListResponse: An object containing a list of file information.
      Each file entry typically includes details such as filename, path, and any other relevant metadata.

    Raises:
    - HTTPException(500): If the IndexingService is not initialized.

    The files list is updated each time this endpoint is called, ensuring the returned information is current.
    """
    files = service.rescan_files_and_paths()

    logger.info(f"Found files {files}")
    return FilesListResponse(files=files)

@app.get("/health")
async def health_check():
    """
    Health check endpoint with explicit trace generation for testing.
    """
    logger.info("Health check requested - attempting to generate traces")
    
    # Generate an explicit trace for testing
    if settings.tracing_enabled:
        try:
            from opentelemetry import trace
            
            # Get current tracer
            tracer = trace.get_tracer("indexing_service")
            logger.info(f"Got tracer: {tracer}")
            
            # Create a span using the tracer
            with tracer.start_as_current_span("health_check") as span:
                span.set_attribute("service.name", "indexing_service")
                span.set_attribute("operation.type", "health_check")
                span.add_event("Health check started")
                
                # Simulate some work
                import time
                time.sleep(0.1)
                
                # Create a nested span
                with tracer.start_as_current_span("database_check") as child_span:
                    child_span.set_attribute("database", "health_verification")
                    time.sleep(0.05)
                    child_span.add_event("Database check completed")
                
                # Finalize the parent span
                span.add_event("Health check completed")
                logger.info("Health check trace completed")
            
            # Check if Haystack tracing is enabled rather than trying to get a tracer
            import haystack.tracing
            tracing_enabled = haystack.tracing.is_tracing_enabled()
            logger.info(f"Haystack tracing enabled: {tracing_enabled}")
            
            # If Haystack tracing is enabled, create an OpenTelemetry span for Haystack
            if tracing_enabled:
                # Use OpenTelemetry directly instead of trying to access Haystack's tracer
                with tracer.start_as_current_span("haystack_integration_test") as hs_span:
                    hs_span.set_attribute("component", "haystack")
                    hs_span.set_attribute("test_type", "integration")
                    logger.info("Created span for Haystack integration test using OpenTelemetry")
        except Exception as e:
            logger.error(f"Error generating traces: {e}")
    else:
        logger.info("Tracing is disabled")
    
    return {"status": "ok", "service": "indexing_service", "trace_test": "completed"}

@app.post("/index")
async def index_file(file: UploadFile) -> Dict:
    """
    Upload and immediately index a file.
    
    This endpoint processes and indexes the uploaded file to both document stores:
    - Elasticsearch for full-text search
    - Qdrant for embedding-based semantic search
    
    Only PDF and Markdown files are supported.
    """
    try:
        # Start timing the indexing operation for metrics
        import time
        start_time = time.time()
        
        # Get file type for metrics labeling
        file_type = "unknown"
        if file.filename:
            file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"
            if file_ext in ["pdf"]:
                file_type = "pdf"
            elif file_ext in ["txt", "text"]:
                file_type = "text"
            elif file_ext in ["md", "markdown"]:
                file_type = "markdown"
        
        # Process file
        result = await indexing_service.index_file(file)
        
        # Record metrics for indexing if enabled
        if hasattr(settings, 'metrics_enabled') and settings.metrics_enabled:
            if index_counter:
                index_counter.labels(operation="index").inc()
            
            if upload_latency:
                latency_seconds = (time.time() - start_time)
                upload_latency.labels(file_type=file_type).observe(latency_seconds)
        
        return {
            "message": "File indexed successfully to Elasticsearch and Qdrant",
            "indexed_count": result["indexed_documents"],
            "es_document_count": result["es_document_count"],
            "qdrant_document_count": result["qdrant_document_count"]
        }
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
