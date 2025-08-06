import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SessionsPage from '../page';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

// Mock modules
jest.mock('@/contexts/i18n-context', () => ({
  useI18n: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  apiClient: {
    getClients: jest.fn(),
    getCurrencies: jest.fn(),
    getSessions: jest.fn(),
    createSession: jest.fn(),
    updateSession: jest.fn(),
    deleteSession: jest.fn(),
    createClient: jest.fn(),
  },
}));

jest.mock('@/components/ClientModal', () => ({
  ClientModal: ({ isOpen, onClose, onClientCreated }: any) => {
    if (!isOpen) return null;
    return (
      <div data-testid="client-modal">
        <button onClick={() => {
          const newClient = { id: 'new-client', name: 'New Client' };
          onClientCreated(newClient);
          onClose();
        }}>Create Client</button>
      </div>
    );
  }
}));

describe('SessionsPage Client Data Loading', () => {
  const mockT = (key: string) => key;
  const mockSessions = [
    {
      id: 'session-1',
      session_date: '2025-08-05',
      client: { id: 'client-1', name: 'Client 1', is_anonymized: false },
      duration_min: 60,
      fee_currency: 'NTD',
      fee_amount: 2500,
      fee_display: 'NTD 2,500',
      duration_display: '60 分鐘',
      notes: 'Test session',
    },
  ];

  const mockClients = [
    { id: 'client-1', name: 'Client 1', is_anonymized: false },
    { id: 'client-2', name: 'Client 2', is_anonymized: false },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
    
    // Default successful responses
    (apiClient.getSessions as jest.Mock).mockResolvedValue({ 
      items: mockSessions,
      total_pages: 1 
    });
    (apiClient.getCurrencies as jest.Mock).mockResolvedValue(['NTD', 'USD', 'EUR']);
  });

  it('should handle client loading failure with fallback', async () => {
    // Mock clients API to fail
    (apiClient.getClients as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<SessionsPage />);

    await waitFor(() => {
      expect(screen.getByText('sessions.title')).toBeInTheDocument();
    });

    // Should still render the page even if clients fail to load
    expect(screen.getByText('sessions.addSession')).toBeInTheDocument();
  });

  it('should load client data in filters', async () => {
    (apiClient.getClients as jest.Mock).mockResolvedValue({ 
      items: mockClients,
      total_pages: 1 
    });

    render(<SessionsPage />);

    await waitFor(() => {
      // Check that clients are loaded in the filter dropdown
      const clientFilter = screen.getByText('sessions.client').parentElement?.parentElement?.querySelector('select');
      expect(clientFilter).toBeInTheDocument();
      expect(clientFilter?.innerHTML).toContain('Client 1');
      expect(clientFilter?.innerHTML).toContain('Client 2');
    });
  });

  it('should refresh client data when opening create modal', async () => {
    const updatedClients = [
      ...mockClients,
      { id: 'client-3', name: 'Client 3', is_anonymized: false },
    ];

    (apiClient.getClients as jest.Mock)
      .mockResolvedValueOnce({ items: mockClients, total_pages: 1 }) // Initial load
      .mockResolvedValueOnce({ items: updatedClients, total_pages: 1 }); // Modal open refresh

    render(<SessionsPage />);

    // Open create modal
    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      // Verify getClients was called twice (initial + modal open)
      expect(apiClient.getClients).toHaveBeenCalledTimes(2);
    });
  });

  it('should handle client refresh failure gracefully', async () => {
    (apiClient.getClients as jest.Mock)
      .mockResolvedValueOnce({ items: mockClients, total_pages: 1 }) // Initial load succeeds
      .mockRejectedValueOnce(new Error('Refresh failed')); // Modal open refresh fails

    render(<SessionsPage />);

    // Open create modal
    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      // Modal should still open even if refresh fails
      expect(screen.getByText('sessions.newSession')).toBeInTheDocument();
    });
  });

  it('should load currencies from API with fallback to defaults', async () => {
    (apiClient.getClients as jest.Mock).mockResolvedValue({ 
      items: mockClients,
      total_pages: 1 
    });
    (apiClient.getCurrencies as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      // Should have default currencies even if API fails
      const currencySelect = screen.getByText('sessions.currency').parentElement?.parentElement?.querySelector('select');
      expect(currencySelect).toBeInTheDocument();
      expect(currencySelect?.innerHTML).toContain('NTD');
      expect(currencySelect?.innerHTML).toContain('USD');
    });
  });

  it('should handle empty client list gracefully', async () => {
    (apiClient.getClients as jest.Mock).mockResolvedValue({ 
      items: [],
      total_pages: 1 
    });

    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      const clientSelect = screen.getByText('sessions.client').parentElement?.parentElement?.querySelector('select');
      expect(clientSelect).toBeInTheDocument();
      // Should have the "select client" and "add client" options even with no clients
      expect(clientSelect?.innerHTML).toContain('sessions.selectClient');
      expect(clientSelect?.innerHTML).toContain('新增客戶');
    });
  });

  it('should handle malformed API response', async () => {
    (apiClient.getClients as jest.Mock).mockResolvedValue({ 
      items: null, // Malformed response
      total_pages: 1 
    });

    render(<SessionsPage />);

    // Should handle gracefully and not crash
    await waitFor(() => {
      expect(screen.getByText('sessions.title')).toBeInTheDocument();
    });
  });

  it('should use fallback empty array when clients API returns undefined items', async () => {
    (apiClient.getClients as jest.Mock).mockResolvedValue({ 
      items: undefined,
      total_pages: 1 
    });

    render(<SessionsPage />);

    // Should not crash during initial render
    await waitFor(() => {
      expect(screen.getByText('sessions.title')).toBeInTheDocument();
    });

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      // Should not crash and should show the client select even with multiple sessions.client labels
      const clientSelects = screen.getAllByText('sessions.client');
      expect(clientSelects.length).toBeGreaterThan(0);
      
      // Should have at least the modal form rendered
      expect(screen.getByText('sessions.newSession')).toBeInTheDocument();
    });
  });
});