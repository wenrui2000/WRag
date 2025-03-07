import { fetchFileList, searchQuery, uploadFiles } from '../services/apiCalls';

global.fetch = jest.fn();

describe('API Calls', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('fetchFileList', async () => {
    const mockResponse = { files: ['file1.txt', 'file2.pdf'] };
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchFileList();
    expect(result).toEqual(mockResponse.files);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/files'));
  });

  test('searchQuery', async () => {
    const mockResponse = {
      results: [{
        answers: [{
          answer: 'Mocked response'
        }]
      }]
    };
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await searchQuery('Test query');
    expect(result).toBe('Mocked response');
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/search'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ query: 'Test query' }),
      })
    );
  });

  test('uploadFiles', async () => {
    const mockResponse = { message: 'Files uploaded successfully' };
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const mockFiles = [new File(['file content'], 'test.txt')];
    const result = await uploadFiles(mockFiles);
    expect(result).toEqual(mockResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/files'),
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    );
  });

  test('fetchFileList handles network error', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));
    await expect(fetchFileList()).rejects.toThrow('Network error');
  });


  // Add more tests for error handling scenarios
});