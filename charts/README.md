# Haystack RAG Application Helm Chart

This Helm chart deploys the Haystack reference RAG application.

## Architecture

The application consists of several components:

### API Gateway

- NGINX-based reverse proxy
- Serves static files (Reach build, CSS, images)
- Routes traffic to indexing and query services

### Search layer

- **OpenSearch**: Document storage and search engine

  - Single-node deployment
  - Secure authentication

### Backend services
- **Indexing Service**: Document processing
  - File upload handling
  - Document indexing
  - Persistent storage for uploads

- **Query Service**: Search operations
  - RAG pipeline
  - OpenAI integration
  - Configurable embedding options
  - Read-only access to persistent storage

### Frontend
- Simple React-based UI
- File upload interface
- Search functionality

## Prerequisites

- Kubernetes 1.31+
- Helm 3.16+
- Storage class with ReadWriteOnce support
- OpenAI API key

## Installation

### Quick start

1. Edit values file for your environment:

```yaml
global:
  environment: production
  image:
    registryPath: your-registry
    pullPolicy: Always
  secrets:
    useExternalSecrets: true
    name: "hra-secrets"
..
```

2. Add external secrets (or edit values.yaml):

```bash
kubectl create secret generic hra-secrets \
  --from-literal=opensearch-user=admin \
  --from-literal=opensearch-password=<password> \
  --from-literal=openai-api-key=<key>
```

3. Check the persistent storage configuration in `values.yaml`

4. Check gateway/ingress configuration in `values.yaml`

5. Install the chart:

```bash
helm install hra . -f values.yaml
```

## Configuration reference

### Global settings

```yaml
global:
  environment: development
  image:
    registryPath: your-registry
    pullPolicy: Always
  secrets:
  ..
  openai:
    apiKey: your-api-key
..
```

### Component settings

