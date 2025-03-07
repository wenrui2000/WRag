"""
Query Pipeline Builder Module

This module builds the query pipeline programmatically instead of using YAML
to avoid import and configuration issues.
"""
from haystack import Pipeline
from haystack.components.builders.answer_builder import AnswerBuilder
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.embedders.sentence_transformers_text_embedder import SentenceTransformersTextEmbedder
from haystack.components.joiners.document_joiner import DocumentJoiner

# Import from haystack_integrations namespace instead of direct integration packages
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchBM25Retriever
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.components.generators.ollama import OllamaGenerator

from common.config import settings
from common.document_store import initialize_document_store, get_qdrant_store

def create_query_pipeline(model: str = None):
    """
    Create and configure the query pipeline programmatically.
    
    Args:
        model (str, optional): The LLM model to use. If None, uses the default from settings.
    
    Returns:
        Pipeline: The configured Haystack pipeline
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Initialize components
    logger.info("Creating query pipeline components...")
    
    # 1. Create document stores
    es_document_store = initialize_document_store()
    qdrant_store = get_qdrant_store()
    
    # 2. Create retrievers
    bm25_retriever = ElasticsearchBM25Retriever(
        document_store=es_document_store,
        top_k=10,
        fuzziness="AUTO",
        filter_policy="replace"
    )
    
    # 3. Create query embedder
    query_embedder = SentenceTransformersTextEmbedder(
        model=settings.embedding_model,
        device=None
    )
    
    # 4. Create Qdrant retriever
    qdrant_retriever = QdrantEmbeddingRetriever(
        document_store=qdrant_store,
        top_k=5
    )
    
    # 5. Create document joiner for rank merging
    rank_merger = DocumentJoiner(
        weights=[0.5, 0.5],
        top_k=5
    )
    
    # 6. Create prompt builder
    prompt_builder = PromptBuilder(
        template="""
        Given the following context, answer the question.
        Context:
        {% for document in documents %}
            {{ document.content }}
        {% endfor %}
        Question: {{query}}
        Answer:
        """
    )
    
    # 7. Create LLM generator
    # Use the provided model if specified, otherwise use the default from settings
    llm_model = model if model else settings.ollama_model
    logger.info(f"Using LLM model: {llm_model}")
    
    llm = OllamaGenerator(
        model=llm_model,
        url=settings.ollama_api_url,
        generation_kwargs={
            "temperature": 0.7,
            "num_predict": 500  # num_predict is the Ollama equivalent of max_tokens
        }
    )
    
    # 8. Create answer builder
    answer_builder = AnswerBuilder()
    
    # Add all components to pipeline
    logger.info("Adding components to pipeline...")
    pipeline.add_component("bm25_retriever", bm25_retriever)
    pipeline.add_component("query_embedder", query_embedder)
    pipeline.add_component("qdrant_retriever", qdrant_retriever)
    pipeline.add_component("rank_merger", rank_merger)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("llm", llm)
    pipeline.add_component("answer_builder", answer_builder)
    
    # Connect components - without using direct 'query' connections
    logger.info("Connecting pipeline components...")
    
    # Connect embedder to retriever
    pipeline.connect("query_embedder.embedding", "qdrant_retriever.query_embedding")
    
    # Connect retrievers to merger
    pipeline.connect("bm25_retriever.documents", "rank_merger.documents")
    pipeline.connect("qdrant_retriever.documents", "rank_merger.documents")
    
    # Connect to prompt builder
    pipeline.connect("rank_merger.documents", "prompt_builder.documents")
    
    # Connect to LLM and answer builder
    pipeline.connect("prompt_builder.prompt", "llm.prompt")
    pipeline.connect("rank_merger.documents", "answer_builder.documents")
    pipeline.connect("llm.replies", "answer_builder.replies")
    pipeline.connect("llm.meta", "answer_builder.meta")
    
    # Note: The 'query' parameter for answer_builder must be provided directly in the pipeline inputs
    # It cannot be connected through other components since none provide query as an output
    
    # Debug: Print all connections
    logger.info("Pipeline connections established.")
    
    return pipeline 