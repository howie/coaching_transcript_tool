import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useRouter, useParams } from 'next/navigation';
import EditClientPage from '../[id]/edit/page';
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

describe('EditClientPage', () => {
  const mockPush = jest.fn();
  const mockRouter = { push: mockPush };
  const mockUser = { id: 'user-123', email: 'test@example.com' };
  const mockT = (key: string) => key;

  const mockClient = {
    id: 'client-123',
    name: 'Test Client',
    email: 'client@example.com',
    phone: '1234567890',
    memo: 'Test memo',
    source: 'friend',
    client_type: 'individual',
    issue_types: 'career,personal',
    is_anonymized: false,
  };

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

  it('should load and display client data', async () => {
    (fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockClient),
        });
      }
      if (url.includes('/api/v1/clients/options/sources')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { value: 'friend', label: 'Friend' },
            { value: 'client', label: 'Client' },
          ]),
        });
      }
      if (url.includes('/api/v1/clients/options/types')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { value: 'individual', label: 'Individual' },
            { value: 'corporate', label: 'Corporate' },
          ]),
        });
      }
      return Promise.resolve({ ok: false });
    });

    render(<EditClientPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
      expect(screen.getByDisplayValue('client@example.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('1234567890')).toBeInTheDocument();
    });
  });

  it('should not allow editing anonymized clients', async () => {
    const anonymizedClient = { ...mockClient, is_anonymized: true };
    
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(anonymizedClient),
    });

    render(<EditClientPage />);

    await waitFor(() => {
      expect(screen.getByText('Cannot edit anonymized client')).toBeInTheDocument();
    });
  });

  it('should submit form and redirect on success', async () => {
    (fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('/api/v1/clients/client-123') && options?.method === 'PATCH') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ...mockClient, name: 'Updated Client' }),
        });
      }
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockClient),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });

    render(<EditClientPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Test Client');
    fireEvent.change(nameInput, { target: { value: 'Updated Client' } });

    const submitButton = screen.getByText('clients.update');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard/clients');
    });
  });

  it('should handle submission errors', async () => {
    window.alert = jest.fn();
    
    (fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('/api/v1/clients/client-123') && options?.method === 'PATCH') {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({ detail: 'Update failed' }),
        });
      }
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockClient),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });

    render(<EditClientPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('clients.update');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('更新客戶失敗: Update failed');
    });
  });

  it('should handle cancel button', async () => {
    (fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/v1/clients/client-123')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockClient),
        });
      }
      if (url.includes('/api/v1/clients/options/sources')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { value: 'friend', label: 'Friend' },
            { value: 'client', label: 'Client' },
          ]),
        });
      }
      if (url.includes('/api/v1/clients/options/types')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { value: 'individual', label: 'Individual' },
            { value: 'corporate', label: 'Corporate' },
          ]),
        });
      }
      return Promise.resolve({ ok: false });
    });

    render(<EditClientPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
    });

    const cancelButton = screen.getByText('common.cancel');
    fireEvent.click(cancelButton);

    expect(mockPush).toHaveBeenCalledWith('/dashboard/clients');
  });
});