See [values.yaml](https://github.com/deepset-ai/haystack-rag-app/blob/main/charts/values.yaml) and the table below for detailed configuration options for:

- OpenSearch deployment
- Backend services (indexing and query)
- Frontend service
- API Gateway
- GKE Gateway configuration (for GKE environments)
- Ingress configuration

Please note that the `config` section in `values.yaml` is used to configure the backend services.

```yaml
search:
  opensearch:
    enabled: true
    replicas: 1
    # ... other OpenSearch settings

backend:
  indexing:
    enabled: true
    replicas: 2
    # ... other indexing service settings
  query:
    enabled: true
    replicas: 3
    # ... other query service settings
  config:
    llm:
      generator: openai
      useOpenAIEmbedder: false
    tokenizers:
      parallelism: false
    logging:
      level: INFO
      haystackLevel: INFO
    indexing:
      onStartup: true

frontend:
  enabled: true
  replicas: 2
  # ... other frontend settings

# Example GKE Gateway configuration
gkeGateway:
  enabled: true
  routes:
    - path: /
      service: gateway-api-gw
      port: 8080
```

### Storage configuration

```yaml
persistence:
  fileStorage:
    enabled: true
    size: 10Gi
    storageClass: standard-rwo-regional  # GKE storage class
    accessMode: ReadWriteOnce
```

## Validation

The chart includes schema validation. Validate your values:

```bash
helm lint --strict -f values.yaml .
```

## Maintenance

### Scaling

Components can be scaled independently:

```bash
helm upgrade hra . --set backend.query.replicas=3
```

### Updates

```bash
helm upgrade hra . -f values.yaml
```

## Troubleshooting

1. **OpenSearch issues**

   - Check memory settings and limits
   - Verify storage class availability
   - Validate security credentials

2. **Service connectivity**

   - Check service names and ports
   - Verify API Gateway nginx configuration (locations, timeouts)
   - Check gateway/ingress settings (host, path, service, port, timeouts)

3. **Resource issues**

   - Monitor resource usage
   - Ensure ephemeral storage is sufficient
   - Check pod logs
   - Verify PVC status

4. **Health checks**

    - Check readiness probes
    - Check liveness probes
    - Check OpenSearch cluster health endpoint

5. **Configuration and secrets**

    - Check values.yaml
    - Check external secrets (e.g., OpenAI API key)

## Security Considerations

1. **API Keys & secrets**
   - Use external secrets management when possible (Vault, AWS Secrets Manager, etc.)
   - Rotate credentials regularly
   - Never commit sensitive values to version control

2. **Improvements to network security**
   - Enable TLS for ingress/gateway
   - Configure network policies
   - Use secure OpenSearch configuration
   - Consider using GKE Gateway's built-in security features

## Chart Values

| Value | Type | Description | Default |
|-----------|------|-------------|---------|
| `global.environment` | string | Environment name (development/production) | `development` |
| `global.image.registryPath` | string | Container registry path | `gcr.io/your-project-id` |
| `global.image.pullPolicy` | string | Image pull policy | `Always` |
| `global.secrets.useExternalSecrets` | boolean | Use external secrets | `true` |
| `global.secrets.name` | string | Name of the secrets | `"hra-secrets"` |
| `global.secrets.opensearch.adminUser` | string | (If not external secrets)  OpenSearch username | `"admin"` |
| `global.secrets.opensearch.adminPassword` | string | (If not external secrets) OpenSearch password | `"your-password-here"` |
| `global.secrets.openai.apiKey` | string | (If not external secrets) OpenAI API key | `"sk-proj-999"` |
| `search.opensearch.enabled` | boolean | Enable OpenSearch deployment | `true` |
| `search.opensearch.replicas` | integer | Number of OpenSearch replicas | `1` |
| `search.opensearch.image.imageName` | string | OpenSearch image name | `opensearch` |
| `search.opensearch.image.tag` | string | OpenSearch image tag | `"2.18.0"` |
| `search.opensearch.image.pullPolicy` | string | Image pull policy | `IfNotPresent` |
| `search.opensearch.securityContext.runAsUser` | integer | User ID to run container | `1000` |
| `search.opensearch.podSecurityContext.fsGroup` | integer | File system group ID | `1000` |
| `search.opensearch.service.ports[0].port` | integer | Service port for REST API | `9200` |
| `search.opensearch.service.ports[0].targetPort` | integer | Container port for REST API | `9200` |
| `search.opensearch.service.ports[0].name` | string | Port name for REST API | `rest-api` |
| `search.opensearch.resources.requests.memory` | string | Memory request | `"2Gi"` |
| `search.opensearch.resources.requests.cpu` | string | CPU request | `"500m"` |
| `search.opensearch.resources.requests.ephemeral-storage` | string | Ephemeral storage request | `"2Gi"` |
| `search.opensearch.resources.limits.memory` | string | Memory limit | `"4Gi"` |
| `search.opensearch.resources.limits.cpu` | string | CPU limit | `"1000m"` |
| `search.opensearch.resources.limits.ephemeral-storage` | string | Ephemeral storage limit | `"4Gi"` |
| `search.opensearch.volumeClaimTemplates.size` | string | Storage size | `30Gi` |
| `search.opensearch.volumeClaimTemplates.storageClass` | string | Storage class | `standard-rwo-regional` |
| `search.opensearch.config.javaOpts` | string | Java options | `"-Xms512m -Xmx512m"` |
| `search.opensearch.readinessProbe.tcpSocket.port` | string | Readiness probe port | `rest-api` |
| `search.opensearch.readinessProbe.initialDelaySeconds` | integer | Initial delay for readiness | `90` |
| `search.opensearch.readinessProbe.periodSeconds` | integer | Period for readiness check | `10` |
| `search.opensearch.readinessProbe.timeoutSeconds` | integer | Timeout for readiness | `10` |
| `search.opensearch.readinessProbe.failureThreshold` | integer | Failure threshold for readiness | `10` |
| `search.opensearch.livenessProbe.tcpSocket.port` | string | Liveness probe port | `rest-api` |
| `search.opensearch.livenessProbe.initialDelaySeconds` | integer | Initial delay for liveness | `180` |
| `search.opensearch.livenessProbe.periodSeconds` | integer | Period for liveness check | `10` |
| `search.opensearch.livenessProbe.timeoutSeconds` | integer | Timeout for liveness | `5` |
| `search.opensearch.livenessProbe.failureThreshold` | integer | Failure threshold for liveness | `10` |
| `backend.indexing.enabled` | boolean | Enable indexing service | `true` |
| `backend.indexing.replicas` | integer | Number of indexing replicas | `1` |
| `backend.indexing.image.imageName` | string | Indexing service image name | `hra-indexing` |
| `backend.indexing.image.tag` | string | Indexing service image tag | `latest` |
| `backend.indexing.service.ports[0].port` | integer | Service port | `8001` |
| `backend.indexing.service.ports[0].targetPort` | integer | Container port | `8001` |
| `backend.indexing.service.ports[0].name` | string | Port name | `indexing-api` |
| `backend.indexing.service.readinessProbe.httpGet.path` | string | Readiness probe path | `/health` |
| `backend.indexing.service.readinessProbe.httpGet.port` | string | Readiness probe port | `indexing-api` |
| `backend.indexing.service.readinessProbe.initialDelaySeconds` | integer | Initial delay for readiness | `30` |
| `backend.indexing.service.readinessProbe.periodSeconds` | integer | Period for readiness check | `10` |
| `backend.indexing.service.readinessProbe.timeoutSeconds` | integer | Timeout for readiness | `5` |
| `backend.indexing.service.readinessProbe.failureThreshold` | integer | Failure threshold for readiness | `18` |
| `backend.indexing.resources.requests.memory` | string | Memory request | `"1Gi"` |
| `backend.indexing.resources.requests.cpu` | string | CPU request | `"250m"` |
| `backend.indexing.resources.requests.ephemeral-storage` | string | Ephemeral storage request | `"10Gi"` |
| `backend.indexing.resources.limits.memory` | string | Memory limit | `"2Gi"` |
| `backend.indexing.resources.limits.cpu` | string | CPU limit | `"500m"` |
| `backend.indexing.resources.limits.ephemeral-storage` | string | Ephemeral storage limit | `"20Gi"` |
| `backend.query.enabled` | boolean | Enable query service | `true` |
| `backend.query.replicas` | integer | Number of query replicas | `1` |
| `backend.query.image.imageName` | string | Query service image name | `hra-query` |
| `backend.query.image.tag` | string | Query service image tag | `latest` |
| `backend.query.service.ports[0].port` | integer | Service port | `8002` |
| `backend.query.service.ports[0].targetPort` | integer | Container port | `8002` |
| `backend.query.service.ports[0].name` | string | Port name | `query-api` |
| `backend.query.service.type` | string | Service type | `ClusterIP` |
| `backend.storage.volumeName` | string | Storage volume name | `file-storage` |
| `backend.storage.mountPath` | string | Storage mount path | `/app/files` |
| `backend.config.llm.generator` | string | LLM generator type | `openai` |
| `backend.config.llm.useOpenAIEmbedder` | boolean | Use OpenAI embedder | `false` |
| `backend.config.tokenizers.parallelism` | boolean | Enable tokenizer parallelism | `false` |
| `backend.config.logging.level` | string | Logging level | `INFO` |
| `backend.config.logging.haystackLevel` | string | Haystack logging level | `INFO` |
| `backend.config.indexing.onStartup` | boolean | Index on startup | `true` |
| `frontend.enabled` | boolean | Enable frontend deployment | `true` |
| `frontend.replicas` | integer | Number of frontend replicas | `1` |
| `frontend.image.imageName` | string | Frontend image name | `hra-frontend` |
| `frontend.image.tag` | string | Frontend image tag | `latest` |
| `frontend.service.ports[].port` | integer | Service port | `3000` |
| `frontend.service.ports[0].targetPort` | integer | Container port | `3000` |
| `frontend.service.ports[0].name` | string | Port name | `react-app` |
| `frontend.service.type` | string | Service type | `ClusterIP` |
| `frontend.service.readinessProbe.httpGet.path` | string | Readiness probe path | `/` |
| `frontend.service.readinessProbe.httpGet.port` | string | Readiness probe port | `react-app` |
| `frontend.resources.requests.memory` | string | Memory request | `"256Mi"` |
| `frontend.resources.requests.cpu` | string | CPU request | `"100m"` |
| `frontend.resources.limits.memory` | string | Memory limit | `"512Mi"` |
| `frontend.resources.limits.cpu` | string | CPU limit | `"200m"` |
| `apiGateway.enabled` | boolean | Enable API Gateway | `true` |
| `apiGateway.replicas` | integer | Number of Gateway replicas | `1` |
| `apiGateway.image.registryPath` | string | Registry path | `docker.io/library` |
| `apiGateway.image.imageName` | string | Gateway image name | `nginx` |
| `apiGateway.image.tag` | string | Gateway image tag | `alpine` |
| `apiGateway.service.ports[0].port` | integer | Service port | `8080` |
| `apiGateway.service.ports[0].targetPort` | integer | Container port | `8080` |
| `apiGateway.service.type` | string | Service type | `ClusterIP` |
| `apiGateway.configMap.name` | string | ConfigMap name | `api-gateway-config` |
| `apiGateway.resources.requests.cpu` | string | CPU request | `"100m"` |
| `apiGateway.resources.requests.memory` | string | Memory request | `"256Mi"` |
| `apiGateway.resources.limits.cpu` | string | CPU limit | `"200m"` |
| `apiGateway.resources.limits.memory` | string | Memory limit | `"512Mi"` |
| `gkeGateway.enabled` | boolean | Enable GKE Gateway | `false` |
| `gkeGateway.routes[0].path` | string | Route path | `/` |
| `gkeGateway.routes[0].service` | string | Service name | `gateway-api-gw` |
| `gkeGateway.routes[0].port` | integer | Service port | `8080` |
| `persistence.fileStorage.enabled` | boolean | Enable persistent storage | `true` |
| `persistence.fileStorage.size` | string | Storage size | `30Gi` |
| `persistence.fileStorage.storageClass` | string | Storage class name | `standard-rwo-regional` |
| `persistence.fileStorage.accessMode` | string | Storage access mode | `ReadWriteOnce` |

## Monitoring & Observability

### Metrics

..

### Logging

..

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request
