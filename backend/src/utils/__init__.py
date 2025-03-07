"""
Utility functions for the application.
"""
from .tracing import setup_tracer, instrument_fastapi

__all__ = ["setup_tracer", "instrument_fastapi"] 