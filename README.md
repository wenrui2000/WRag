# RAG Application with Haystack, React UI, Elasticsearch, Qdrant and Ollama

## Overview

This project is a Retrieval-Augmented Generation (RAG) application built with Haystack 2. It demonstrates how to create a functional search and generative question-answering system with a user-friendly interface.

### Backend
The backend is built with [FastAPI](https://github.com/fastapi/fastapi) and [Haystack 2](https://github.com/deepset-ai/haystack). It provides a RAG pipeline that can use either Ollama or OpenAI for generation.

### Frontend
The frontend is a React application leveraging [Bootstrap](https://getbootstrap.com/). It offers an intuitive interface for users to interact with the RAG system, upload documents, and perform searches.

## Quick Start

To quickly test this application, do the following:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/haystack-rag-app.git
   ```

2. Switch to the project directory:
   ```
   cd haystack-rag-app
   ```

3. Configure the application by editing the `config.yml` file:
   - Adjust Elasticsearch settings
   - Configure LLM settings (Ollama model selection)
   - Adjust embedding model settings if needed
   - Change document processing parameters if needed

4. Start the application using Docker Compose:
   ```
   docker-compose up
   ```
   (Or `docker-compose up -d` to run in detached mode.)

5. Once all containers are up and running, use a browser to access the UI at http://localhost:9090.

The above steps will set up and run all necessary components, including the backend services, frontend, Elasticsearch, Qdrant, Ollama, and the nginx proxy. After a few minutes, you can start uploading documents and querying the system as described in the "How to Use" section below.

**Note**: It may take some time for all containers to start. Check container logs if you're having trouble. For instance, the backend containers should report the following when they're ready:

```
nginx-1             | 2024/xx/xx xx:xx:xx [notice] 1#1: nginx/x.xx.x
nginx-1             | 2024/xx/xx xx:xx:xx [notice] 1#1: start worker processes
indexing_service-1  | INFO:     127.0.0.1:xxxxx - "GET /health HTTP/1.1" 200 OK
query_service-1     | INFO:     127.0.0.1:xxxxx - "GET /health HTTP/1.1" 200 OK
```

## How to Use

### Accessing the UI

1. Ensure that all containers are running and the backend is ready.
2. Open your web browser and navigate to [http://localhost:9090](http://localhost:9090).
3. Use the interface to upload documents that you want to search through. Uploaded files are stored in a Docker volume.
4. Uploading large files may take a while since the files are indexed synchronously.
5. Once documents are uploaded, you can ask questions and search the documents.
6. The query backend service will use the RAG pipeline to process your query and return relevant results.

**Note**: This RAG application currently supports PDF, TXT, and Markdown file formats.

### Accessing Prometheus Metrics

Access the Prometheus UI at [http://localhost:9091](http://localhost:9091) to view system metrics, including:
- HTTP request counts and latencies
- File upload and indexing operations
- Search performance metrics

## How the Application Works with Docker

When all containers are running, the application architecture works as follows:

1. **nginx proxy container**: This container acts as a reverse proxy and is the entry point for all incoming requests. It listens on port `9090` and routes traffic based on the request URI:

   - Requests to `/`: These are routed to the frontend container, which serves the React UI application build.
   - Requests to `/api`: These are proxied to the backend services, which handle API requests.

2. **frontend container**: This container hosts the React UI application. It doesn't normally receive external requests but is accessed through the nginx proxy.

3. **backend services containers**: 
   - **indexing_service**: Handles document uploading and indexing.
   - **query_service**: Processes search queries using the RAG pipeline.

4. **database containers**:
   - **elasticsearch**: For search and document storage.
   - **qdrant**: For vector storage and semantic search.
   - **kibana**: Web UI for Elasticsearch (optional, for debugging).

5. **ollama**: Container for running local LLMs.

6. **prometheus**: Metrics collection and monitoring system. Access the Prometheus UI at http://localhost:9091.

This setup allows for a clean separation of concerns and scalability.

## Configuration

The application is configured via the `config.yml` file:

```yaml
# Elasticsearch settings
elasticsearch:
  url: "http://elasticsearch:9200"
  user: "elastic"
  password: "YourSecurePass123!"

# Qdrant settings
qdrant:
  url: "http://qdrant:6333"
  collection_name: "semantic_search"

# LLM settings
llm:
  generator: "ollama"
  use_ollama: true
  ollama_api_url: "http://ollama:11434"
  ollama_model: "deepseek-r1:7b"  # Options: "deepseek-r1:1.5b" or "deepseek-r1:7b"

# Embedding settings
embedding:
  model: "intfloat/multilingual-e5-base"
  dim: 768

# Document processing settings
document:
  split_by: "word"
  split_length: 250
  split_overlap: 30
```

## Building and Running Locally

The project includes a Makefile with various commands:

```bash
# Run all tests
make test

# Build all images
make build

# Start all services
make start

# Stop all services
make stop

# Restart all services
make restart

# Clean Docker resources
make clean

# Rebuild a specific service
make rebuild-service SERVICE=indexing_service
```

## Troubleshooting

### Checking if Elasticsearch is running:

```
curl -X GET http://localhost:9201
```

### Checking if Qdrant is running:

```
curl -X GET http://localhost:6333/collections
```

### Checking if Ollama is running:

```
curl -X GET http://localhost:11434/api/tags
```

### Checking if Prometheus is running:

```
curl -X GET http://localhost:9091/api/v1/status/config
```

### Docker Logs:

```
docker-compose logs -f indexing_service
docker-compose logs -f query_service
docker-compose logs -f elasticsearch
docker-compose logs -f qdrant
docker-compose logs -f ollama
```

### Removing all Docker containers, images, and volumes

If you need to completely reset your Docker environment:

```
docker-compose down -v
docker system prune -a --volumes
```

## Project Structure

- `backend/`: Backend code
  - `src/`: Source code
    - `common/`: Shared code between services
    - `indexing/`: Indexing service code
    - `query/`: Query service code
    - `pipelines/`: Haystack pipeline definitions
  - `tests/`: Test code
- `frontend/`: Frontend code
- `scripts/`: Utility scripts
- `nginx/`: Nginx configuration
- `config.yml`: Application configuration
- `docker-compose.yml`: Docker Compose configuration
- `Makefile`: Build and deployment commands

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- Make (for Windows, you can use PowerShell or the provided batch scripts)
