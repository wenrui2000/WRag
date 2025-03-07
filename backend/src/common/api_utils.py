from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging


logger = logging.getLogger(__name__)

def create_api(
        title: str, lifespan: callable
) -> FastAPI:
    """Creates FastAPI app with common settings"""
    app = FastAPI(title=title, lifespan=lifespan)
    
    # Add CORS middleware - same for all services:
    # Edit 'allow_origins' to include the domains where your frontend is hosted.
    # This is necessary if your frontend is hosted on a different domain than the API.
    # For example, if your frontend is hosted on "https://my-rag-app.example.com", add it to the list.
    # The entry "http://localhost:3000" allows testing the frontend build locally if the API is tunneled.
    # If the API and frontend are on the same domain, no changes are necessary.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000", "http://localhost:8080", "http://localhost"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
    )

    @app.get("/")
    async def root():
        """
        Root endpoint that provides a welcome message and documentation links.

        Returns:
            dict: A dictionary containing a welcome message and documentation links.
        """
        return {
            "message": "Welcome!",
            "documentation": {
                "Swagger UI": "/docs",
                "ReDoc": "/redoc",
                "OpenAPI JSON": "/openapi.json"
            }
        }

    @app.get("/health")
    async def health_check():
        """
        Health check endpoint to verify the service status.

        Returns:
            dict: A dictionary containing the status of the service.
        """
        return {
            "status": "ok"
        }

    return app
