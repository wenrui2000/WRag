from pathlib import Path
import sys

from dataclasses import dataclass
import logging
from typing import Optional

from haystack import Pipeline
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.joiners import DocumentJoiner
from haystack.components.builders import PromptBuilder
from haystack.components.builders.answer_builder import AnswerBuilder

# Import from haystack_integrations namespace as requested
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchBM25Retriever
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.components.generators.ollama import OllamaGenerator

# No fallback needed as we're using haystack_integrations directly
USING_DIRECT_IMPORTS = False

from common.config import settings
from common.document_store import get_qdrant_store

# Import our code-defined pipeline
from pipelines.query_pipeline import create_query_pipeline


logger = logging.getLogger(__name__)

@dataclass
class QueryConfig:
    document_store: ElasticsearchDocumentStore
    qdrant_store: QdrantDocumentStore
    embedder_model: str = "intfloat/multilingual-e5-base"
    prompt_template: str = """
    Given the following context, answer the question.
    Context:
    {% for document in documents %}
        {{ document.content }}
    {% endfor %}
    Question: {{query}}
    Answer:
    """

class QueryService:
    def __init__(self, document_store):
        self.document_store = document_store
        self.qdrant_store = get_qdrant_store()
        
        # Initialize default pipeline using the single pipeline creation function
        logger.info("Creating default pipeline from code")
        try:
            self.pipeline = create_query_pipeline()
            # Store pipelines for each model to avoid recreating them for each request
            self.model_pipelines = {}
        except Exception as e:
            logger.error(f"Failed to create pipeline: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_pipeline_for_model(self, model: Optional[str] = None):
        """
        Get or create a pipeline for the specified model.
        
        Args:
            model (str, optional): The model to use. If None, uses the default pipeline.
            
        Returns:
            Pipeline: The pipeline for the specified model
        """
        if not model:
            return self.pipeline
            
        # Check if we already have a pipeline for this model
        if model in self.model_pipelines:
            return self.model_pipelines[model]
            
        # Create a new pipeline for this model
        logger.info(f"Creating new pipeline for model: {model}")
        try:
            pipeline = create_query_pipeline(model)
            self.model_pipelines[model] = pipeline
            return pipeline
        except Exception as e:
            logger.error(f"Failed to create pipeline for model {model}: {e}")
            # Fallback to default pipeline
            logger.info("Falling back to default pipeline")
            return self.pipeline

    def search(self, query: str, filters: Optional[dict] = None, model: Optional[str] = None):
        logger.info(f"Searching for: {query} with model: {model}")
        try:
            # Get the appropriate pipeline for this model
            pipeline = self.get_pipeline_for_model(model)
            
            # Create inputs for each component that needs the query
            inputs = {
                "query_embedder": {"text": query},
                "bm25_retriever": {"query": query},
                "prompt_builder": {"query": query},
                "answer_builder": {"query": query}
            }
            
            # Debug logging
            logger.info(f"Running pipeline with inputs: {inputs}")
            
            # Run the pipeline with component-specific inputs
            results = pipeline.run(inputs)
            
            logger.info(f"Pipeline completed successfully with keys: {results.keys()}")
            
            # Handle the case where answer_builder might not exist
            if "answer_builder" in results and "answers" in results["answer_builder"]:
                return results["answer_builder"]["answers"][0]
            else:
                logger.warning(f"Unexpected result structure: {results.keys()}")
                return None
                
        except Exception as e:
            logger.error(f"Error during search: {e}")
            # Log more details about the error
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
