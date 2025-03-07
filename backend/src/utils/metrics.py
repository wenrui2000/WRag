"""
Prometheus metrics configuration.
"""
import logging
import time
import functools
from typing import Optional, Any, Dict, List

from prometheus_client import Counter, Histogram, Gauge, start_http_server
from fastapi import FastAPI

from common.config import settings

# Create a logger for this module
logger = logging.getLogger(__name__)

# Global metrics registry
counters = {}
histograms = {}
gauges = {}

# Component metrics specific to Haystack components
component_call_counter = None
component_latency_histogram = None

def setup_metrics(service_name: str, port: int = 8000) -> None:
    """
    Configure Prometheus metrics.
    
    Args:
        service_name: Name of the service (e.g., 'indexing_service', 'query_service')
        port: Port to expose metrics on
    """
    global component_call_counter, component_latency_histogram
    
    # If metrics are not enabled, return None
    if not hasattr(settings, 'metrics_enabled') or not settings.metrics_enabled:
        logger.info("Metrics are not enabled. Skipping metrics setup.")
        return
    
    try:
        logger.info(f"Setting up Prometheus metrics for {service_name}")
        
        # The metrics will be exposed by FastAPI on the /metrics endpoint
        # No need to start a separate HTTP server
        
        # Create metrics for pipeline components
        component_call_counter = Counter(
            'haystack_component_calls_total',
            'Number of times a Haystack component has been called',
            ['service', 'component_type', 'component_name', 'method']
        )
        
        component_latency_histogram = Histogram(
            'haystack_component_latency_milliseconds',
            'Latency of Haystack component method calls in milliseconds',
            ['service', 'component_type', 'component_name', 'method'],
            buckets=[1, 5, 10, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000, 120000, 180000, 240000, 300000]
        )
        
        logger.info(f"Metrics setup complete for {service_name}")
    except Exception as e:
        logger.error(f"Error setting up metrics: {e}")

def instrument_fastapi_with_metrics(app: FastAPI, service_name: str) -> None:
    """
    Instrument a FastAPI application with Prometheus metrics.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service
    """
    # If metrics are not enabled, don't instrument
    if not hasattr(settings, 'metrics_enabled') or not settings.metrics_enabled:
        return
    
    try:
        # Setup metrics
        setup_metrics(service_name)
        
        from prometheus_fastapi_instrumentator import Instrumentator
        
        # Instrument FastAPI for metrics
        logger.info(f"Instrumenting FastAPI app with metrics for {service_name}")
        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app)
        logger.info(f"FastAPI metrics instrumentation complete for {service_name}")
    except Exception as e:
        logger.error(f"Error instrumenting FastAPI app with metrics: {e}")

def create_counter(name: str, description: str, labels: list = None) -> Optional[Counter]:
    """
    Create a Prometheus counter metric.
    
    Args:
        name: Name of the counter
        description: Description of what the counter measures
        labels: List of label names
        
    Returns:
        A counter object or None if metrics are disabled
    """
    if not hasattr(settings, 'metrics_enabled') or not settings.metrics_enabled:
        return None
    
    if labels is None:
        labels = []
    
    if name not in counters:
        counters[name] = Counter(name, description, labels)
    
    return counters[name]

def create_histogram(name: str, description: str, labels: list = None, buckets: list = None) -> Optional[Histogram]:
    """
    Create a Prometheus histogram metric.
    
    Args:
        name: Name of the histogram
        description: Description of what the histogram measures
        labels: List of label names
        buckets: List of bucket boundaries
        
    Returns:
        A histogram object or None if metrics are disabled
    """
    if not hasattr(settings, 'metrics_enabled') or not settings.metrics_enabled:
        return None
    
    if labels is None:
        labels = []
    
    if buckets is None:
        # Default buckets suitable for milliseconds
        buckets = [1, 5, 10, 25, 50, 75, 100, 250, 500, 750, 1000, 2500, 5000, 7500, 10000]
    
    if name not in histograms:
        histograms[name] = Histogram(name, description, labels, buckets=buckets)
    
    return histograms[name]

