## Overview

This project is a Retrieval-Augmented Generation (RAG) application built with Haystack 2. It demonstrates how to create a functional search and generative question-answering system with a user-friendly interface.

For detailed architectural decisions and technical design, see the [Technical Design Document](./techdesign.md).


## Quick Start

### Language Support

**Important**: Currently, this service only supports **English** documents and queries. The embedding model and text splitter components have not been adapted for Chinese or other languages. Documents in non-English languages may result in suboptimal chunking and retrieval performance.



To get started with this application:

1. Clone the repository:
   ```
   git clone https://github.com/wenrui2000/WRag.git
   ```

2. Navigate to the project directory:
   ```
   cd wrag-app
   ```

3. Customize the application in `config.yml`, particularly the model selection:
   ```yaml
   # Database connections
   elasticsearch:
     url: "http://elasticsearch:9200"
     user: "elastic"
     password: "YourSecurePass123!"
   
   qdrant:
     url: "http://qdrant:6333"
     collection_name: "semantic_search"
   
   # LLM settings - Select your preferred models here
   llm:
     generator: "ollama"  # Use either "ollama" or "openai"
     use_ollama: true
     ollama_api_url: "http://ollama:11434"
     default_model: "llama3:8b"  # This model will be used for inference
     # List all models you want available in your application
     ollama_models:
       - "deepseek-r1:1.5b"  # Smaller model (faster)
       - "llama3:8b"         # Balanced performance
       - "mistral:7b"        # Alternative option
       - "gemma:7b"          # Add or remove models as needed
   
   # Embedding model settings
   embedding:
     model: "intfloat/multilingual-e5-base"  # Embedding model for vector search
     dim: 768  # Dimension size for the chosen model
   
   # Document processing settings
   document:
     split_by: "word"  # Chunk by "word" or "character" 
     split_length: 250  # Tokens per chunk
     split_overlap: 30  # Overlap between chunks
   ```

4. Start all services using Docker Compose:
   ```
   docker-compose up -d
   ```

5. Wait for all containers to initialize. You can check the status with:
   ```
   docker-compose ps
   ```

