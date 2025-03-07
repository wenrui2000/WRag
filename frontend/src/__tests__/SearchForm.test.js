import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchForm from '../components/SearchForm';

describe('SearchForm Component', () => {
  test('renders SearchForm component', () => {
    render(<SearchForm query="" setQuery={() => {}} onSubmit={() => {}} />);
    expect(screen.getByPlaceholderText('Type your question here')).toBeInTheDocument();
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });

  test('handles input change', () => {
    const setQuery = jest.fn();
    render(<SearchForm query="" setQuery={setQuery} onSubmit={() => {}} />);
    const input = screen.getByPlaceholderText('Type your question here');
    fireEvent.change(input, { target: { value: 'Test query' } });
    expect(setQuery).toHaveBeenCalledWith('Test query');
  });

  test('handles form submission', () => {
    const onSubmit = jest.fn();
    render(<SearchForm query="Test query" setQuery={() => {}} onSubmit={onSubmit} />);
    const form = screen.getByRole('form');
    fireEvent.submit(form);
    expect(onSubmit).toHaveBeenCalled();
  });
});