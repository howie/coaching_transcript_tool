import React, { useState, useEffect, useCallback } from 'react';
import { useI18n } from '@/contexts/i18n-context';
import LineChart from '@/components/charts/LineChart';
import BarChart from '@/components/charts/BarChart';
import PieChart from '@/components/charts/PieChart';

interface UsageDataPoint {
  date: string;
  sessions: number;
  minutes: number;
  hours: number;
  transcriptions: number;
  exports: number;
  cost: number;
  utilization: number;
  success_rate: number;
  avg_duration: number;
  [key: string]: string | number;
}

interface UsageInsight {
  type: 'pattern' | 'optimization' | 'trend' | 'warning' | 'cost';
  title: string;
  message: string;
  suggestion: string;
  priority: 'low' | 'medium' | 'high';
  action?: string;
}

interface UsagePrediction {
  predicted_sessions: number;
  predicted_minutes: number;
  estimated_limit_date: string | null;
  confidence: number;
  recommendation: string;
  growth_rate: number;
  current_trend: 'growing' | 'stable' | 'declining';
}

interface UsageHistoryProps {
  userId: string;
  userPlan?: string;
  defaultPeriod?: '7d' | '30d' | '3m' | '12m';
  showInsights?: boolean;
  showPredictions?: boolean;
}

type PeriodType = '7d' | '30d' | '3m' | '12m';

