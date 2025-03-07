import React, { useState, useEffect } from 'react';
import { Form, Button, Row, Col, Alert } from 'react-bootstrap';
import { fetchAvailableModels } from '../services/apiCalls';

function SearchForm({ query, setQuery, onSubmit, selectedModel, setSelectedModel }) {
  const [models, setModels] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [debugInfo, setDebugInfo] = useState('Loading models...');

  useEffect(() => {
    const getModels = async () => {
      setIsLoading(true);
      setError(null);
      try {
        console.log('Fetching models from API...');
        setDebugInfo('Fetching models...');
        const modelsList = await fetchAvailableModels();
        console.log('Models fetched:', modelsList);
        setDebugInfo(`Fetched ${modelsList.length} models`);
        setModels(modelsList);
      } catch (error) {
        console.error('Error fetching models:', error);
        setError(`Error fetching models: ${error.message}`);
        setDebugInfo(`Error: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    getModels();
  }, []);

  return (
    <Form onSubmit={onSubmit} role="form">
      {error && <Alert variant="danger">{error}</Alert>}
      {models.length === 0 && !error && <Alert variant="info">{debugInfo}</Alert>}

      <Row>
        <Col xs={12} md={9}>
          <Form.Group className="mb-3" controlId="formQuery">
            <Form.Control
              type="text"
              placeholder="Type your question here"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </Form.Group>
        </Col>
        <Col xs={12} md={3}>
          <Form.Group className="mb-3" controlId="formModel">
            <Form.Select
              value={selectedModel || ''}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={isLoading}
            >
              <option value="">Default Model</option>
              {models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
      </Row>
      <Button variant="primary" type="submit" className="w-100">
        Submit
      </Button>
    </Form>
  );
}

export default SearchForm;
