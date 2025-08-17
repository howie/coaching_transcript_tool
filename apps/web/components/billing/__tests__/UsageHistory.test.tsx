import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UsageHistory from '../UsageHistory';

// Mock the chart components
jest.mock('@/components/charts/LineChart', () => {
  return function MockLineChart({ title, data }: any) {
    return (
      <div data-testid="line-chart">
        <h3>{title}</h3>
        <div>{data.length} data points</div>
      </div>
    );
  };
});

jest.mock('@/components/charts/BarChart', () => {
  return function MockBarChart({ title, data }: any) {
    return (
      <div data-testid="bar-chart">
        <h3>{title}</h3>
        <div>{data.length} data points</div>
      </div>
    );
  };
});

jest.mock('@/components/charts/PieChart', () => {
  return function MockPieChart({ title, data }: any) {
    return (
      <div data-testid="pie-chart">
        <h3>{title}</h3>
        <div>{data.length} data points</div>
      </div>
    );
  };
});

// Mock i18n context
const mockT = (key: string) => {
  const translations: Record<string, string> = {
    'analytics.usageHistory': 'Usage History',
    'analytics.last7Days': 'Last 7 Days',
    'analytics.last30Days': 'Last 30 Days',
    'analytics.last3Months': 'Last 3 Months',
    'analytics.last12Months': 'Last 12 Months',
    'analytics.trends': 'Trends',
    'analytics.breakdown': 'Breakdown',
    'analytics.insights': 'Insights',
    'analytics.totalSessions': 'Total Sessions',
    'analytics.totalMinutes': 'Total Minutes',
    'analytics.planUtilization': 'Plan Utilization',
    'analytics.totalCost': 'Total Cost',
    'analytics.fromPrevious': 'from previous',
    'analytics.hours': 'hours',
    'analytics.usageTrends': 'Usage Trends',
    'analytics.monthlyComparison': 'Monthly Comparison',
    'analytics.performanceMetrics': 'Performance Metrics',
    'analytics.usageDistribution': 'Usage Distribution',
    'analytics.costBreakdown': 'Cost Breakdown',
    'analytics.predictions': 'Usage Predictions',
    'analytics.personalizedInsights': 'Personalized Insights',
    'analytics.noInsightsAvailable': 'No insights available',
    'common.export': 'Export',
    'common.error': 'Error',
    'common.retry': 'Retry'
  };
  return translations[key] || key;
};

jest.mock('@/contexts/i18n-context', () => ({
  useI18n: () => ({ t: mockT })
}));

// Mock fetch
global.fetch = jest.fn();