6. Begin using the application:
   - Web UI: [http://localhost:9090](http://localhost:9090)
   - Upload PDF, TXT, or Markdown documents
   - After indexing, ask questions using the RAG capabilities

**Note**: Initial startup may take several minutes as the system downloads models, initializes databases, and sets up the observability stack.

## Using the Application

### Web Interface

The application provides a simple web interface at [http://localhost:9090](http://localhost:9090) for:

1. **Document Management**:
   - Upload documents in PDF, TXT, or Markdown formats
   - View and manage uploaded documents
   - Documents are stored in a Docker volume for persistence

2. **Search & Question Answering**:
   - Ask natural language questions about your documents
   - View retrieved context passages supporting the answer
   - Explore vector similarity search results

Note that uploading large files may take time as documents are processed and indexed synchronously.


### Changing LLM Models

To change which model is used for inference:

1. Make sure the model is listed in the `ollama_models` array in `config.yml`
2. Set the `default_model` parameter to your preferred model
3. Restart the application with `docker-compose restart`

For custom Ollama models:
1. Add your custom model to the `llm.ollama_models` list
2. Ensure it's available in the Ollama registry or has a valid Modelfile
3. Set it as your default model and restart

Check available models with:
```bash
curl -X GET http://localhost:11434/api/tags
```

## Observability Tools

The application includes comprehensive tools for monitoring and debugging:

### Prometheus & Grafana

- **Prometheus**: Access metrics at [http://localhost:9091](http://localhost:9091)
- **Grafana**: Access dashboards at [http://localhost:3001](http://localhost:3001) (login: admin/admin)
  - Pre-configured dashboards for application metrics
  - Monitors HTTP requests, document processing, and query performance
  - Predefined dashboard: [wrag-metrics](http://localhost:3001/d/wrag-metrics/wrag-application-metrics?orgId=1&refresh=5s)

## Architecture Components

- **Frontend**: React application with Bootstrap providing an intuitive UI for document uploads and queries
- **Backend**: FastAPI services powered by Haystack 2 for document processing and RAG capabilities 
- **Storage**: Elasticsearch for document storage and Qdrant for vector embeddings
- **LLM Integration**: Ollama for local model hosting and inference
- **Observability**: OpenTelemetry, Jaeger, Prometheus, and Grafana for monitoring

### Jaeger Tracing

Access the Jaeger UI at [http://localhost:16686](http://localhost:16686) to view distributed traces.

![Jaeger UI Overview](https://www.jaegertracing.io/img/screens/traces-detail.png)

##### Understanding the Jaeger UI Interface

The Jaeger UI consists of several key sections:

1. **Search Panel (Left Side)**
   - **Service**: Select the service you want to explore (e.g., `indexing_service`, `query_service`)
   - **Operation**: Filter by specific operations (e.g., `GET /documents`, `POST /query`)
   - **Tags**: Search for spans with specific tags or attribute values
   - **Lookback**: Time range for trace data (e.g., last 1h, last 6h)
   - **Min/Max Duration**: Filter traces by their execution time
   - **Limit Results**: Control how many traces are returned

2. **Trace List (Top Right)**
   - Displays matching traces with duration, span count, and timestamps
   - Color-coded to highlight potentially problematic traces
   - Sort by service, operation name, duration, or timestamp

3. **Trace Detail View (Bottom Right)**
   - Timeline visualization of all spans within a selected trace
   - Hierarchical view showing parent-child relationships between spans
   - Expandable span details showing tags, logs, and process information

##### Using Jaeger for Debugging and Performance Analysis

For the RAG application, Jaeger is particularly valuable for:

1. **RAG Pipeline Analysis**
   - Trace document processing from ingestion through chunking, embedding, and storage
   - Identify bottlenecks in the query pipeline (retrieval vs. generation phases)
   - Monitor the performance of different LLM models and embedding operations

2. **Troubleshooting Failed Operations**
   - When document uploads or queries fail, locate the error in the trace
   - See exact error messages and stack traces in span logs
   - Understand dependencies between services when errors occur

3. **Performance Optimization**
   - Compare traces before and after configuration changes
   - Identify slow components in the pipeline
   - Analyze the impact of different chunk sizes or embedding models

##### Example Scenarios

1. **Document Indexing Performance**
   - Search for traces from the `indexing_service` with the operation `POST /documents`
   - Expand the trace to see the breakdown of processing time
   - Look for spans related to document splitting, embedding generation, and database storage

2. **Query Latency Analysis**
   - Examine traces from the `query_service` with operation `POST /query`
   - Compare latencies between vector similarity search and LLM generation
   - Identify if slow queries correlate with specific document types or query patterns

3. **Error Investigation**
   - Filter traces with the tag `error=true`
   - Expand error spans to see the detailed error messages
   - Track the propagation of errors across service boundaries

##### Advanced Trace Navigation Tips

- Use the **Compare** feature to analyze multiple traces side-by-side
- Toggle **Span Logs** to see detailed event information within spans
- Enable **Span References** to visualize relationships between spans in different services
- Use **Timeline Expand/Collapse** controls to focus on specific parts of a complex trace
- Save complex search queries using **Search** presets for later reuse



## Troubleshooting

### Service Health Checks

```bash
# Elasticsearch
curl -X GET http://localhost:9201

# Qdrant
curl -X GET http://localhost:6333/collections

# Ollama
curl -X GET http://localhost:11434/api/tags

# Prometheus
curl -X GET http://localhost:9091/api/v1/status/config

# Grafana
curl -X GET http://localhost:3001/api/health
```

### Viewing Logs

```bash
# View logs for a specific service
docker-compose logs -f indexing_service
docker-compose logs -f query_service
docker-compose logs -f elasticsearch
docker-compose logs -f qdrant
docker-compose logs -f ollama

# View logs for all services
docker-compose logs -f
```

### Resetting the Environment

If you need to completely reset your Docker environment:

```bash
docker-compose down -v
docker system prune -a --volumes
```
