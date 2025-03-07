"""
OpenTelemetry tracing configuration with Jaeger exporter.
"""
import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.haystack import HaystackInstrumentor
from opentelemetry.semconv.resource import ResourceAttributes
import functools

from common.config import settings

# Create a logger for this module
logger = logging.getLogger(__name__)

def setup_tracer(service_name):
    """
    Configure OpenTelemetry with OTLP exporter.
    
    Args:
        service_name: Name of the service (e.g., 'indexing_service', 'query_service')
    
    Returns:
        tracer: An OpenTelemetry tracer object
    """
    # If tracing is not enabled, return a no-op tracer
    if not settings.tracing_enabled:
        return trace.get_tracer(service_name)
    
    try:
        logger.info(f"Setting up OpenTelemetry tracing for {service_name}")
        
        # Set environment variables for OpenTelemetry
        os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"service.name={service_name}"
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"http://{settings.jaeger_host}:4318"
        os.environ["OTEL_TRACES_SAMPLER"] = "always_on"
        
        # Create a resource to identify the service using proper constants
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name
        })
        
        # Create a tracer provider with ALWAYS_ON sampler
        tracer_provider = TracerProvider(
            resource=resource,
            sampler=ALWAYS_ON
        )
        
        # Create an OTLP HTTP exporter pointing to Jaeger
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"http://{settings.jaeger_host}:4318/v1/traces"
        )
        
        # Add the exporter to the tracer provider
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Add a console exporter for debugging
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        # tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
        # Set the global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Get a tracer
        tracer = trace.get_tracer(service_name)
        
        # Explicitly tell Haystack to use the tracer
        import haystack.tracing
        from haystack.tracing import OpenTelemetryTracer
        
        # First auto-detect the configured tracer
        haystack.tracing.auto_enable_tracing()
        logger.info("Enabled auto tracing for Haystack")
        
        # Then explicitly create and enable an OpenTelemetry tracer
        haystack_tracer = OpenTelemetryTracer(tracer)
        haystack.tracing.enable_tracing(haystack_tracer)
        logger.info(f"Explicitly enabled Haystack OpenTelemetry tracer for {service_name}")
        
        # Also configure content tracing if requested
        if settings.tracing_content_enabled:
            logger.info("Enabling Haystack instrumentation with content tracing")
            HaystackInstrumentor().instrument(
                tracer_provider=tracer_provider,
                is_content_tracing_enabled=True
            )
        else:
            HaystackInstrumentor().instrument(tracer_provider=tracer_provider)
        
        logger.info(f"Tracing setup complete for {service_name}")
        return tracer
    except Exception as e:
        logger.error(f"Error setting up tracing: {e}")
        return trace.get_tracer(service_name)

def instrument_fastapi(app, service_name):
    """
    Instrument a FastAPI application with OpenTelemetry.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service
    """
    # If tracing is not enabled, don't instrument
    if not settings.tracing_enabled:
        return
    
    try:
        # Setup the tracer
        setup_tracer(service_name)
        
        # Instrument FastAPI
        logger.info(f"Instrumenting FastAPI app for {service_name}")
        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"FastAPI instrumentation complete for {service_name}")
    except Exception as e:
        logger.error(f"Error instrumenting FastAPI app: {e}")

