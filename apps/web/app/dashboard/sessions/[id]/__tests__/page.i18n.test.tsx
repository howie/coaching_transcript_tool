import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter, useParams } from 'next/navigation';
import { I18nProvider } from '@/contexts/i18n-context';
import { AuthProvider } from '@/contexts/auth-context';
import SessionDetailPage from '../page';
import { apiClient } from '@/lib/api';

// Mock external dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useParams: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  apiClient: {
    getSession: jest.fn(),
    getSessions: jest.fn(),
    getClients: jest.fn(),
    getTranscript: jest.fn(),
    updateSession: jest.fn(),
    uploadTranscript: jest.fn(),
    generateAiAnalysis: jest.fn(),
    chatWithAi: jest.fn(),
    getCurrencies: jest.fn().mockResolvedValue([
      { value: 'TWD', label: 'TWD - 新台幣' },
      { value: 'USD', label: 'USD - 美元' },
      { value: 'CNY', label: 'CNY - 人民幣' },
    ]),
  },
  TranscriptNotAvailableError: class extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'TranscriptNotAvailableError';
    }
  },
}));

jest.mock('@/hooks/useTranscriptionStatus', () => ({
  useTranscriptionStatus: () => ({
    transcriptionStatus: null,
    isLoading: false,
    error: null,
  }),
  formatTimeRemaining: (seconds: number) => `${seconds}s`,
  formatDuration: (seconds: number) => `${Math.floor(seconds / 60)}:${seconds % 60}`,
}));

jest.mock('@/components/AudioUploader', () => ({
  AudioUploader: () => <div data-testid="audio-uploader">Audio Uploader</div>,
}));

jest.mock('@/hooks/usePlanLimits', () => ({
  usePlanLimits: () => ({
    checkBeforeAction: jest.fn().mockResolvedValue({ allowed: true }),
    validateAction: jest.fn().mockResolvedValue({ allowed: true }),
  }),
}));

jest.mock('@/contexts/auth-context', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      email: 'test@example.com',
      name: 'Test User',
      plan: 'free',
    },
    isAuthenticated: true,
    isLoading: false,
  }),
  AuthProvider: ({ children }: any) => children,
}));

const mockSession = {
  id: 'test-session-1',
  session_date: '2024-01-01',
  client_id: 'client-1',
  client_name: 'Test Client',
  duration_min: 60,
  fee_currency: 'TWD',
  fee_amount: 1000,
  fee_display: 'TWD 1,000',
  duration_display: '60 分鐘',
  notes: 'Test session notes',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockClients = [
  { id: 'client-1', name: 'Test Client' },
  { id: 'client-2', name: 'Another Client' },
];

const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  name: 'Test User',
  plan: 'free',
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode; language?: 'zh' | 'en' }> = ({ 
  children, 
  language = 'zh' 
}) => (
  <I18nProvider initialLanguage={language}>
    <AuthProvider>
      {children}
    </AuthProvider>
  </I18nProvider>
);

