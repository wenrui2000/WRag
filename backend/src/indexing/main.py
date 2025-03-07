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
    
    for file in files:
        try:
            # Use the index_file method, which already handles saving and indexing
            result = await service.index_file(file)
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
    return {"status": "ok"}

@app.post("/index")
async def index_file(file: UploadFile) -> Dict:
    """
    Index a single file to both Elasticsearch and Qdrant.
    
    This endpoint processes and indexes the uploaded file to both document stores:
    - Elasticsearch for full-text search
    - Qdrant for embedding-based semantic search
    
    Only PDF and Markdown files are supported.
    """
    if not file.content_type in ["application/pdf", "text/markdown", "text/plain"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDF, Markdown, and text files are supported."
        )
    
    try:
        result = await indexing_service.index_file(file)
        if result["success"]:
            return {
                "message": "File indexed successfully to Elasticsearch and Qdrant",
                "indexed_count": result["indexed_documents"],
                "es_document_count": result["es_document_count"],
                "qdrant_document_count": result["qdrant_document_count"]
            }
        else:
            raise HTTPException(status_code=500, detail=f"Error indexing file: {result.get('error', 'Unknown error')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
