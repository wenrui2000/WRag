import React, { useState, useRef } from 'react';
import { Form, Button, Spinner, Alert } from 'react-bootstrap';

function FileList({ files, onFileInputChange, error }) {
  const [uploadStatus, setUploadStatus] = useState('');
  const fileInputRef = useRef(null);

  const handleUploadClick = () => fileInputRef.current.click();

  const handleUploadStatus = async (event) => {
    setUploadStatus('uploading');
    try {
      const success = await onFileInputChange(event); // App.js: handleFileInputChange()
      if (success) {
        setUploadStatus('success');
      } else {
        setUploadStatus('error');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadStatus('error');
    } finally {
      setTimeout(() => setUploadStatus(''), 2000); // Clear upload status after 2 seconds
    }
  };

  return (
    <>
      <Form.Group className="mb-3">
        <Form.Label>Files</Form.Label>
        {error ? (
          <Alert variant="danger">{error}</Alert>
        ) : (
          <Form.Control
            as="textarea"
            rows={10}
            readOnly
            value={files.join('\n')}
            role="filelist"
            style={{
              resize: 'none',
              fontFamily: 'monospace',
              fontSize: '0.8rem'
            }}
          />
        )}
      </Form.Group>
      <Form.Group className="mb-3">
        <input
          id="fileInput"
          type="file"
          ref={fileInputRef}
          onChange={handleUploadStatus}
          style={{ display: 'none' }}
          multiple
          aria-label="Upload Files"
        />
        <Button onClick={handleUploadClick}>Upload Files</Button>
        {uploadStatus === 'uploading' && <Spinner animation="border" size="sm" className="ms-2" role="spinner" />}
        {uploadStatus === 'success' && <span className="text-success ms-2">Upload successful!</span>}
        {uploadStatus === 'error' && <span className="text-danger ms-2">Upload failed!</span>}
      </Form.Group>
    </>
  );
}

export default FileList;
