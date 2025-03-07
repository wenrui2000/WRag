import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResponseTextBox from '../components/ResponseTextBox';

describe('ResponseTextBox Component', () => {
  test('renders ResponseTextBox component', () => {
    render(<ResponseTextBox response="" isLoading={false} />);
    expect(screen.getByText('LLM response')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Generated answer will appear here...')).toBeInTheDocument();
  });

  test('displays response text', () => {
    const response = 'Test response';
    render(<ResponseTextBox response={response} isLoading={false} />);
    expect(screen.getByText(response)).toBeInTheDocument();
  });

  test('shows loading spinner when isLoading is true', () => {
    render(<ResponseTextBox response="" isLoading={true} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});