describe('SessionDetailPage i18n', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: jest.fn(),
      back: jest.fn(),
    });
    
    (useParams as jest.Mock).mockReturnValue({
      id: 'test-session-1',
    });

    (apiClient.getSession as jest.Mock).mockResolvedValue(mockSession);
    (apiClient.getClients as jest.Mock).mockResolvedValue({ items: mockClients });
    (apiClient.getTranscript as jest.Mock).mockRejectedValue(new Error('No transcript'));

    // Mock window.location for tests
    delete (window as any).location;
    window.location = { href: '' } as any;
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.resetModules();
  });

  it('should display Chinese translations correctly', async () => {
    render(
      <TestWrapper language="zh">
        <SessionDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check tab navigation translations
      expect(screen.getByText('會談概覽')).toBeInTheDocument();
      expect(screen.getByText('逐字稿')).toBeInTheDocument();
      expect(screen.getByText('AI 分析')).toBeInTheDocument();
    });

    // Check basic info section
    expect(screen.getByText('基本資料')).toBeInTheDocument();
    
    // Check transcript content section
    expect(screen.getByText('逐字稿內容')).toBeInTheDocument();
  });

  it('should display English translations correctly', async () => {
    render(
      <TestWrapper language="en">
        <SessionDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check tab navigation translations
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Transcript')).toBeInTheDocument();
      expect(screen.getByText('AI Analysis')).toBeInTheDocument();
    });

    // Check basic info section
    expect(screen.getByText('Basic Information')).toBeInTheDocument();
    
    // Check transcript content section
    expect(screen.getByText('Transcript Content')).toBeInTheDocument();
  });

  it('should display export format translation correctly', async () => {
    // Mock transcript data to show export section
    (apiClient.getTranscript as jest.Mock).mockResolvedValue({
      transcript: {
        segments: [
          {
            id: '1',
            start_time: 0,
            end_time: 5,
            speaker: 'coach',
            text: 'Hello',
            confidence: 0.95,
          }
        ],
        duration_sec: 300,
      }
    });

    render(
      <TestWrapper language="zh">
        <SessionDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Click on transcript tab to see export section
      const transcriptTab = screen.getByText('逐字稿');
      transcriptTab.click();
    });

    await waitFor(() => {
      // Check export format translation
      expect(screen.getByText('匯出格式:')).toBeInTheDocument();
      expect(screen.getByText('純文字 (.txt)')).toBeInTheDocument();
    });
  });

  it('should display session stats translations correctly', async () => {
    // Mock transcript with speaking stats
    (apiClient.getTranscript as jest.Mock).mockResolvedValue({
      transcript: {
        segments: [
          {
            id: '1',
            start_time: 0,
            end_time: 5,
            speaker: 'coach',
            text: 'Hello',
            confidence: 0.95,
          }
        ],
        duration_sec: 300,
      },
      speaking_stats: {
        coach_time: 150,
        client_time: 120,
        silence_time: 30,
        total_segments: 10,
      }
    });

    render(
      <TestWrapper language="zh">
        <SessionDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Click on transcript tab
      const transcriptTab = screen.getByText('逐字稿');
      transcriptTab.click();
    });

    await waitFor(() => {
      // Check speaking stats translations
      expect(screen.getByText('談話分析結果')).toBeInTheDocument();
      expect(screen.getByText('談話時間分配')).toBeInTheDocument();
      expect(screen.getByText('整體統計')).toBeInTheDocument();
      expect(screen.getByText('總時長')).toBeInTheDocument();
      expect(screen.getByText('談話時間')).toBeInTheDocument();
      expect(screen.getByText('靜默時間')).toBeInTheDocument();
      expect(screen.getByText('對話段數')).toBeInTheDocument();
    });
  });

  it('should display AI analysis translations correctly', async () => {
    render(
      <TestWrapper language="zh">
        <SessionDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Click on AI analysis tab
      const aiTab = screen.getByText('AI 分析');
      aiTab.click();
    });

    await waitFor(() => {
      // Check AI analysis translations
      expect(screen.getByText('會談摘要')).toBeInTheDocument();
      expect(screen.getByText('產生摘要')).toBeInTheDocument();
      expect(screen.getByText('AI 對話')).toBeInTheDocument();
    });
  });

  it('should display upload method translations correctly', async () => {
    render(
      <TestWrapper language="zh">
        <SessionDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check upload method translations
      expect(screen.getByText('請選擇上傳方式：')).toBeInTheDocument();
      expect(screen.getByText('音檔分析')).toBeInTheDocument();
      expect(screen.getByText('直接上傳逐字稿')).toBeInTheDocument();
    });
  });

  it('should display no transcript message translations correctly', async () => {
    render(
      <TestWrapper language="zh">
        <SessionDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      // Click on transcript tab
      const transcriptTab = screen.getByText('逐字稿');
      transcriptTab.click();
    });

    await waitFor(() => {
      // Check no transcript message
      expect(screen.getByText('此諮詢記錄尚未上傳音檔或逐字稿')).toBeInTheDocument();
    });
  });
});