const UsageHistory: React.FC<UsageHistoryProps> = ({
  userId,
  userPlan = 'free',
  defaultPeriod = '30d',
  showInsights = true,
  showPredictions = true
}) => {
  const { t } = useI18n();
  const [period, setPeriod] = useState<PeriodType>(defaultPeriod);
  const [data, setData] = useState<UsageDataPoint[]>([]);
  const [insights, setInsights] = useState<UsageInsight[]>([]);
  const [predictions, setPredictions] = useState<UsagePrediction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'trends' | 'breakdown' | 'insights'>('trends');

  // Chart configuration
  const chartConfig = {
    sessions: { 
      color: '#FFB800', 
      label: t('sessions.sessions'), 
      unit: '' 
    },
    minutes: { 
      color: '#4ECDC4', 
      label: t('usage.audioMinutes'), 
      unit: ' min' 
    },
    transcriptions: { 
      color: '#FF6B6B', 
      label: t('sessions.transcriptions'), 
      unit: '' 
    },
    cost: { 
      color: '#9B59B6', 
      label: t('billing.cost'), 
      unit: ' USD' 
    }
  };

  const utilizationConfig = {
    utilization: { 
      color: '#3498DB', 
      label: t('billing.utilization'), 
      unit: '%' 
    }
  };

  const performanceConfig = {
    success_rate: { 
      color: '#2ECC71', 
      label: t('analytics.successRate'), 
      unit: '%' 
    },
    avg_duration: { 
      color: '#E67E22', 
      label: t('analytics.avgDuration'), 
      unit: ' min' 
    }
  };

  // Helper function to generate mock usage data
  const generateMockUsageData = (period: PeriodType): UsageDataPoint[] => {
    const now = new Date();
    const days = period === '7d' ? 7 : period === '30d' ? 30 : period === '3m' ? 90 : 365;
    const data: UsageDataPoint[] = [];
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Generate realistic random data
      const baseSessions = Math.floor(Math.random() * 10) + 1;
      const sessions = Math.max(0, baseSessions + Math.floor(Math.random() * 5) - 2);
      const avgDuration = 8 + Math.random() * 12; // 8-20 minutes average
      const minutes = sessions * avgDuration;
      const hours = minutes / 60;
      const transcriptions = Math.ceil(sessions * (1.2 + Math.random() * 0.3)); // 1.2-1.5x sessions
      const exports = Math.floor(sessions * (0.1 + Math.random() * 0.2)); // 10-30% export rate
      const cost = minutes * 0.015; // $0.015 per minute
      const utilization = Math.min(100, (minutes / 600) * 100); // Assuming 600 min plan
      const success_rate = 85 + Math.random() * 15; // 85-100%
      
      data.push({
        date: date.toISOString().split('T')[0],
        sessions,
        minutes: Math.round(minutes * 100) / 100,
        hours: Math.round(hours * 100) / 100,
        transcriptions,
        exports,
        cost: Math.round(cost * 100) / 100,
        utilization: Math.round(utilization * 100) / 100,
        success_rate: Math.round(success_rate * 100) / 100,
        avg_duration: Math.round(avgDuration * 100) / 100
      });
    }
    
    return data;
  };

  const fetchUsageData = useCallback(async () => {
    try {
      setLoading(true);

      // Use real API call to backend
      const { apiClient } = await import('@/lib/api');
      const usageData = await apiClient.getUsageHistory(period, 'day');

      // Transform backend data to match component interface
      const transformedData = usageData.map((item: any) => ({
        date: item.date,
        sessions: item.sessions || 0,
        minutes: item.minutes || 0,
        hours: item.hours || 0,
        transcriptions: item.transcriptions || 0,
        exports: item.exports || 0,
        cost: item.cost || 0,
        utilization: item.utilization || 0,
        success_rate: item.success_rate || 0,
        avg_duration: item.avg_duration || 0
      }));

      setData(transformedData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch usage data:', err);
      // Fallback to mock data if API fails
      const mockData = generateMockUsageData(period);
      setData(mockData);
      setError('Failed to load real usage data, showing sample data');
    } finally {
      setLoading(false);
    }
  }, [period]);

  const fetchInsights = useCallback(async () => {
    try {
      // Use real API call to backend
      const { apiClient } = await import('@/lib/api');
      const insights = await apiClient.getUsageInsights();

      setInsights(insights);
    } catch (err) {
      console.error('Failed to fetch usage insights:', err);
      // Fallback to mock insights if API fails
      const mockInsights: UsageInsight[] = [
        {
          type: 'pattern',
          title: t('analytics.peakUsageDay'),
          message: 'You use the platform most on Mondays',
          suggestion: 'Consider scheduling heavy transcription tasks on this day',
          priority: 'medium'
        },
        {
          type: 'optimization',
          title: t('analytics.lowUtilization'),
          message: 'You\'re using only 45% of your plan capacity',
          suggestion: 'You might consider a smaller plan to save costs',
          priority: 'low'
        }
      ];
      setInsights(mockInsights);
    }
  }, [t]);

  const fetchPredictions = useCallback(async () => {
    try {
      // Use real API call to backend
      const { apiClient } = await import('@/lib/api');
      const predictions = await apiClient.getUsagePredictions();

      setPredictions(predictions);
    } catch (err) {
      console.error('Failed to fetch usage predictions:', err);
      // Fallback to mock predictions if API fails
      const mockPredictions: UsagePrediction = {
        predicted_sessions: 25,
        predicted_minutes: 450,
        estimated_limit_date: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(),
        confidence: 0.78,
        recommendation: 'Your usage is growing steadily. Consider upgrading to PRO plan soon.',
        growth_rate: 12,
        current_trend: 'growing'
      };
      setPredictions(mockPredictions);
    }
  }, []);

  useEffect(() => {
    fetchUsageData();
  }, [fetchUsageData]);

  useEffect(() => {
    if (showInsights) {
      fetchInsights();
    }
    if (showPredictions) {
      fetchPredictions();
    }
  }, [showInsights, showPredictions, fetchInsights, fetchPredictions]);

  const exportData = async (format: 'csv' | 'pdf' | 'json') => {
    try {
      // Map csv/pdf to xlsx/txt as per WP6-Cleanup-4 correction
      const actualFormat = format === 'csv' ? 'xlsx' : format === 'pdf' ? 'txt' : format;

      const { apiClient } = await import('@/lib/api');

      if (actualFormat === 'json') {
        const data = await apiClient.exportUsageData(actualFormat, period);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `usage-history-${period}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const blob = await apiClient.exportUsageData(actualFormat, period);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `usage-history-${period}.${actualFormat}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error('Export failed:', err);
      alert('Export failed. Please try again later.');
    }
  };

  const calculateSummaryStats = () => {
    if (!data.length) return null;

    const totalSessions = data.reduce((sum, point) => sum + point.sessions, 0);
    const totalMinutes = data.reduce((sum, point) => sum + point.minutes, 0);
    const totalTranscriptions = data.reduce((sum, point) => sum + point.transcriptions, 0);
    const totalCost = data.reduce((sum, point) => sum + point.cost, 0);
    const avgUtilization = data.reduce((sum, point) => sum + point.utilization, 0) / data.length;
    
    // Calculate changes compared to previous period
    const halfPoint = Math.floor(data.length / 2);
    const earlyPeriod = data.slice(0, halfPoint);
    const latePeriod = data.slice(halfPoint);
    
    const earlyAvg = earlyPeriod.reduce((sum, point) => sum + point.sessions, 0) / earlyPeriod.length;
    const lateAvg = latePeriod.reduce((sum, point) => sum + point.sessions, 0) / latePeriod.length;
    const sessionChange = earlyAvg > 0 ? ((lateAvg - earlyAvg) / earlyAvg) * 100 : 0;
    
    return {
      totalSessions,
      totalMinutes,
      totalHours: totalMinutes / 60,
      totalTranscriptions,
      totalCost,
      avgUtilization,
      sessionChange,
      sessionTrend: sessionChange > 5 ? 'up' : sessionChange < -5 ? 'down' : 'stable'
    };
  };

  const getSummaryCardClass = (trend: string) => {
    switch (trend) {
      case 'up': return 'border-l-4 border-l-green-500';
      case 'down': return 'border-l-4 border-l-red-500';
      default: return 'border-l-4 border-l-blue-500';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '↗️';
      case 'down': return '↘️';
      default: return '→';
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'pattern': return '📊';
      case 'optimization': return '⚡';
      case 'trend': return '📈';
      case 'warning': return '⚠️';
      case 'cost': return '💰';
      default: return '💡';
    }
  };

  const getInsightPriorityClass = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-l-red-500 bg-red-50';
      case 'medium': return 'border-l-yellow-500 bg-yellow-50';
      default: return 'border-l-blue-500 bg-blue-50';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-content-primary">
            {t('analytics.usageHistory')}
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-dashboard-card border border-border rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-border rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-border rounded w-3/4"></div>
            </div>
          ))}
        </div>
        <div className="bg-dashboard-card border border-border rounded-lg p-6 animate-pulse">
          <div className="h-64 bg-border rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dashboard-card border border-border rounded-lg p-6">
        <div className="text-center text-content-secondary">
          <p className="text-lg mb-2">😔 {t('common.error')}</p>
          <p>{error}</p>
          <button 
            onClick={fetchUsageData}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
          >
            {t('common.retry')}
          </button>
        </div>
      </div>
    );
  }

  const summaryStats = calculateSummaryStats();

  // Check if user has access to usage history (Enterprise only)
  const hasAccess = userPlan === 'business' || userPlan === 'enterprise';

  if (!hasAccess) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-3 mb-8">
          <h2 className="text-2xl font-bold text-content-primary">
            {t('analytics.usageHistory')}
          </h2>
        </div>

        {/* Enterprise Only Message */}
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 p-8 rounded-lg text-white text-center">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">📊</span>
            </div>
            <h3 className="text-2xl font-bold mb-3">
              {t('analytics.enterpriseFeature')}
            </h3>
            <p className="text-purple-100 mb-6 leading-relaxed">
              {t('analytics.enterpriseFeatureDescription')}
            </p>
            <div className="space-y-3 text-sm text-purple-100 mb-6">
              <div className="flex items-center justify-center">
                <span className="mr-2">✨</span>
                <span>{t('analytics.detailedUsageTrends')}</span>
              </div>
              <div className="flex items-center justify-center">
                <span className="mr-2">🔮</span>
                <span>{t('analytics.predictiveAnalytics')}</span>
              </div>
              <div className="flex items-center justify-center">
                <span className="mr-2">📈</span>
                <span>{t('analytics.advancedInsights')}</span>
              </div>
              <div className="flex items-center justify-center">
                <span className="mr-2">📊</span>
                <span>{t('analytics.customReports')}</span>
              </div>
            </div>
            <button
              onClick={() => window.location.href = '/dashboard/billing/change-plan'}
              className="bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold hover:bg-purple-50 transition-colors inline-flex items-center"
            >
              <span className="mr-2">🚀</span>
              {t('billing.upgradeToEnterprise')}
            </button>
          </div>
        </div>

        {/* Preview Feature List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-dashboard-card border border-border rounded-lg p-6 opacity-50">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">📈</span>
              <h3 className="font-semibold text-content-primary">{t('analytics.usageTrends')}</h3>
            </div>
            <p className="text-content-secondary text-sm">
              {t('analytics.usageTrendsPreview')}
            </p>
          </div>

          <div className="bg-dashboard-card border border-border rounded-lg p-6 opacity-50">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">💡</span>
              <h3 className="font-semibold text-content-primary">{t('analytics.insights')}</h3>
            </div>
            <p className="text-content-secondary text-sm">
              {t('analytics.insightsPreview')}
            </p>
          </div>

          <div className="bg-dashboard-card border border-border rounded-lg p-6 opacity-50">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">📊</span>
              <h3 className="font-semibold text-content-primary">{t('analytics.breakdown')}</h3>
            </div>
            <p className="text-content-secondary text-sm">
              {t('analytics.breakdownPreview')}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with period selector and export */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-content-primary">
          {t('analytics.usageHistory')}
        </h2>
        
        <div className="flex flex-col sm:flex-row gap-2">
          {/* Period Selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as PeriodType)}
            className="px-3 py-2 border border-border rounded-lg bg-surface text-content-primary focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="7d">{t('analytics.last7Days')}</option>
            <option value="30d">{t('analytics.last30Days')}</option>
            <option value="3m">{t('analytics.last3Months')}</option>
            <option value="12m">{t('analytics.last12Months')}</option>
          </select>
          
          {/* Export Dropdown */}
          <select
            onChange={(e) => {
              if (e.target.value) {
                exportData(e.target.value as 'csv' | 'pdf' | 'json');
                e.target.value = '';
              }
            }}
            className="px-3 py-2 border border-border rounded-lg bg-surface text-content-primary focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">{t('common.export')}</option>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
            <option value="json">JSON</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      {summaryStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className={`bg-dashboard-card border border-border rounded-lg p-4 ${getSummaryCardClass(summaryStats.sessionTrend)}`}>
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm text-content-secondary">{t('analytics.totalSessions')}</p>
                <p className="text-2xl font-bold text-content-primary">{summaryStats.totalSessions}</p>
              </div>
              <span className="text-2xl">{getTrendIcon(summaryStats.sessionTrend)}</span>
            </div>
            {summaryStats.sessionChange !== 0 && (
              <p className={`text-xs mt-2 ${summaryStats.sessionChange > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {summaryStats.sessionChange > 0 ? '+' : ''}{summaryStats.sessionChange.toFixed(1)}% {t('analytics.fromPrevious')}
              </p>
            )}
          </div>

          <div className="bg-dashboard-card border border-border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm text-content-secondary">{t('analytics.totalMinutes')}</p>
                <p className="text-2xl font-bold text-content-primary">{summaryStats.totalMinutes.toFixed(1)}</p>
              </div>
              <span className="text-2xl">⏱️</span>
            </div>
            <p className="text-xs text-content-secondary mt-2">
              {summaryStats.totalHours.toFixed(1)} {t('analytics.hours')}
            </p>
          </div>

          <div className="bg-dashboard-card border border-border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm text-content-secondary">{t('analytics.planUtilization')}</p>
                <p className="text-2xl font-bold text-content-primary">{summaryStats.avgUtilization.toFixed(1)}%</p>
              </div>
              <span className="text-2xl">📊</span>
            </div>
          </div>

          <div className="bg-dashboard-card border border-border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm text-content-secondary">{t('analytics.totalCost')}</p>
                <p className="text-2xl font-bold text-content-primary">${summaryStats.totalCost.toFixed(2)}</p>
              </div>
              <span className="text-2xl">💰</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-border">
        <nav className="flex space-x-8">
          {[
            { id: 'trends', label: t('analytics.trends'), icon: '📈' },
            { id: 'breakdown', label: t('analytics.breakdown'), icon: '📊' },
            { id: 'insights', label: t('analytics.insights'), icon: '💡' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-content-secondary hover:text-content-primary hover:border-border'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* Main Usage Trends Chart */}
          <LineChart
            data={data}
            config={chartConfig}
            title={t('analytics.usageTrends')}
            height={350}
            showGrid
            showTooltip
            showLegend
            yAxisLabel={t('analytics.usage')}
            xAxisLabel={t('analytics.date')}
          />

          {/* Plan Utilization Chart */}
          <LineChart
            data={data}
            config={utilizationConfig}
            title={t('analytics.planUtilizationTrend')}
            height={250}
            showGrid
            showTooltip
            yAxisLabel={t('analytics.utilizationPercent')}
          />
        </div>
      )}

      {activeTab === 'breakdown' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Monthly Comparison Bar Chart */}
          <BarChart
            data={data.slice(-12).map(point => ({
              name: new Date(point.date).toLocaleDateString('en-US', { month: 'short' }),
              sessions: point.sessions,
              transcriptions: point.transcriptions
            }))}
            config={{
              sessions: chartConfig.sessions,
              transcriptions: chartConfig.transcriptions
            }}
            title={t('analytics.monthlyComparison')}
            height={300}
            showGrid
            showTooltip
            showLegend
          />

          {/* Performance Metrics */}
          <LineChart
            data={data}
            config={performanceConfig}
            title={t('analytics.performanceMetrics')}
            height={300}
            showGrid
            showTooltip
            showLegend
          />

          {/* Usage Distribution Pie Chart */}
          <PieChart
            data={[
              { name: t('sessions.sessions'), value: summaryStats?.totalSessions || 0 },
              { name: t('sessions.transcriptions'), value: summaryStats?.totalTranscriptions || 0 }
            ]}
            title={t('analytics.usageDistribution')}
            width={300}
            height={300}
          />

          {/* Cost Breakdown */}
          <div className="bg-dashboard-card border border-border rounded-lg p-6">
            <h3 className="text-lg font-semibold text-content-primary mb-4">
              {t('analytics.costBreakdown')}
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-content-secondary">{t('analytics.totalCost')}:</span>
                <span className="font-medium">${summaryStats?.totalCost.toFixed(2) || '0.00'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary">{t('analytics.costPerMinute')}:</span>
                <span className="font-medium">
                  ${summaryStats && summaryStats.totalMinutes > 0 
                    ? (summaryStats.totalCost / summaryStats.totalMinutes).toFixed(4) 
                    : '0.0000'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary">{t('analytics.costPerSession')}:</span>
                <span className="font-medium">
                  ${summaryStats && summaryStats.totalSessions > 0 
                    ? (summaryStats.totalCost / summaryStats.totalSessions).toFixed(2) 
                    : '0.00'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'insights' && (
        <div className="space-y-6">
          {/* Predictions */}
          {showPredictions && predictions && (
            <div className="bg-dashboard-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-content-primary mb-4 flex items-center">
                <span className="mr-2">🔮</span>
                {t('analytics.predictions')}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-sm text-content-secondary">{t('analytics.predictedSessions')}</p>
                  <p className="text-2xl font-bold text-content-primary">{predictions.predicted_sessions}</p>
                  <p className="text-xs text-content-secondary">{t('analytics.nextMonth')}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-content-secondary">{t('analytics.predictedMinutes')}</p>
                  <p className="text-2xl font-bold text-content-primary">{predictions.predicted_minutes}</p>
                  <p className="text-xs text-content-secondary">{t('analytics.nextMonth')}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-content-secondary">{t('analytics.confidence')}</p>
                  <p className="text-2xl font-bold text-content-primary">{(predictions.confidence * 100).toFixed(0)}%</p>
                  <p className="text-xs text-content-secondary">{t('analytics.predictionAccuracy')}</p>
                </div>
              </div>
              
              {predictions.recommendation && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <span className="font-medium">{t('analytics.recommendation')}:</span> {predictions.recommendation}
                  </p>
                </div>
              )}

              {predictions.estimated_limit_date && (
                <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <span className="font-medium">{t('analytics.estimatedLimitDate')}:</span> {new Date(predictions.estimated_limit_date).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Insights */}
          {showInsights && insights.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-content-primary flex items-center">
                <span className="mr-2">💡</span>
                {t('analytics.personalizedInsights')}
              </h3>
              {insights.map((insight, index) => (
                <div
                  key={index}
                  className={`border-l-4 p-4 bg-surface rounded-lg ${getInsightPriorityClass(insight.priority)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="mr-2">{getInsightIcon(insight.type)}</span>
                        <h4 className="font-medium text-content-primary">{insight.title}</h4>
                        <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                          insight.priority === 'high' ? 'bg-red-100 text-red-800' :
                          insight.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {insight.priority}
                        </span>
                      </div>
                      <p className="text-sm text-content-secondary mb-2">{insight.message}</p>
                      <p className="text-sm text-content-primary">{insight.suggestion}</p>
                    </div>
                    {insight.action && (
                      <button className="ml-4 px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary-dark transition-colors">
                        {t(`actions.${insight.action}`)}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty state for insights */}
          {showInsights && insights.length === 0 && (
            <div className="bg-dashboard-card border border-border rounded-lg p-6 text-center">
              <p className="text-content-secondary">
                {t('analytics.noInsightsAvailable')}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UsageHistory;