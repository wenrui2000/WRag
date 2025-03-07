import os
import uuid
from typing import List

from haystack.dataclasses import GeneratedAnswer, Document
from common.models import (
    QueryResultsResponse,
    ResultModel,
    AnswerModel,
    DocumentModel,
    FileModel
)


def serialize_query_result(query: str, answer: GeneratedAnswer) -> QueryResultsResponse:
    query_id = uuid.uuid4().hex[:8]
    
    result = ResultModel(
        query_id=query_id,
        query=query,
        answers=[serialize_answer(answer)],
        documents=[serialize_document(doc) for doc in answer.documents]
    )

    return QueryResultsResponse(query_id=query_id, results=[result])

def serialize_answer(answer: GeneratedAnswer) -> AnswerModel:
    return AnswerModel(
        answer=answer.data,
        type="generative",
        document_ids=[doc.id for doc in answer.documents],
        meta={"_references": []},
        file=serialize_file(answer.documents[0] if answer.documents else None)
    )

def serialize_document(doc: Document) -> DocumentModel:
    return DocumentModel(
        id=str(doc.id),
        content=doc.content,
        content_type="text",
        meta={
            "file_name": doc.meta.get("file_name") or os.path.basename(doc.meta.get("file_path", "")),
            "split_idx_start": doc.meta.get("split_idx_start"),
        },
        score=doc.score
    )

def serialize_file(doc: Document | None) -> FileModel:
    if not doc:
        return FileModel(id="", name="")
    return FileModel(
        id="",
        name=os.path.basename(doc.meta.get("file_path", ""))
    )
