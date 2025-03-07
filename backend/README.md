# Development Environment

Here's how to test the backend and the UI locally.

## Configuration

While in `haystack-rag-app` directory...

Copy the `.env.example` file to `.env` and edit accordingly. Copy `.env` to `backend/src` (or export its variables manually in each shell below).

## OpenSearch

Run it locally in a container, or use a remote instance with ssh port forwarding. When running locally, use `http://localhost:9200` as the OpenSearch URL in the `.env` file.

## Starting Indexing and Query Services

1. Activate virtual environment

```bash
python -m venv venv && \
source venv/bin/activate
```

2. Install dependencies

```bash
python -m pip install -r backend/requirements.txt
```

3. Run indexing service

```bash
cd backend/src && \
uvicorn indexing.main:app --host 0.0.0.0 --port 8001
```

4. In a new terminal, run query service

```bash
source venv/bin/activate
```

```bash
cd backend/src && \
uvicorn query.main:app --host 0.0.0.0 --port 8002
```

## Starting Frontend

In a new terminal, run frontend

```bash
cd frontend && \
npm install
```

To test the UI, file uploads and indexing:

```bash
export REACT_APP_HAYSTACK_API_URL=http://localhost:8001 && \
npm start
```

To test the UI and search:

```bash
export REACT_APP_HAYSTACK_API_URL=http://localhost:8002 && \
npm start
```

## API Documentation and Testing

The API is documented with Swagger. To access the documentation, use

- `http://localhost:8001/docs`
- `http://localhost:8001/redoc`
- `http://localhost:8002/docs`
- `http://localhost:8002/redoc`
