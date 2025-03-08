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

### Accessing Grafana Dashboards

Access the Grafana UI at [http://localhost:3001](http://localhost:3001) (login with username `admin` and password `admin`) to visualize Prometheus metrics through interactive dashboards. Grafana provides:
- Pre-configured dashboards for application metrics
- The ability to create custom visualizations
- Advanced analytics for performance monitoring

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

7. **grafana**: Visualization and dashboard platform for monitoring metrics from Prometheus. Access the Grafana UI at http://localhost:3001.

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
  default_model: "deepseek-r1:7b"  # Options: "deepseek-r1:1.5b" or "deepseek-r1:7b"
  ollama_models:
    - "deepseek-r1:1.5b"
    - "deepseek-r1:7b"
    - "llama3:8b"  # Add your preferred models here
    - "mistral:7b"
    - "gemma:7b"

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

### Configuring Ollama Models

The application allows you to use your preferred Ollama models by configuring them in the `config.yml` file:

1. **Add models to be pulled during startup:**
   ```yaml
   # LLM settings
   llm:
     generator: "ollama"
     use_ollama: true
     ollama_api_url: "http://ollama:11434"
     default_model: "llama3:8b"  # Choose any model from the list below
     ollama_models:
       - "deepseek-r1:1.5b"
       - "deepseek-r1:7b"
       - "llama3:8b"  # Add your preferred models here
       - "mistral:7b"
       - "gemma:7b"
   ```

#### Understanding Model Configuration

The LLM settings contain two important model-related configurations:

- **default_model**: Specifies which model will be used for inference by default. This is the model that the RAG pipeline will use to generate responses when querying the system.
- **ollama_models**: A list of all models that should be pulled/downloaded when the application starts. All models in this list will be available for use.

When you start the application, it will automatically pull all the models listed in `ollama_models` if they're not already present on your system. The model specified in `default_model` will be the one used for generating responses.

#### Changing the Default Model

To change which model is used for inference:

1. Make sure the model is listed in the `ollama_models` array (so it will be downloaded)
2. Set the `default_model` to the name of your preferred model
3. Restart the application

For example, to use Mistral instead of Llama:

```yaml
llm:
  default_model: "mistral:7b"  # This will be used for inference
  ollama_models:
    - "deepseek-r1:7b"
    - "mistral:7b"
    - "llama3:8b"
```

When you start the application using Docker Compose, the specified models will be automatically downloaded (if not already present) and the selected model will be used for inference.

#### Using Custom Ollama Models

You can also use custom models with Ollama:

1. Add your custom model to the `llm.ollama_models` list in `config.yml`
2. Ensure your custom model is available in the Ollama registry or has a valid Modelfile
3. Set `llm.default_model` to your custom model name
4. Restart the application with `docker-compose restart`

#### Checking Available Models

To check which models are currently available in your Ollama instance:

```bash
curl -X GET http://localhost:11434/api/tags
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

### Checking if Grafana is running:

```
curl -X GET http://localhost:3001/api/health
```

### Docker Logs:

```
docker-compose logs -f indexing_service
docker-compose logs -f query_service
docker-compose logs -f elasticsearch
docker-compose logs -f qdrant
docker-compose logs -f ollama
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### Removing all Docker containers, images, and volumes

If you need to completely reset your Docker environment:

```
docker-compose down -v
docker system prune -a --volumes
```

## Tracing and Monitoring

This application includes comprehensive tracing and monitoring capabilities to help you understand performance, diagnose issues, and observe system behavior.

### Tracing with OpenTelemetry and Jaeger

The application leverages OpenTelemetry for distributed tracing, with Jaeger as the backend storage and visualization tool. This provides end-to-end visibility into request processing across services.

#### Enabling Tracing

Tracing is configured in the `config.yml` file:

```yaml
# Tracing settings
tracing:
  enabled: true
  jaeger_host: "jaeger"
  jaeger_port: 6831
  content_enabled: false
```

- `enabled`: Set to `true` to enable distributed tracing
- `jaeger_host`: The hostname of the Jaeger service
- `jaeger_port`: The port for the Jaeger collector
- `content_enabled`: When set to `true`, will include document content in traces (may impact trace size and performance)

#### Accessing the Jaeger UI

Once the application is running, you can access the Jaeger UI at [http://localhost:16686](http://localhost:16686) to view traces.

The Jaeger UI provides:
- Search functionality to find traces by service, operation, tags, and duration
- Detailed flamegraphs showing the relationships between spans
- Timing information for each operation
- Tag information including error details for failed operations

#### Key Traces Available

The application traces the following operations:
- HTTP requests to the API endpoints
- Document indexing operations
- Query processing through the RAG pipeline
- Pipeline creation and component initialization
- Haystack operations (document splitting, embedding, retrieval, generation)

#### Content Tracing

For debugging purposes, you can enable content tracing by setting `content_enabled: true` in the configuration. This will include document content and query/response data in traces, which can be useful for debugging but may significantly increase trace size.

### Monitoring with Prometheus

The application uses Prometheus for metrics collection and monitoring. This provides insights into system performance, resource usage, and application-specific metrics.

#### Enabling Prometheus Metrics

Metrics collection is configured in the `config.yml` file:

```yaml
# Metrics settings
metrics:
  enabled: true
  prometheus_exporter: true
  service_name: "wrag-app"
```

#### Accessing Prometheus UI

The Prometheus UI is available at [http://localhost:9091](http://localhost:9091), allowing you to:
- Query metrics using PromQL
- Create graphs and visualizations
- Set up alerts (when configured)
- View target health status

#### Visualizing Metrics with Grafana

For enhanced visualization and dashboarding of Prometheus metrics, the application includes Grafana integration.

##### Accessing Grafana UI

The Grafana dashboard is available at [http://localhost:3001](http://localhost:3001), with the following default credentials:
- Username: `admin`
- Password: `admin`

##### Pre-configured Dashboards

Grafana comes pre-configured with:
- A Prometheus data source connected to your Prometheus instance
- A sample dashboard showing key metrics from your application:
  - HTTP request rates
  - Haystack component metrics

##### Creating Custom Dashboards

You can create your own custom dashboards in Grafana to visualize specific metrics:

1. Log in to Grafana at [http://localhost:3001](http://localhost:3001)
2. Click on "Dashboards" in the left sidebar
3. Click "New" and select "New Dashboard"
4. Use the "Add visualization" button to create panels using Prometheus metrics
5. Configure panels with appropriate PromQL queries
6. Save your dashboard for future use

##### Example PromQL Queries for Grafana

When creating panels in Grafana, you can use queries like:

1. Request rate by service:
   ```
   sum(rate(http_requests_total[5m])) by (service)
   ```

2. Average response time:
   ```
   sum(rate(http_request_duration_seconds_sum[5m])) by (handler) / sum(rate(http_request_duration_seconds_count[5m])) by (handler)
   ```

3. Error rate:
   ```
   sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
   ```

#### Available Metrics

The application exposes the following metrics:
- HTTP request counts, latencies, and status codes
- Document processing metrics (processing time, document count)
- RAG pipeline performance metrics (retrieval time, generation time)
- Haystack component metrics (embedder throughput, retriever performance)
- System resource usage (when configured)

#### Example Prometheus Queries

Here are some useful Prometheus queries:

1. Total number of API requests:
   ```
   sum(http_requests_total)
   ```

2. 95th percentile request duration:
   ```
   histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))
   ```

3. Document processing latency:
   ```
   rate(haystack_component_processing_time_seconds_sum{component="DocumentSplitter"}[5m]) / rate(haystack_component_processing_time_seconds_count{component="DocumentSplitter"}[5m])
   ```

### Combined Observability

The combination of distributed tracing and metrics provides comprehensive observability for the RAG application:
- Tracing shows the path of individual requests through the system
- Metrics provide aggregated views of system performance and health
- Together, they enable effective debugging, performance optimization, and system monitoring

### Best Practices

1. **Correlation**: When debugging an issue, use trace IDs from logs to find the corresponding trace in Jaeger.
2. **Selective Tracing**: For production, consider sampling traces instead of tracing every request.
3. **Dashboard Creation**: Create custom Prometheus dashboards for your specific monitoring needs.
4. **Alert Configuration**: Set up alerts based on key metrics to be notified of potential issues.

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
