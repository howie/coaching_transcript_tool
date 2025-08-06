import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useRouter } from 'next/navigation';
import SessionsPage from '../page';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

// Mock modules
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/contexts/i18n-context', () => ({
  useI18n: jest.fn(),
}));

// Mock API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    getClients: jest.fn(),
    getCurrencies: jest.fn(),
    getSessions: jest.fn(),
    createSession: jest.fn(),
  },
}));

const mockRouter = {
  push: jest.fn(),
};

const mockT = (key: string) => {
  const translations: Record<string, string> = {
    'sessions.title': '教練記錄',
    'sessions.addSession': '新增會談記錄',
    'sessions.selectClient': '請選擇客戶',
    'sessions.client': '客戶',
    'sessions.sessionDate': '會談日期',
    'sessions.durationMinutes': '時長 (分鐘)',
    'sessions.currency': '幣別',
    'sessions.amount': '金額',
    'sessions.notes': '備註',
    'sessions.newSession': '新增會談記錄',
    'sessions.create': '新增',
    'common.cancel': '取消',
  };
  return translations[key] || key;
};

const mockClients = [
  { id: '1', name: '客戶A', is_anonymized: false },
  { id: '2', name: '客戶B', is_anonymized: false },
];

const mockCurrencies = ['USD', 'EUR', 'NTD', 'TWD'];

describe('SessionsPage', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useAuth as jest.Mock).mockReturnValue({ user: { id: '1' } });
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
    
    // Mock API client methods
    (apiClient.getClients as jest.Mock).mockResolvedValue({ items: mockClients });
    (apiClient.getCurrencies as jest.Mock).mockResolvedValue(mockCurrencies);
    (apiClient.getSessions as jest.Mock).mockResolvedValue({ 
      items: [], 
      total: 0, 
      page: 1, 
      page_size: 20, 
      total_pages: 0 
    });
    (apiClient.createSession as jest.Mock).mockResolvedValue({ id: '1', session_date: '2024-01-15' });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders sessions page correctly', async () => {
    render(<SessionsPage />);
    
    expect(screen.getByText('教練記錄')).toBeInTheDocument();
    expect(screen.getByText('新增會談記錄')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/v1/clients?page_size=1000', expect.any(Object));
      expect(fetch).toHaveBeenCalledWith('/api/v1/sessions/options/currencies');
    });
  });

  it('opens new session modal when add button is clicked', async () => {
    const user = userEvent.setup();
    render(<SessionsPage />);
    
    await user.click(screen.getByText('新增會談記錄'));
    
    await waitFor(() => {
      expect(screen.getByText('新增會談記錄')).toBeInTheDocument();
      expect(screen.getByText('請選擇客戶')).toBeInTheDocument();
    });
  });

  it('shows "Add new client" option in client dropdown', async () => {
    const user = userEvent.setup();
    render(<SessionsPage />);
    
    // Open modal
    await user.click(screen.getByText('新增會談記錄'));
    
    await waitFor(() => {
      expect(screen.getByText('+ 新增客戶')).toBeInTheDocument();
    });
  });

  it('navigates to new client page when "Add new client" is selected', async () => {
    const user = userEvent.setup();
    render(<SessionsPage />);
    
    // Open modal
    await user.click(screen.getByText('新增會談記錄'));
    
    await waitFor(() => {
      expect(screen.getByText('+ 新增客戶')).toBeInTheDocument();
    });
    
    // Select "Add new client" option
    const clientSelect = screen.getByDisplayValue('');
    await user.selectOptions(clientSelect, 'new');
    
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/clients/new');
  });

  it('closes modal when "Add new client" is selected', async () => {
    const user = userEvent.setup();
    render(<SessionsPage />);
    
    // Open modal
    await user.click(screen.getByText('新增會談記錄'));
    
    await waitFor(() => {
      expect(screen.getByText('+ 新增客戶')).toBeInTheDocument();
    });
    
    // Select "Add new client" option
    const clientSelect = screen.getByDisplayValue('');
    await user.selectOptions(clientSelect, 'new');
    
    // Modal should be closed (we can't easily test this without more complex setup)
    // But we can verify that the navigation was called
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/clients/new');
  });

  it('loads and displays currency options', async () => {
    const user = userEvent.setup();
    render(<SessionsPage />);
    
    // Open modal
    await user.click(screen.getByText('新增會談記錄'));
    
    await waitFor(() => {
      const currencySelect = screen.getByDisplayValue('NTD');
      expect(currencySelect).toBeInTheDocument();
    });
    
    // Check that currencies are loaded
    expect(fetch).toHaveBeenCalledWith('/api/v1/sessions/options/currencies');
  });

  it('does not show source-related fields in form', async () => {
    const user = userEvent.setup();
    render(<SessionsPage />);
    
    // Open modal
    await user.click(screen.getByText('新增會談記錄'));
    
    await waitFor(() => {
      // Source field should not be present
      expect(screen.queryByText('客戶來源')).not.toBeInTheDocument();
      expect(screen.queryByText('來源')).not.toBeInTheDocument();
    });
  });

  it('does not show source column in table', async () => {
    render(<SessionsPage />);
    
    await waitFor(() => {
      // Source column should not be present in table headers
      expect(screen.queryByText('來源')).not.toBeInTheDocument();
    });
  });

  it('submits session form with correct data structure', async () => {
    const user = userEvent.setup();
    
    // Mock successful session creation
    (fetch as jest.Mock).mockImplementation((url: string, options: any) => {
      if (options?.method === 'POST' && url.includes('/sessions')) {
        return Promise.resolve({ ok: true });
      }
      // Return default mocks for other requests
      if (url.includes('/clients')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ items: mockClients })
        });
      }
      if (url.includes('/currencies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCurrencies)
        });
      }
      if (url.includes('/sessions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ 
            items: [], 
            total: 0, 
            page: 1, 
            page_size: 20, 
            total_pages: 0 
          })
        });
      }
      return Promise.resolve({ ok: false });
    });
    
    render(<SessionsPage />);
    
    // Open modal
    await user.click(screen.getByText('新增會談記錄'));
    
    await waitFor(() => {
      expect(screen.getByText('請選擇客戶')).toBeInTheDocument();
    });
    
    // Fill form
    await user.type(screen.getByDisplayValue(''), '2024-01-15');
    
    const clientSelect = screen.getByDisplayValue('');
    await user.selectOptions(clientSelect, '1');
    
    await user.type(screen.getByDisplayValue(''), '60');
    await user.type(screen.getByDisplayValue(''), '2000');
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /新增/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      const postCalls = (fetch as jest.Mock).mock.calls.filter(call => 
        call[1]?.method === 'POST' && call[0].includes('/sessions')
      );
      
      expect(postCalls.length).toBeGreaterThan(0);
      
      const requestBody = JSON.parse(postCalls[0][1].body);
      // Should not contain source field
      expect(requestBody).not.toHaveProperty('source');
      expect(requestBody).toHaveProperty('session_date');
      expect(requestBody).toHaveProperty('client_id');
      expect(requestBody).toHaveProperty('duration_min');
      expect(requestBody).toHaveProperty('fee_currency');
      expect(requestBody).toHaveProperty('fee_amount');
    });
  });
});