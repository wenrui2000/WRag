from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID


class SearchQuery(BaseModel):
    query: str = Field(..., description="The search query string")
    filters: Optional[dict] = Field(None, description="Optional filters for the search")
    model: Optional[str] = Field(None, description="LLM model to use for query")


class SearchResponse(BaseModel):
    results: List[str] = Field(..., description="List of search results")
    error: Optional[str] = Field(None, description="Error message if search failed")


class FilesUploadResponse(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    status: str = Field(..., description="Status of the upload (e.g., 'success', 'failed')")
    error: Optional[str] = Field(None, description="Error message if upload failed")


class FilesListResponse(BaseModel):
    files: List[str] = Field(..., description="List of indexed files")


class FilesIndexResponse(BaseModel):
    status: str
    message: str
    error: Optional[str] = Field(None, description="Error message if indexing failed")


class FileModel(BaseModel):
    id: str
    name: str


class DocumentModel(BaseModel):
    id: str
    content: str
    content_type: str
    meta: Dict[str, str | int]
    score: Optional[float] = None


class AnswerModel(BaseModel):
    answer: str
    type: str
    document_ids: List[str]
    meta: Dict[str, List]
    file: FileModel


class ResultModel(BaseModel):
    query_id: str
    query: str
    answers: List[AnswerModel]
    documents: List[DocumentModel]


class QueryResultsResponse(BaseModel):
    query_id: str
    results: List[ResultModel]
