import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Modal, Button, Spinner } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import FileList from './components/FileList';
import SearchForm from './components/SearchForm';
import ResponseTextBox from './components/ResponseTextBox';
import { fetchFileList, searchQuery, uploadFiles } from './services/apiCalls';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [files, setFiles] = useState([]);
  const [fileListError, setFileListError] = useState(null);
  const [oversizedUpload, setOversizedUpload] = useState([]);
  const [showSizeModal, setShowSizeModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('');

  // Fetch the list of files when the component mounts
  useEffect(() => {
    fetchFileList()
      .then(setFiles)
      .catch(error => {
        console.error('Error fetching file list:', error);
        setFileListError('Failed to connect to the API.');
      });
  }, []);

  const ALLOWED_FILE_TYPES = ['.pdf', '.txt'];
  const MAX_TOTAL_SIZE = 110 * 1024 * 1024; // Limit total upload size to 110MB (can be several files)

  const handleFileInputChange = async (e) => {
    setFileListError(null); // Clear any previous errors
    const files = Array.from(e.target.files);
    // Filter out files that are not .pdf or .txt
    const validFiles = files.filter(file =>
      ALLOWED_FILE_TYPES.some(type => file.name.toLowerCase().endsWith(type))
    );
    // Check if any files were filtered out
    if (validFiles.length < files.length) {
      console.warn('Some files were skipped because they are not .pdf or .txt');
    }
    const totalSize = validFiles.reduce((acc, file) => acc + file.size, 0);
    if (totalSize > MAX_TOTAL_SIZE) {
      setOversizedUpload(validFiles);
      setShowSizeModal(true);
      return false;
    }
    if (validFiles.length > 0) {
      try {
        await uploadFiles(validFiles);
        const updatedFiles = await fetchFileList(); // Retrieve the list of files
        setFiles(updatedFiles);
        return true;
      } catch (error) {
        console.error('Error uploading files:', error);
        setFileListError('Error uploading files. Please try again.');
        return false;
      }
    } else {
      console.error('No valid files selected for upload');
      setFileListError('Please choose .pdf or .txt files.');
      return false;
    }
  };

  const handleCloseSizeModal = () => {
    setShowSizeModal(false);
    setOversizedUpload([]);
  };

  // Function to handle seach form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const result = await searchQuery(query, selectedModel || null);
      setResponse(result);
    } catch (error) {
      console.error('Error:', error);
      setResponse('An error occurred while fetching the response.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Container fluid className="bg-light py-2 mb-5">
        <Row>
          <Col className="d-flex align-items-center">
            <a href="https://haystack.deepset.ai" target="_blank" rel="noopener noreferrer">
              <img
                src="/haystack-signet-colored-on-dark.png"
                alt="Haystack Logo"
                style={{ height: '100px', marginRight: '1px' }}
              />
            </a>
            <h1 className="h3 mb-0">Example RAG UI</h1>
          </Col>
        </Row>
      </Container>

      <Container className="mt-5" style={{ maxWidth: '1200px' }}>
        <Row>
          <Col md={4}>
            {/* Display list of files and file upload input */}
            <FileList files={files} onFileInputChange={handleFileInputChange} error={fileListError} />
          </Col>
          <Col md={8}>
            {/* Display response and search form */}
            <ResponseTextBox response={response} isLoading={isLoading} />
            <SearchForm
              query={query}
              setQuery={setQuery}
              onSubmit={handleSubmit}
              selectedModel={selectedModel}
              setSelectedModel={setSelectedModel}
            />
          </Col>
        </Row>
      </Container>

      <Modal show={showSizeModal} onHide={handleCloseSizeModal}>
        <Modal.Header closeButton>
          <Modal.Title>Upload Size Error</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Selected file(s) exceed the maximum upload size of 100MB:
          <ul>
            {oversizedUpload.map((file, index) => (
              <li key={index}>{file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)</li>
            ))}
          </ul>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseSizeModal}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

    </>
  );
}

export default App;
