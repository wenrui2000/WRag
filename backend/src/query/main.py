from pathlib import Path
import sys

from contextlib import asynccontextmanager
import json
import logging
from typing import List
import uuid

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

from common.api_utils import create_api
from common.models import SearchQuery, QueryResultsResponse
from common.document_store import initialize_document_store
from common.config import settings, OllamaModel
from query.service import QueryService
from query.serializer import serialize_query_result
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

# Create a single instance of QueryService
document_store = initialize_document_store()
query_service = QueryService(document_store)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    yield
    # Shutdown
    logger.info("Shutting down")
    # Add any cleanup code here if needed

app = create_api(title="RAG Query Service", lifespan=lifespan)

# Add OpenTelemetry tracing if enabled
if settings.tracing_enabled:
    instrument_fastapi(app, "query_service")
    # Also ensure Haystack tracing integration is patched
    patch_haystack_tracing()

# Add Prometheus metrics if enabled
if hasattr(settings, 'metrics_enabled') and settings.metrics_enabled:
    instrument_fastapi_with_metrics(app, "query_service")
    # Create some basic metrics
    search_counter = create_counter(
        name="query_search_requests_total",
        description="Number of search requests processed",
        labels=["query_type"]
    )
    search_latency = create_histogram(
        name="query_search_latency_milliseconds",
        description="Latency of search operations in milliseconds",
        labels=["query_type"]
    )
    # Initialize component metrics
    setup_metrics("query_service")

def get_query_service():
    if query_service.pipeline is None:
        raise HTTPException(status_code=500, detail="QueryService not initialized")
    return query_service

@app.post("/search", response_model=QueryResultsResponse)
async def search(
    query: SearchQuery,
    service: QueryService = Depends(get_query_service)
) -> QueryResultsResponse:
    """
    Perform a search based on the provided query and filters.

    Parameters:
    - query (SearchQuery): The search query object containing the query string, filters, and optional model.
    - service (QueryService): The query service instance (automatically injected).

    Returns:
    - SearchResponse: The search results containing a list of replies and any error information.

    Raises:
    - HTTPException: If an error occurs during the search process.

    Description:
    This endpoint accepts a POST request with a SearchQuery object and returns search results.
    It uses the QueryService to perform the search based on the provided query, filters, and model.
    If successful, it returns a SearchResponse with the results. If an error occurs, it logs
    the error and raises an HTTPException with a 500 status code.
    """
    try:
        # Start timing the search operation for metrics
        import time
        start_time = time.time()
        
        # Process the search request
        results = service.search(
            query=query.query,
            filters=query.filters,
            model=query.model
        )
        
        # Record metrics if enabled
        if hasattr(settings, 'metrics_enabled') and settings.metrics_enabled:
            if search_counter:
                search_counter.labels(query_type="search").inc()
            
            if search_latency:
                # Calculate latency in milliseconds
                latency_ms = (time.time() - start_time) * 1000
                search_latency.labels(query_type="search").observe(latency_ms)
        
        # Process and return the results
        return serialize_query_result(query.query, results)
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

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
            tracer = trace.get_tracer("query_service")
            logger.info(f"Got tracer: {tracer}")
            
            # Create a span using the tracer
            with tracer.start_as_current_span("health_check") as span:
                span.set_attribute("service.name", "query_service")
                span.set_attribute("operation.type", "health_check")
                span.add_event("Health check started")
                
                # Simulate some work
                import time
                time.sleep(0.1)
                
                # Create a nested span
                with tracer.start_as_current_span("query_engine_check") as child_span:
                    child_span.set_attribute("component", "query_engine")
                    time.sleep(0.05)
                    child_span.add_event("Query engine check completed")
                
                # Finalize the parent span
                span.add_event("Health check completed")
                logger.info("Health check trace completed")
            
            # Try to trigger a haystack trace via the direct API
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
    
    return {"status": "ok", "service": "query_service", "trace_test": "completed"}

@app.get("/available-models")
async def get_available_models():
    """
    Get the list of available LLM models.
    
    Returns:
        List[dict]: A list of model dictionaries with id and name keys
    """
    models = [{"id": model.value} 
              for model in OllamaModel]
    
    return {"models": models}

# Add another route with the same handler for the frontend path
@app.get("/api/available-models")
async def get_available_models_api():
    """
    Alternate endpoint for getting the list of available LLM models.
    This endpoint is provided for compatibility with the frontend.
    
    Returns:
        List[dict]: A list of model dictionaries with id and name keys
    """
    return get_available_models()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