describe('UsageHistory', () => {
  const mockUserId = 'user-123';
  
  const mockUsageData = [
    {
      date: '2024-01-01',
      sessions: 10,
      minutes: 120,
      hours: 2,
      transcriptions: 15,
      exports: 3,
      cost: 5.50,
      utilization: 75,
      success_rate: 95,
      avg_duration: 12
    },
    {
      date: '2024-01-02',
      sessions: 15,
      minutes: 180,
      hours: 3,
      transcriptions: 20,
      exports: 5,
      cost: 8.25,
      utilization: 85,
      success_rate: 98,
      avg_duration: 12
    }
  ];

  const mockInsights = [
    {
      type: 'pattern',
      title: 'Peak Usage Day',
      message: 'You use the platform most on Mondays',
      suggestion: 'Consider scheduling heavy tasks on this day',
      priority: 'medium'
    }
  ];

  const mockPredictions = {
    predicted_sessions: 50,
    predicted_minutes: 600,
    estimated_limit_date: '2024-02-15',
    confidence: 0.85,
    recommendation: 'Consider upgrading your plan',
    growth_rate: 15,
    current_trend: 'growing'
  };

  beforeEach(() => {
    // Reset fetch mock
    (fetch as jest.Mock).mockReset();
  });

  it('renders loading state initially', () => {
    // Mock pending fetch
    (fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<UsageHistory userId={mockUserId} />);

    expect(screen.getByText('Usage History')).toBeInTheDocument();
    
    // Should show loading skeleton
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('renders usage data successfully', async () => {
    // Mock successful API responses
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockInsights)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPredictions)
      });

    render(<UsageHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Should show summary cards
    expect(screen.getByText('Total Sessions')).toBeInTheDocument();
    expect(screen.getByText('Total Minutes')).toBeInTheDocument();
    expect(screen.getByText('Plan Utilization')).toBeInTheDocument();
    expect(screen.getByText('Total Cost')).toBeInTheDocument();

    // Should show tab navigation
    expect(screen.getByText('Trends')).toBeInTheDocument();
    expect(screen.getByText('Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Insights')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(<UsageHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('changes period when dropdown selection changes', async () => {
    // Mock successful API response
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUsageData)
    });

    render(<UsageHistory userId={mockUserId} defaultPeriod="30d" />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Find and change period selector
    const periodSelector = screen.getByDisplayValue('Last 30 Days');
    fireEvent.change(periodSelector, { target: { value: '7d' } });

    // Should trigger new API call
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('period=7d')
      );
    });
  });

  it('switches between tabs correctly', async () => {
    // Mock successful API responses
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockInsights)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPredictions)
      });

    render(<UsageHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Initially on trends tab - should show line chart
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();

    // Click breakdown tab
    const breakdownTab = screen.getByText('Breakdown');
    fireEvent.click(breakdownTab);

    // Should show breakdown charts
    await waitFor(() => {
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });

    // Click insights tab
    const insightsTab = screen.getByText('Insights');
    fireEvent.click(insightsTab);

    // Should show insights and predictions
    await waitFor(() => {
      expect(screen.getByText('Usage Predictions')).toBeInTheDocument();
      expect(screen.getByText('Personalized Insights')).toBeInTheDocument();
    });
  });

  it('displays summary statistics correctly', async () => {
    // Mock successful API response
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUsageData)
    });

    render(<UsageHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Check summary calculations
    // Total sessions: 10 + 15 = 25
    expect(screen.getByText('25')).toBeInTheDocument();
    
    // Total minutes: 120 + 180 = 300
    expect(screen.getByText('300.0')).toBeInTheDocument();
    
    // Total cost: 5.50 + 8.25 = 13.75
    expect(screen.getByText('$13.75')).toBeInTheDocument();
  });

  it('shows predictions when enabled', async () => {
    // Mock successful API responses
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockInsights)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPredictions)
      });

    render(<UsageHistory userId={mockUserId} showPredictions={true} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Click insights tab
    const insightsTab = screen.getByText('Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('Usage Predictions')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument(); // predicted sessions
      expect(screen.getByText('600')).toBeInTheDocument(); // predicted minutes
      expect(screen.getByText('85%')).toBeInTheDocument(); // confidence
    });
  });

  it('shows insights when enabled', async () => {
    // Mock successful API responses
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockInsights)
      });

    render(<UsageHistory userId={mockUserId} showInsights={true} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Click insights tab
    const insightsTab = screen.getByText('Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('Personalized Insights')).toBeInTheDocument();
      expect(screen.getByText('Peak Usage Day')).toBeInTheDocument();
      expect(screen.getByText('You use the platform most on Mondays')).toBeInTheDocument();
    });
  });

  it('handles export functionality', async () => {
    // Mock successful API response
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUsageData)
    });

    // Mock blob and URL.createObjectURL
    const mockBlob = new Blob(['test data'], { type: 'text/csv' });
    global.URL.createObjectURL = jest.fn(() => 'mock-url');
    global.URL.revokeObjectURL = jest.fn();

    // Mock createElement and appendChild/removeChild
    const mockAnchor = {
      href: '',
      download: '',
      click: jest.fn()
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
    jest.spyOn(document.body, 'appendChild').mockImplementation();
    jest.spyOn(document.body, 'removeChild').mockImplementation();

    render(<UsageHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Find export dropdown and select CSV
    const exportDropdown = screen.getByDisplayValue('Export');
    fireEvent.change(exportDropdown, { target: { value: 'csv' } });

    // Should trigger export
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/usage/export?format=csv')
      );
    });
  });

  it('shows empty insights state when no insights available', async () => {
    // Mock successful API responses with empty insights
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]) // Empty insights
      });

    render(<UsageHistory userId={mockUserId} showInsights={true} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Click insights tab
    const insightsTab = screen.getByText('Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('No insights available')).toBeInTheDocument();
    });
  });

  it('calculates trend indicators correctly', async () => {
    const trendData = [
      { date: '2024-01-01', sessions: 5, minutes: 60, hours: 1, transcriptions: 8, exports: 1, cost: 2.50, utilization: 50, success_rate: 90, avg_duration: 12 },
      { date: '2024-01-02', sessions: 10, minutes: 120, hours: 2, transcriptions: 15, exports: 3, cost: 5.50, utilization: 75, success_rate: 95, avg_duration: 12 },
      { date: '2024-01-03', sessions: 15, minutes: 180, hours: 3, transcriptions: 20, exports: 5, cost: 8.25, utilization: 85, success_rate: 98, avg_duration: 12 },
      { date: '2024-01-04', sessions: 20, minutes: 240, hours: 4, transcriptions: 25, exports: 7, cost: 11.00, utilization: 95, success_rate: 99, avg_duration: 12 }
    ];

    // Mock successful API response with trending up data
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(trendData)
    });

    render(<UsageHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Usage History')).toBeInTheDocument();
    });

    // Should show upward trend indicator
    const trendIndicators = document.querySelectorAll('span');
    const hasTrendIcon = Array.from(trendIndicators).some(span => 
      span.textContent === '↗️'
    );
    expect(hasTrendIcon).toBe(true);
  });

  it('retries data fetch on error', async () => {
    // Mock API error first, then success
    (fetch as jest.Mock)
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData)
      });

    render(<UsageHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
    });

    // Click retry button
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    // Should succeed on retry
    await waitFor(() => {
      expect(screen.getByText('Total Sessions')).toBeInTheDocument();
    });
  });
});