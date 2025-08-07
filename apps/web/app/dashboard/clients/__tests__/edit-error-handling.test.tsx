import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useRouter, useParams } from 'next/navigation';
import ClientDetailPage from '../[id]/detail/page';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';

// Mock modules
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useParams: jest.fn(),
}));

jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/contexts/i18n-context', () => ({
  useI18n: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

describe('ClientDetailPage Error Handling', () => {
  const mockPush = jest.fn();
  const mockRouter = { push: mockPush };
  const mockUser = { id: 'user-123', email: 'test@example.com' };
  const mockT = (key: string) => key;

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useParams as jest.Mock).mockReturnValue({ id: 'client-123' });
    (useAuth as jest.Mock).mockReturnValue({ user: mockUser });
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
    
    // Setup localStorage mock
    const localStorageMock = {
      getItem: jest.fn(() => 'mock-token'),
      setItem: jest.fn(),
      clear: jest.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
  });

  it('should handle client not found error (404)', async () => {
    (fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.resolve({
          ok: false,
          status: 404,
          statusText: 'Not Found',
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });

    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Client not found')).toBeInTheDocument();
    });
  });

  it('should handle network error when fetching client', async () => {
    (fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.reject(new Error('Network error'));
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });

    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Client not found')).toBeInTheDocument();
    });
  });

  it('should handle API error response when fetching client', async () => {
    (fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });

    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Client not found')).toBeInTheDocument();
    });
  });

  it('should handle options fetch failure gracefully', async () => {
    const mockClient = {
      id: 'client-123',
      name: 'Test Client',
      email: 'client@example.com',
      phone: '1234567890',
      memo: 'Test memo',
      is_anonymized: false,
    };

    (fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockClient),
        });
      }
      if (url.includes('/api/v1/clients/options/sources') || 
          url.includes('/api/v1/clients/options/types')) {
        return Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });

    render(<ClientDetailPage />);

    // Should still display client data even if options fail to load
    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
      expect(screen.getByDisplayValue('client@example.com')).toBeInTheDocument();
    });
  });
});