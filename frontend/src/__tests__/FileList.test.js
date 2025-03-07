import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FileList from '../components/FileList';

describe('FileList Component', () => {
  const mockFiles = ['file1.txt', 'file2.pdf'];
  const mockOnFileInputChange = jest.fn();

  test('renders FileList component', () => {
    render(<FileList files={mockFiles} onFileInputChange={mockOnFileInputChange} />);
    expect(screen.getByText('Files')).toBeInTheDocument();
    const textarea = screen.getByRole('filelist');
    expect(textarea).toHaveValue(mockFiles.join('\n'));
  });

  test('handles file upload click', () => {
    render(<FileList files={mockFiles} onFileInputChange={mockOnFileInputChange} />);
    const uploadButton = screen.getByText('Upload Files');
    fireEvent.click(uploadButton);
    // Add assertions to check if the file input is triggered
  });

  test('displays error message', () => {
    const errorMessage = 'Error uploading files';
    render(<FileList files={[]} onFileInputChange={mockOnFileInputChange} error={errorMessage} />);
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('displays upload spinner', async () => {
    const mockOnFileInputChange = jest.fn().mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(true), 100)));
    const { getByLabelText } = render(<FileList files={[]} onFileInputChange={mockOnFileInputChange} />);
    const fileInput = getByLabelText('Upload Files');
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [new File([''], 'test.txt', { type: 'text/plain' })] } });
    });
    await waitFor(() => {
      expect(screen.getByRole('spinner')).toBeInTheDocument();
    }, { timeout: 1000 });
    await waitFor(() => {
      expect(screen.queryByRole('spinner')).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  // Add more tests for upload status, etc.
});