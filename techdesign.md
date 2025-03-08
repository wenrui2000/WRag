# WRAG-APP: Technical Design Document

## 1. Overview

This document outlines the architecture and key design decisions for our Retrieval-Augmented Generation (RAG) application. The system is designed to efficiently process, index, and query documents with LLM capabilities.

## 2. System Architecture

The application follows a microservices architecture with the following components:

- **Frontend**: User interface for document upload, query submission, and result visualization
- **Backend Services**:
  - **Indexing Service**: Handles document processing, embedding, and storage
  - **Query Service**: Manages query processing, retrieval, and generation
  - **Common Components**: Shared utilities and connectors
- **Storage**:
  - **MySQL**: Primary persistence layer for document storage and metadata
  - **Vector Database**: For efficient retrieval of embeddings
- **Observability Stack**:
  - **OpenTelemetry + Jaeger**: Distributed tracing
  - **Prometheus + Grafana**: Metrics collection and visualization
- **Model Deployment**:
  - **Ollama**: For local model hosting and inference

### Architecture Diagram

```
┌───────────────┐     ┌─────────────────────────────────────┐
│               │     │              Backend                │
│   Frontend    │────▶│  ┌───────────┐     ┌────────────┐  │
│               │     │  │ Indexing  │     │   Query    │  │
└───────────────┘     │  │ Service   │     │  Service   │  │
                      │  └───────────┘     └────────────┘  │
                      │         │                │         │
                      └─────────┼────────────────┼─────────┘
                                │                │
                      ┌─────────▼────────────────▼─────────┐
                      │            Storage                 │
                      │  ┌───────────┐     ┌────────────┐  │
                      │  │   MySQL   │     │   Vector    │  │
                      │  │           │     │  Database   │  │
                      │  └───────────┘     └────────────┘  │
                      └─────────────────────────────────────┘
                                 │
                      ┌──────────▼──────────────────────────┐
                      │        Observability               │
                      │  ┌───────────┐     ┌────────────┐  │
                      │  │OpenTelemetry    │ Prometheus  │  │
                      │  │  + Jaeger  │     │+ Grafana   │  │
                      │  └───────────┘     └────────────┘  │
                      └─────────────────────────────────────┘
```

## 3. Key Design Decisions

### 3.1 LLM Framework Selection: Haystack

We chose to use the Haystack framework rather than implementing RAG functionality from scratch.

**Advantages:**
- Comprehensive RAG capabilities available out-of-the-box
- Rich ecosystem of pre-built components (document converters, text splitters, embedding models)
- Modular architecture allowing for component-level customization
- Abstracts away many complexities of working with different embedding models and vector databases

**Challenges:**
- Steeper learning curve compared to simpler libraries
- Documentation can be inconsistent, especially with the transition between API versions
- LLM tools themselves struggle to provide guidance due to the framework's evolving nature and dual API versions
- High level of encapsulation makes certain customizations challenging (e.g., metrics collection)
- Future extensibility may be constrained by framework limitations

### 3.2 Persistence Layer: MySQL over HBase

We selected MySQL as our primary persistence database instead of HBase.

**Rationale:**
- MySQL's relational model naturally aligns with our document data structures
- Support for foreign key constraints ensures referential integrity between source documents and chunk documents
- Built-in transaction support maintains data consistency, particularly important for future user management features
- Mature ecosystem with extensive tooling and community support
- Lower operational complexity compared to distributed systems like HBase

HBase would offer advantages in highly distributed, horizontal scaling scenarios, but our current requirements don't necessitate the additional complexity of a distributed NoSQL solution.

### 3.3 Observability Stack

We implemented a comprehensive observability solution using industry-standard tools:

**Tracing: OpenTelemetry + Jaeger**
- Distributed tracing across all microservices
- Performance bottleneck identification
- Request flow visualization across system boundaries
- Custom instrumentation for Haystack components

**Monitoring: Prometheus + Grafana**
- Real-time metrics collection
- Custom dashboards for system health visualization
- Alerting capabilities for proactive issue detection
- Performance trending and capacity planning

This observability stack enables data-driven optimization and troubleshooting, particularly important when working with complex LLM processing pipelines.

## 4. Implementation Details

### 4.1 Document Processing Pipeline

1. Document ingestion through the indexing service
2. Format-specific conversion (PDF, Markdown, etc.)
3. Text chunking based on configurable strategies
4. Embedding generation using transformer models
5. Storage in both MySQL (metadata) and vector database (embeddings)

### 4.2 Query Processing Pipeline

1. Query receipt through the query service
2. Query embedding generation
3. Vector similarity search
4. Context assembly from retrieved documents
5. LLM generation with assembled context
6. Response formatting and delivery

### 4.3 Deployment Strategy

The application is containerized using Docker, with docker-compose for local deployment and potential Kubernetes support for production environments.

## 5. Scalability Considerations

Our architecture is designed with scalability in mind, allowing for growth as usage increases:

### 5.1 Distributed Deployment

The microservices architecture enables distributed deployment across multiple nodes:
- Services can be independently scaled based on load patterns
- Kubernetes orchestration provides automated scaling and load balancing
- Service mesh technologies (like Istio) can be implemented for advanced traffic management
- API Gateway pattern for centralized request routing and load distribution

### 5.2 Vector Database Scaling

For vector databases like Elasticsearch and Qdrant:
- **Replication Strategy**: Primary-replica setup with read replicas to distribute query load
- **Resource Requirements**: One node can typically support up to 10GB of index data, sufficient for most RAG applications
- **Prioritizing Replication over Sharding**: For typical RAG workloads, vertical scaling with replication is preferred over horizontal sharding
- **High Availability**: Multiple replicas ensure system availability during node failures

### 5.3 LLM Inference Scaling

LLM inference represents the primary bottleneck in the current system:
- **Distributed Ollama Deployment**: Multiple Ollama instances behind a load balancer to increase processing capacity
- **API Flexibility**: System design allows for easy extension to support external LLM APIs (OpenAI, Anthropic, etc.)
- **User API Key Support**: Infrastructure to allow users to provide their own API keys for external LLM services
- **Batching Optimizations**: Request batching for more efficient GPU utilization
- **Model Quantization**: Use of quantized models to reduce resource requirements while maintaining acceptable quality

### 5.4 Database Scaling

MySQL serves as our persistence store with the following scaling considerations:
- **Traffic Patterns**: MySQL primarily serves indexing traffic and potential future user management, not query-intensive workloads
- **Scalability Assessment**: A single MySQL node is typically sufficient for standard RAG applications
- **Optimization Path**: Read replicas can be added if metadata querying becomes a bottleneck
- **Maintenance Strategy**: Regular performance monitoring and database optimization to ensure consistent performance

## 6. Future Considerations

- User authentication and authorization system
- Enhanced document processing capabilities (more formats, improved chunking)
- Custom metrics and performance optimizations
- Advanced RAG techniques (hypothetical document embeddings, reranking)

## 7. Conclusion

This architecture provides a solid foundation for our RAG application, balancing practicality with performance. The selected technologies and design decisions support our current requirements while allowing for future growth and enhancement. 