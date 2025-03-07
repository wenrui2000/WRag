import React from 'react';
import { Form, Spinner } from 'react-bootstrap';

function ResponseTextBox({ response, isLoading }) {
  return (
    <Form.Group className="mb-3">
      <Form.Label>LLM response</Form.Label>
      <div className="position-relative">
        <Form.Control
          as="textarea"
          rows={15}
          value={response}
          readOnly
          placeholder="Generated answer will appear here..."
          style={{ resize: 'none' }}
        />
        {isLoading && (
          <div className="position-absolute top-50 start-50 translate-middle">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        )}
      </div>
    </Form.Group>
  );
}

export default ResponseTextBox;
