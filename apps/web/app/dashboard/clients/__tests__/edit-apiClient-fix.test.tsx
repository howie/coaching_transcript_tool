import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useRouter, useParams } from 'next/navigation';
import ClientDetailPage from '../[id]/detail/page';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

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

jest.mock('@/lib/api', () => ({
  apiClient: {
    getClient: jest.fn(),
    getClientSources: jest.fn(),
    getClientTypes: jest.fn(),
    updateClient: jest.fn(),
  },
}));

describe('ClientDetailPage ApiClient Fix', () => {
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
    client_type: 'paid',
    issue_types: 'career,personal',
    is_anonymized: false,
  };

  const mockSources = [
    { value: 'friend', label: 'Friend' },
    { value: 'referral', label: 'Referral' },
  ];

  const mockTypes = [
    { value: 'paid', label: 'Paid Client' },
    { value: 'pro_bono', label: 'Pro Bono' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useParams as jest.Mock).mockReturnValue({ id: 'client-123' });
    (useAuth as jest.Mock).mockReturnValue({ user: mockUser });
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
    
    // Default successful API responses
    (apiClient.getClient as jest.Mock).mockResolvedValue(mockClient);
    (apiClient.getClientSources as jest.Mock).mockResolvedValue(mockSources);
    (apiClient.getClientTypes as jest.Mock).mockResolvedValue(mockTypes);
    (apiClient.updateClient as jest.Mock).mockResolvedValue(mockClient);
  });

  it('should successfully load client data using apiClient', async () => {
    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(apiClient.getClient).toHaveBeenCalledWith('client-123');
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
      expect(screen.getByDisplayValue('client@example.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('1234567890')).toBeInTheDocument();
    });
  });

  it('should load client options using apiClient', async () => {
    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(apiClient.getClientSources).toHaveBeenCalled();
      expect(apiClient.getClientTypes).toHaveBeenCalled();
    });
  });

  it('should handle successful form submission using apiClient', async () => {
    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Test Client');
    fireEvent.change(nameInput, { target: { value: 'Updated Client' } });

    const submitButton = screen.getByText('clients.update');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(apiClient.updateClient).toHaveBeenCalledWith('client-123', {
        name: 'Updated Client',
        email: 'client@example.com',
        phone: '1234567890',
        memo: 'Test memo',
        source: 'friend',
        client_type: 'paid',
        issue_types: 'career,personal'
      });
      expect(mockPush).toHaveBeenCalledWith('/dashboard/clients');
    });
  });

  it('should handle API errors gracefully', async () => {
    (apiClient.getClient as jest.Mock).mockRejectedValue(new Error('Client not found'));

    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Client not found')).toBeInTheDocument();
    });
  });

  it('should handle options loading failure gracefully', async () => {
    (apiClient.getClientSources as jest.Mock).mockRejectedValue(new Error('Sources API failed'));
    (apiClient.getClientTypes as jest.Mock).mockRejectedValue(new Error('Types API failed'));

    render(<ClientDetailPage />);

    await waitFor(() => {
      // Should still load client data even if options fail
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
    });
  });

  it('should handle update errors with proper error message', async () => {
    window.alert = jest.fn();
    (apiClient.updateClient as jest.Mock).mockRejectedValue(new Error('Update failed'));

    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('clients.update');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('更新客戶失敗: Update failed');
    });
  });

  it('should not allow editing anonymized clients', async () => {
    const anonymizedClient = { ...mockClient, is_anonymized: true };
    (apiClient.getClient as jest.Mock).mockResolvedValue(anonymizedClient);

    render(<ClientDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Cannot edit anonymized client')).toBeInTheDocument();
    });
  });
});