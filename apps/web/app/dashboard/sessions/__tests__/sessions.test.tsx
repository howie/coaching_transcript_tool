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

describe('SessionsPage', () => {
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
    
    // Default mock implementations
    (apiClient.getClients as jest.Mock).mockResolvedValue({ 
      items: mockClients,
      total_pages: 1 
    });
    (apiClient.getCurrencies as jest.Mock).mockResolvedValue(['NTD', 'USD', 'EUR']);
    (apiClient.getSessions as jest.Mock).mockResolvedValue({ 
      items: mockSessions,
      total_pages: 1 
    });
  });

  it('should render sessions table', async () => {
    render(<SessionsPage />);

    await waitFor(() => {
      expect(screen.getByText('sessions.title')).toBeInTheDocument();
      // Use getAllByText since Client 1 appears in both dropdown and table
      const clientElements = screen.getAllByText('Client 1');
      expect(clientElements.length).toBeGreaterThan(0);
      expect(screen.getByText('2025-08-05')).toBeInTheDocument();
      expect(screen.getByText('60 分鐘')).toBeInTheDocument();
      expect(screen.getByText('NTD 2,500')).toBeInTheDocument();
    });
  });

  it('should open create session modal', async () => {
    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('sessions.newSession')).toBeInTheDocument();
    });
  });

  it('should provide default currencies when API fails', async () => {
    (apiClient.getCurrencies as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      const currencySelect = screen.getByText('sessions.currency').parentElement?.querySelector('select');
      expect(currencySelect).toBeInTheDocument();
      // Should have default currencies
      expect(currencySelect?.innerHTML).toContain('NTD');
      expect(currencySelect?.innerHTML).toContain('USD');
      expect(currencySelect?.innerHTML).toContain('EUR');
    });
  });

  it('should handle amount as optional field', async () => {
    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      const amountInput = screen.getByPlaceholderText('0');
      expect(amountInput).not.toHaveAttribute('required');
    });
  });

  it('should open client modal when selecting new client', async () => {
    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      const clientSelects = screen.getAllByText('sessions.client');
      const clientSelect = clientSelects[0].parentElement?.parentElement?.querySelector('select') as HTMLSelectElement;
      expect(clientSelect).toBeInTheDocument();
      
      fireEvent.change(clientSelect, { target: { value: 'new' } });
    });

    await waitFor(() => {
      expect(screen.getByTestId('client-modal')).toBeInTheDocument();
    });
  });

  it('should add new client to list after creation', async () => {
    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    // Open client modal
    await waitFor(() => {
      const clientSelects = screen.getAllByText('sessions.client');
      const clientSelect = clientSelects[0].parentElement?.parentElement?.querySelector('select') as HTMLSelectElement;
      fireEvent.change(clientSelect, { target: { value: 'new' } });
    });

    // Create new client through modal
    const createClientButton = await screen.findByText('Create Client');
    fireEvent.click(createClientButton);

    await waitFor(() => {
      expect(screen.queryByTestId('client-modal')).not.toBeInTheDocument();
    });
  });

  it('should delete session with confirmation', async () => {
    window.confirm = jest.fn(() => true);
    (apiClient.deleteSession as jest.Mock).mockResolvedValue({});

    render(<SessionsPage />);

    await waitFor(() => {
      const deleteButtons = screen.getAllByTitle('刪除');
      expect(deleteButtons).toHaveLength(1);
      fireEvent.click(deleteButtons[0]);
    });

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith('sessions.confirmDelete');
      expect(apiClient.deleteSession).toHaveBeenCalledWith('session-1');
    });
  });

  it('should not delete session when cancelled', async () => {
    window.confirm = jest.fn(() => false);

    render(<SessionsPage />);

    await waitFor(() => {
      const deleteButtons = screen.getAllByTitle('刪除');
      fireEvent.click(deleteButtons[0]);
    });

    expect(apiClient.deleteSession).not.toHaveBeenCalled();
  });

  it('should refresh clients when opening create modal', async () => {
    const updatedClients = [
      ...mockClients,
      { id: 'client-3', name: 'Client 3', is_anonymized: false },
    ];

    (apiClient.getClients as jest.Mock)
      .mockResolvedValueOnce({ items: mockClients, total_pages: 1 }) // Initial load
      .mockResolvedValueOnce({ items: updatedClients, total_pages: 1 }); // Refresh on modal open

    render(<SessionsPage />);

    const addButton = await screen.findByText('sessions.addSession');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(apiClient.getClients).toHaveBeenCalledTimes(2);
    });
  });

  it('should handle filters correctly', async () => {
    render(<SessionsPage />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('sessions.title')).toBeInTheDocument();
    });

    const startDateInputs = screen.getAllByLabelText('sessions.startDate');
    const endDateInputs = screen.getAllByLabelText('sessions.endDate');
    
    fireEvent.change(startDateInputs[0], { target: { value: '2025-08-01' } });
    fireEvent.change(endDateInputs[0], { target: { value: '2025-08-31' } });

    await waitFor(() => {
      expect(apiClient.getSessions).toHaveBeenCalledWith(
        1,
        20,
        expect.objectContaining({
          from_date: '2025-08-01',
          to_date: '2025-08-31',
          sort: '-session_date'
        })
      );
    });
  });
});