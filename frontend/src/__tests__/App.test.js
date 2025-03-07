import React from 'react';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';
import * as apiCalls from '../services/apiCalls';

jest.mock('../services/apiCalls');

beforeAll(() => {
  jest.useFakeTimers();
});

afterAll(() => {
  jest.useRealTimers();
});

afterEach(() => {
  cleanup();
  jest.clearAllMocks();
  jest.clearAllTimers();
});

describe('App Component', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    apiCalls.fetchFileList.mockResolvedValue(['file1.txt', 'file2.pdf']);
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    console.error.mockRestore();
  });

  test('renders App component', async () => {
    render(<App />);
    expect(screen.getByText('Example RAG UI')).toBeInTheDocument();
    await waitFor(() => {
      const textarea = screen.getByRole('filelist');
      expect(textarea).toHaveValue('file1.txt\nfile2.pdf');
    });
  });

  test('handles search query submission', async () => {
    apiCalls.searchQuery.mockResolvedValue('Mocked response');
    render(<App />);
    
    const input = screen.getByPlaceholderText('Type your question here');
    const submitButton = screen.getByText('Submit');

    fireEvent.change(input, { target: { value: 'Test query' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Mocked response')).toBeInTheDocument();
    });
  });

  // Add more tests for file upload, error handling, etc.
});