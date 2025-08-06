import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useRouter } from 'next/navigation';
import NewClientPage from '../page';
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
    getClientSources: jest.fn(),
    getClientTypes: jest.fn(),
    createClient: jest.fn(),
  },
}));

const mockRouter = {
  push: jest.fn(),
};

const mockT = (key: string) => {
  const translations: Record<string, string> = {
    'clients.newClient': '新增客戶',
    'clients.name': '客戶姓名',
    'clients.namePlaceholder': '請輸入客戶姓名',
    'clients.email': '電子信箱',
    'clients.emailPlaceholder': '請輸入電子信箱',
    'clients.phone': '電話號碼',
    'clients.phonePlaceholder': '請輸入電話號碼',
    'clients.memo': '備註',
    'clients.create': '新增',
    'common.cancel': '取消',
    'common.saving': '儲存中...',
  };
  return translations[key] || key;
};

describe('NewClientPage', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useAuth as jest.Mock).mockReturnValue({ user: { id: '1' } });
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
    
    // Mock API client methods
    (apiClient.getClientSources as jest.Mock).mockResolvedValue([
      { value: 'referral', label: '別人推薦' },
      { value: 'organic', label: '自來客' },
      { value: 'friend', label: '朋友' },
      { value: 'social_media', label: '社群媒體' }
    ]);
    
    (apiClient.getClientTypes as jest.Mock).mockResolvedValue([
      { value: 'paid', label: '付費客戶' },
      { value: 'pro_bono', label: '公益客戶' },
      { value: 'free_practice', label: '免費練習' },
      { value: 'other', label: '其他' }
    ]);
    
    (apiClient.createClient as jest.Mock).mockResolvedValue({ id: '1', name: 'Test Client' });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders new client form correctly', async () => {
    render(<NewClientPage />);
    
    expect(screen.getByText('新增客戶')).toBeInTheDocument();
    expect(screen.getByLabelText('客戶姓名 *')).toBeInTheDocument();
    expect(screen.getByLabelText('電子信箱')).toBeInTheDocument();
    expect(screen.getByLabelText('電話號碼')).toBeInTheDocument();
    expect(screen.getByLabelText('備註')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('請選擇來源')).toBeInTheDocument();
      expect(screen.getByText('請選擇屬性')).toBeInTheDocument();
    });
  });

  it('loads source and type options on mount', async () => {
    render(<NewClientPage />);
    
    await waitFor(() => {
      expect(apiClient.getClientSources).toHaveBeenCalled();
      expect(apiClient.getClientTypes).toHaveBeenCalled();
    });
  });

  it('submits form with correct data', async () => {
    const user = userEvent.setup();
    
    render(<NewClientPage />);
    
    // Fill form
    await user.type(screen.getByLabelText('客戶姓名 *'), '測試客戶');
    await user.type(screen.getByLabelText('電子信箱'), 'test@example.com');
    await user.type(screen.getByLabelText('電話號碼'), '0912345678');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /新增/i }));
    
    await waitFor(() => {
      expect(apiClient.createClient).toHaveBeenCalledWith({
        name: '測試客戶',
        email: 'test@example.com',
        phone: '0912345678',
        memo: '',
        source: '',
        client_type: '',
        issue_types: ''
      });
    });
    
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/clients');
  });

  it('shows error message when creation fails', async () => {
    const user = userEvent.setup();
    
    // Mock failed create
    (apiClient.createClient as jest.Mock).mockRejectedValue(new Error('Validation error'));
    
    // Mock alert
    window.alert = jest.fn();
    
    render(<NewClientPage />);
    
    // Fill required field and submit
    await user.type(screen.getByLabelText('客戶姓名 *'), '測試客戶');
    await user.click(screen.getByRole('button', { name: /新增/i }));
    
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('創建客戶失敗: Validation error');
    });
  });

  it('navigates back to clients list when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(<NewClientPage />);
    
    await user.click(screen.getByRole('button', { name: /取消/i }));
    
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/clients');
  });
});