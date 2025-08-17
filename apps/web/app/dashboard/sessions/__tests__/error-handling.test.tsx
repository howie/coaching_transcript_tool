import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
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
    'sessions.loading': '載入中...',
    'sessions.date': '日期',
    'sessions.client': '客戶',
    'sessions.duration': '時長',
    'sessions.fee': '費用',
    'sessions.actions': '操作',
  };
  return translations[key] || key;
};

describe('SessionsPage Error Handling', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useAuth as jest.Mock).mockReturnValue({ user: { id: '1' } });
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('handles undefined sessions data gracefully', async () => {
    // Mock API to return undefined items
    (apiClient.getClients as jest.Mock).mockResolvedValue({ items: [] });
    (apiClient.getCurrencies as jest.Mock).mockResolvedValue([]);
    (apiClient.getSessions as jest.Mock).mockResolvedValue({ 
      items: undefined, // This is the problematic case
      total: 0, 
      total_pages: 0 
    });

    // This should not throw an error
    expect(() => render(<SessionsPage />)).not.toThrow();
    
    // The component should still render the basic structure
    expect(screen.getByText('教練記錄')).toBeInTheDocument();
    expect(screen.getByText('日期')).toBeInTheDocument();
    expect(screen.getByText('客戶')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    // Mock API to throw errors
    (apiClient.getClients as jest.Mock).mockRejectedValue(new Error('API Error'));
    (apiClient.getCurrencies as jest.Mock).mockRejectedValue(new Error('API Error'));
    (apiClient.getSessions as jest.Mock).mockRejectedValue(new Error('API Error'));

    // Component should not crash
    expect(() => render(<SessionsPage />)).not.toThrow();
    
    // Should still show the basic UI
    expect(screen.getByText('教練記錄')).toBeInTheDocument();
    
    await waitFor(() => {
      // Loading should eventually complete (even with errors)
      expect(apiClient.getSessions).toHaveBeenCalled();
    });
  });

  it('handles malformed API responses', async () => {
    // Mock API to return malformed data
    (apiClient.getClients as jest.Mock).mockResolvedValue(null);
    (apiClient.getCurrencies as jest.Mock).mockResolvedValue(null);
    (apiClient.getSessions as jest.Mock).mockResolvedValue(null);

    // Component should not crash
    expect(() => render(<SessionsPage />)).not.toThrow();
    
    expect(screen.getByText('教練記錄')).toBeInTheDocument();
  });

  it('displays loading state correctly', async () => {
    // Mock API with delayed response
    (apiClient.getClients as jest.Mock).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ items: [] }), 100))
    );
    (apiClient.getCurrencies as jest.Mock).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve([]), 100))
    );
    (apiClient.getSessions as jest.Mock).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ items: [], total_pages: 0 }), 100))
    );

    render(<SessionsPage />);
    
    // Should show loading initially
    expect(screen.getByText('載入中...')).toBeInTheDocument();
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('載入中...')).not.toBeInTheDocument();
    }, { timeout: 200 });
  });

  it('handles empty sessions list', async () => {
    (apiClient.getClients as jest.Mock).mockResolvedValue({ items: [] });
    (apiClient.getCurrencies as jest.Mock).mockResolvedValue([]);
    (apiClient.getSessions as jest.Mock).mockResolvedValue({ 
      items: [], // Empty array
      total: 0, 
      total_pages: 0 
    });

    render(<SessionsPage />);
    
    await waitFor(() => {
      expect(apiClient.getSessions).toHaveBeenCalled();
    });

    // Should render table headers even with empty data
    expect(screen.getByText('日期')).toBeInTheDocument();
    expect(screen.getByText('客戶')).toBeInTheDocument();
    expect(screen.getByText('時長')).toBeInTheDocument();
    expect(screen.getByText('費用')).toBeInTheDocument();
    expect(screen.getByText('操作')).toBeInTheDocument();
  });
});