def trace_pipeline_creation(service_name="pipeline_service"):
    """
    Decorator to add tracing to pipeline creation functions.
    
    This decorator adds OpenTelemetry spans around pipeline creation functions
    to provide visibility into how pipelines are created and configured. It's
    compatible with Haystack's internal tracing by using the same tracer
    and providing the right context.
    
    Args:
        service_name: Name of the service creating the pipeline
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # If tracing is disabled, just call the function
            if not settings.tracing_enabled:
                return func(*args, **kwargs)
            
            # Get the function name and arguments for span attributes
            func_name = func.__name__
            pipeline_type = func_name.replace("create_", "").replace("_pipeline", "")
            
            # Get current tracer
            # We use the same tracer that Haystack uses internally
            tracer = trace.get_tracer("haystack.pipeline")
            
            # Create a span for the pipeline creation
            with tracer.start_as_current_span(
                "haystack.pipeline.create",
                attributes={
                    "haystack.pipeline.type": pipeline_type,
                    "haystack.pipeline.creator": func_name,
                    "haystack.pipeline.service": service_name
                }
            ) as span:
                # Record the start of pipeline creation
                span.add_event("pipeline_creation_started")
                
                # Add attributes for important configuration parameters
                for key, value in kwargs.items():
                    # Only add primitive types as attributes
                    if isinstance(value, (str, int, float, bool)) and key != "password":
                        span.set_attribute(f"haystack.pipeline.config.{key}", str(value))
                
                try:
                    # Create the pipeline
                    pipeline = func(*args, **kwargs)
                    
                    # Record successful creation and info about components
                    if hasattr(pipeline, "components") and pipeline.components:
                        span.set_attribute("haystack.pipeline.component_count", len(pipeline.components))
                        component_list = list(pipeline.components.keys())
                        span.set_attribute("haystack.pipeline.components", str(component_list))
                    
                    # Create a more detailed span architecture description
                    if hasattr(pipeline, "graph") and pipeline.graph is not None:
                        connections = []
                        for node in pipeline.graph.nodes:
                            outgoing = []
                            for edge in pipeline.graph.edges:
                                # In a MultiDiGraph, edges are typically (u, v, key) tuples
                                # where 'key' is the edge key/id, not the socket name
                                if edge[0] == node:
                                    # Need to inspect the edge attributes for connection info
                                    # but gracefully handle different graph implementations
                                    try:
                                        # For Haystack 2.x pipeline graphs
                                        if len(edge) >= 3 and hasattr(pipeline.graph, "get_edge_data"):
                                            # Get edge data might contain socket information
                                            edge_data = pipeline.graph.get_edge_data(edge[0], edge[1], edge[2])
                                            if edge_data and "source_socket" in edge_data and "dest_socket" in edge_data:
                                                # Format: target.socket_name
                                                outgoing.append(f"{edge[1]}.{edge_data['dest_socket']}")
                                            else:
                                                # Fallback: just show the target node
                                                outgoing.append(f"{edge[1]}")
                                        else:
                                            # Simple fallback for other graph types
                                            outgoing.append(f"{edge[1]}")
                                    except Exception as e:
                                        # Ultimate fallback if anything goes wrong
                                        logger.debug(f"Error extracting edge data: {e}")
                                        outgoing.append(f"{edge[1]}")
                            if outgoing:
                                connections.append(f"{node} -> {', '.join(outgoing)}")
                        if connections:
                            span.set_attribute("haystack.pipeline.connections", str(connections))
                    
                    span.add_event("pipeline_creation_completed")
                    return pipeline
                except Exception as e:
                    # Record error information
                    span.record_exception(e)
                    span.set_status(trace.StatusCode.ERROR, str(e))
                    span.add_event("pipeline_creation_failed", {"error": str(e)})
                    raise
        
        return wrapper
    return decorator

# Monkey-patch the haystack tracing module to report all spans to our tracer
# This ensures our spans appear in the same trace as Haystack's spans
def patch_haystack_tracing():
    """
    Patch Haystack's tracing system to ensure our spans are properly included
    in the same trace context.
    
    This is a compatibility function that should be called once at application startup.
    """
    if not settings.tracing_enabled:
        return
    
    try:
        import haystack.tracing as haystack_tracing
        
        # Store the original trace function
        original_trace = haystack_tracing.tracer.trace
        
        # Create a patched version that ensures our spans get the right context
        @functools.wraps(original_trace)
        def patched_trace(operation_name, tags=None, parent_span=None):
            # Get the current span context if available
            current_span = trace.get_current_span()
            if parent_span is None and current_span is not None:
                # Only use current span as parent if it's not a non-recording span
                try:
                    if hasattr(current_span, "is_recording") and current_span.is_recording():
                        parent_span = current_span
                except:
                    pass
                
            # Call the original with the enhanced context
            return original_trace(operation_name, tags, parent_span)
        
        # Apply the patch to Haystack's tracer
        haystack_tracing.tracer.trace = patched_trace
        
        logger.info("Successfully patched Haystack tracing system for improved integration")
    except Exception as e:
        logger.warning(f"Failed to patch Haystack tracing system: {e}")
        logger.warning("Custom spans may not appear in the same trace context as Haystack spans")

# Initialize patching on module import
patch_haystack_tracing() 