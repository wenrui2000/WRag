import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';
import * as apiCalls from '../services/apiCalls';

jest.mock('../services/apiCalls');

test('full user journey', async () => {
    apiCalls.fetchFileList
    .mockResolvedValueOnce(['file1.txt'])
    .mockResolvedValueOnce(['file1.txt', 'test.txt']);
  //console.log('Mock fetchFileList:', apiCalls.fetchFileList.mock.results);
  apiCalls.uploadFiles.mockResolvedValue([{ file_id: 'test.txt', status: 'success', error: null }]);
  apiCalls.searchQuery.mockResolvedValue('Query response');

  render(<App />);

  // Check initial file list
  await waitFor(() => {
    expect(screen.getByText('file1.txt')).toBeInTheDocument();
  });

  // Simulate file upload
  const uploadButton = screen.getByText('Upload Files');
  const file = new File(['file content'], 'test.txt', { type: 'text/plain' });
  const fileInput = screen.getByLabelText(/upload files/i);
  Object.defineProperty(fileInput, 'files', { value: [file] });
  fireEvent.change(fileInput);

  // Wait for the upload success message
  await waitFor(() => {
    expect(screen.getByText('Upload successful!')).toBeInTheDocument();
  });

  // Check updated file list
  await waitFor(() => {
    const fileList = screen.getByRole('filelist');
    expect(fileList).toHaveTextContent('test.txt');
  }, { timeout: 3000 });

  // Debug: Log the current content of the file list
  //console.log('File list content:', screen.getByRole('filelist').textContent);

  // Simulate search query
  const queryInput = screen.getByPlaceholderText('Type your question here');
  fireEvent.change(queryInput, { target: { value: 'Test query' } });
  fireEvent.click(screen.getByText('Submit'));

  // Check response
  await waitFor(() => {
    expect(screen.getByText('Query response')).toBeInTheDocument();
  });
});