def create_gauge(name: str, description: str, labels: list = None) -> Optional[Gauge]:
    """
    Create a Prometheus gauge metric.
    
    Args:
        name: Name of the gauge
        description: Description of what the gauge measures
        labels: List of label names
        
    Returns:
        A gauge object or None if metrics are disabled
    """
    if not hasattr(settings, 'metrics_enabled') or not settings.metrics_enabled:
        return None
    
    if labels is None:
        labels = []
    
    if name not in gauges:
        gauges[name] = Gauge(name, description, labels)
    
    return gauges[name]

def instrument_component_method(component, original_method, service_name):
    """
    Create an instrumented version of a component method.
    Used internally by patch_pipeline_components.
    
    Args:
        component: The component instance
        original_method: The original method to instrument
        service_name: Name of the service
        
    Returns:
        The instrumented method
    """
    def instrumented_method(*args, **kwargs):
        # Get component information
        component_name = component.__class__.__name__
        
        # Determine component type based on module path
        module_path = component.__class__.__module__
        component_parts = module_path.split('.')
        component_type = component_parts[-1] if len(component_parts) > 1 else "unknown"
        
        # If the component is in haystack, use a more specific type
        if "haystack" in module_path:
            # Extract the component category from the module path
            haystack_parts = [part for part in component_parts if part not in ["haystack", "components", "component", "nodes"]]
            if haystack_parts:
                component_type = haystack_parts[0]
        
        method_name = original_method.__name__
        
        start_time = time.time()
        try:
            # Call the original method
            result = original_method(*args, **kwargs)
            
            # Record metrics on success
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if component_call_counter:
                component_call_counter.labels(
                    service=service_name,
                    component_type=component_type,
                    component_name=component_name,
                    method=method_name
                ).inc()
            
            if component_latency_histogram:
                component_latency_histogram.labels(
                    service=service_name,
                    component_type=component_type,
                    component_name=component_name,
                    method=method_name
                ).observe(latency_ms)
            
            return result
        except Exception as e:
            # Record failure but re-raise the exception
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if component_latency_histogram:
                component_latency_histogram.labels(
                    service=service_name,
                    component_type=component_type,
                    component_name=component_name,
                    method=method_name
                ).observe(latency_ms)
            
            # Re-raise the original exception
            raise
            
    return instrumented_method

def patch_pipeline_components(pipeline, service_name: str = "unknown"):
    """
    Patch all components in a Haystack pipeline to collect metrics.
    
    This function monkey-patches the run method of all components in a pipeline
    to add instrumentation. Call this on a pipeline before using it.
    
    Args:
        pipeline: Haystack Pipeline instance
        service_name: Name of the service where the pipeline is running
    
    Returns:
        The same pipeline with instrumented components
    """
    if not hasattr(settings, 'metrics_enabled') or not settings.metrics_enabled:
        return pipeline
    
    # Check if pipeline is a valid Haystack Pipeline instance
    if not pipeline or not hasattr(pipeline, "graph"):
        logger.warning("Pipeline is not a valid Haystack Pipeline or has no graph attribute")
        return pipeline
    
    # Get components from the pipeline graph
    components = {}
    try:
        # Get components from graph nodes where each node has an 'instance' attribute
        for name, instance in pipeline.graph.nodes(data="instance"):
            if instance is not None:
                components[name] = instance
    except Exception as e:
        logger.error(f"Error accessing pipeline graph nodes: {e}")
        return pipeline
    
    if not components:
        logger.warning("No components found in pipeline to instrument")
        return pipeline
    
    logger.info(f"Instrumenting {len(components)} pipeline components in {service_name}")
    
    # Patch each component's run method
    for name, component in components.items():
        if hasattr(component, "run") and callable(component.run):
            # Store a reference to the original method
            original_run = component.run
            
            # Create an instrumented version
            instrumented = instrument_component_method(component, original_run, service_name)
            
            # Bind the instrumented method to the component
            # This approach uses a closure to avoid scope issues
            def make_wrapper(orig_method, instr_method):
                def wrapper(*args, **kwargs):
                    return instr_method(*args, **kwargs)
                return wrapper
                
            component.run = make_wrapper(original_run, instrumented)
            logger.debug(f"Instrumented component {name} ({component.__class__.__name__})")
    
    return pipeline 