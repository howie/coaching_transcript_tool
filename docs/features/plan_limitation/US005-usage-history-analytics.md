# US005: Usage History & Analytics

## 📋 User Story

**As a** platform user  
**I want** to view my historical usage patterns and trends  
**So that** I can optimize my subscription and predict future needs

## 💼 Business Value

### Current Problem
- No visibility into historical usage patterns
- Cannot predict when limits will be reached
- No insights into usage trends over time
- Difficult to justify plan upgrades

### Business Impact
- **Unexpected Limits**: Users hit limits without warning
- **Suboptimal Plans**: Users on wrong plan for their needs
- **Churn Risk**: Frustration from lack of transparency
- **Lost Revenue**: Users don't upgrade proactively

### Value Delivered
- **Usage Insights**: Clear visualization of usage trends
- **Predictive Warnings**: Forecast when limits will be reached
- **Data-Driven Decisions**: Historical data for plan selection
- **Proactive Upgrades**: Users upgrade before hitting limits

## 🎯 Acceptance Criteria

### Usage History Dashboard
1. **Time Range Selection**
   - [ ] Last 7 days view
   - [ ] Last 30 days view
   - [ ] Last 3 months view
   - [ ] Last 12 months view
   - [ ] Custom date range picker

2. **Metrics Visualization**
   - [ ] Line charts for usage over time
   - [ ] Bar charts for monthly comparisons
   - [ ] Stacked charts for multiple metrics
   - [ ] Trend indicators (up/down/stable)
   - [ ] Peak usage highlights

3. **Detailed Metrics**
   - [ ] Sessions created per period
   - [ ] Audio minutes processed
   - [ ] Transcriptions completed
   - [ ] Export operations
   - [ ] Storage usage over time

### Analytics Features
4. **Usage Patterns**
   - [ ] Daily usage patterns
   - [ ] Weekly trends
   - [ ] Monthly summaries
   - [ ] Seasonal variations
   - [ ] Usage heatmap

5. **Predictive Analytics**
   - [ ] Projected usage for current month
   - [ ] Estimated limit reach date
   - [ ] Recommended plan based on trends
   - [ ] Cost optimization suggestions
   - [ ] Usage efficiency score

6. **Comparative Analysis**
   - [ ] Month-over-month comparison
   - [ ] Year-over-year growth
   - [ ] Usage vs. plan limits
   - [ ] Utilization percentage trends
   - [ ] Peer comparison (anonymized)

### Export & Reporting
7. **Data Export**
   - [ ] CSV export of raw data
   - [ ] PDF reports generation
   - [ ] Email monthly summaries
   - [ ] API access for data
   - [ ] Scheduled reports

8. **Insights & Recommendations**
   - [ ] Usage anomaly detection
   - [ ] Optimization tips
   - [ ] Best practices based on usage
   - [ ] Cost-saving opportunities
   - [ ] Feature utilization analysis

## 🏗️ Technical Implementation

### Database Schema
```sql
-- Usage history tracking
CREATE TABLE usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- 'hourly', 'daily', 'monthly'
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Metrics
    sessions_created INTEGER DEFAULT 0,
    audio_minutes_processed DECIMAL(10,2) DEFAULT 0,
    transcriptions_completed INTEGER DEFAULT 0,
    exports_generated INTEGER DEFAULT 0,
    storage_used_mb DECIMAL(10,2) DEFAULT 0,
    
    -- Additional metrics
    unique_clients INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    concurrent_sessions_peak INTEGER DEFAULT 0,
    
    -- Plan context
    plan_name VARCHAR(20),
    plan_limits JSONB,
    
    -- Indexes for performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_user_period UNIQUE (user_id, period_type, period_start)
);

CREATE INDEX idx_usage_history_user_period ON usage_history(user_id, period_start DESC);
CREATE INDEX idx_usage_history_recorded ON usage_history(recorded_at DESC);
```

### API Endpoints
```typescript
// Usage history endpoints
GET /api/usage/history
  ?period=7d|30d|3m|12m|custom
  &from=2024-01-01
  &to=2024-12-31
  &metrics=sessions,minutes,transcriptions
  &groupBy=day|week|month

GET /api/usage/analytics
  ?type=trends|patterns|predictions
  
GET /api/usage/insights
  Returns personalized insights and recommendations

GET /api/usage/export
  ?format=csv|pdf|json
  &period=last_month
  
POST /api/usage/subscribe
  Subscribe to email reports
```

### React Components

```typescript
// components/billing/UsageHistory.tsx
import { LineChart, BarChart, AreaChart } from '@/components/charts';

interface UsageHistoryProps {
  userId: string;
  defaultPeriod?: '7d' | '30d' | '3m' | '12m';
}

export function UsageHistory({ userId, defaultPeriod = '30d' }: UsageHistoryProps) {
  const [period, setPeriod] = useState(defaultPeriod);
  const [data, setData] = useState<UsageData[]>([]);
  const [insights, setInsights] = useState<Insights>();
  
  // Chart configuration
  const chartConfig = {
    sessions: { color: '#FFB800', label: 'Sessions' },
    minutes: { color: '#4ECDC4', label: 'Audio Minutes' },
    transcriptions: { color: '#FF6B6B', label: 'Transcriptions' }
  };
  
  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <PeriodSelector value={period} onChange={setPeriod} />
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Sessions"
          value={data.totalSessions}
          change={data.sessionChange}
          trend={data.sessionTrend}
        />
        {/* More summary cards... */}
      </div>
      
      {/* Main Chart */}
      <div className="bg-dashboard-card p-6 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">Usage Trends</h3>
        <LineChart
          data={data}
          config={chartConfig}
          height={300}
          showGrid
          showTooltip
          showLegend
        />
      </div>
      
      {/* Insights Panel */}
      <InsightsPanel insights={insights} />
      
      {/* Detailed Breakdown */}
      <UsageBreakdown data={data} />
    </div>
  );
}
```

### Data Aggregation Service
```python
# services/usage_analytics_service.py

class UsageAnalyticsService:
    """Service for usage history and analytics."""
    
    def record_usage_snapshot(self, user_id: str):
        """Record current usage snapshot."""
        current_usage = self.get_current_usage(user_id)
        
        # Record hourly snapshot
        self.db.execute("""
            INSERT INTO usage_history (
                user_id, period_type, period_start, period_end,
                sessions_created, audio_minutes_processed,
                transcriptions_completed, exports_generated,
                storage_used_mb, plan_name
            ) VALUES (%s, 'hourly', %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, period_type, period_start)
            DO UPDATE SET
                sessions_created = EXCLUDED.sessions_created,
                audio_minutes_processed = EXCLUDED.audio_minutes_processed,
                -- etc...
        """, params)
    
    def get_usage_trends(self, user_id: str, period: str):
        """Get usage trends for specified period."""
        end_date = datetime.now()
        start_date = self._calculate_start_date(period)
        
        data = self.db.query("""
            SELECT 
                DATE_TRUNC('day', period_start) as date,
                SUM(sessions_created) as sessions,
                SUM(audio_minutes_processed) as minutes,
                SUM(transcriptions_completed) as transcriptions
            FROM usage_history
            WHERE user_id = %s
                AND period_start BETWEEN %s AND %s
                AND period_type = 'hourly'
            GROUP BY DATE_TRUNC('day', period_start)
            ORDER BY date
        """, [user_id, start_date, end_date])
        
        return self._format_trend_data(data)
    
    def predict_usage(self, user_id: str):
        """Predict future usage based on historical patterns."""
        historical_data = self.get_usage_trends(user_id, '3m')
        
        # Simple linear regression for prediction
        from sklearn.linear_model import LinearRegression
        
        model = LinearRegression()
        X = np.array(range(len(historical_data))).reshape(-1, 1)
        y = [d['sessions'] for d in historical_data]
        
        model.fit(X, y)
        
        # Predict next 30 days
        future_X = np.array(range(len(historical_data), 
                                  len(historical_data) + 30)).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        return {
            'predicted_sessions': predictions.sum(),
            'estimated_limit_date': self._calculate_limit_date(predictions),
            'confidence': model.score(X, y),
            'recommendation': self._get_plan_recommendation(predictions)
        }
    
    def generate_insights(self, user_id: str):
        """Generate personalized usage insights."""
        usage_data = self.get_usage_trends(user_id, '30d')
        patterns = self._analyze_patterns(usage_data)
        
        insights = []
        
        # Peak usage times
        if patterns['peak_day']:
            insights.append({
                'type': 'pattern',
                'title': 'Peak Usage Day',
                'message': f'You use the platform most on {patterns["peak_day"]}s',
                'suggestion': 'Consider scheduling heavy tasks on this day'
            })
        
        # Usage efficiency
        if patterns['utilization'] < 50:
            insights.append({
                'type': 'optimization',
                'title': 'Low Plan Utilization',
                'message': f'You're using only {patterns["utilization"]}% of your plan',
                'suggestion': 'Consider downgrading to save costs'
            })
        
        # Growth trend
        if patterns['growth_rate'] > 20:
            insights.append({
                'type': 'trend',
                'title': 'Rapid Growth',
                'message': f'Your usage has grown {patterns["growth_rate"]}% this month',
                'suggestion': 'You may need to upgrade soon'
            })
        
        return insights
```

### Scheduled Jobs
```python
# tasks/usage_aggregation_tasks.py

@celery.task
def aggregate_hourly_usage():
    """Aggregate usage data every hour."""
    users = get_all_active_users()
    
    for user in users:
        service.record_usage_snapshot(user.id)
    
@celery.task
def generate_daily_rollups():
    """Generate daily usage rollups."""
    yesterday = datetime.now() - timedelta(days=1)
    
    db.execute("""
        INSERT INTO usage_history (user_id, period_type, period_start, ...)
        SELECT 
            user_id,
            'daily' as period_type,
            DATE_TRUNC('day', period_start),
            ...
        FROM usage_history
        WHERE period_type = 'hourly'
            AND DATE_TRUNC('day', period_start) = %s
        GROUP BY user_id, DATE_TRUNC('day', period_start)
    """, [yesterday])

@celery.task
def send_monthly_reports():
    """Send monthly usage reports to subscribed users."""
    subscribed_users = get_report_subscribers()
    
    for user in subscribed_users:
        report = generate_monthly_report(user.id)
        send_email(
            to=user.email,
            subject='Your Monthly Usage Report',
            template='usage_report.html',
            context={'report': report}
        )
```

## 🎨 UI/UX Specifications

### Chart Design
1. **Color Palette**
   - Sessions: #FFB800 (Dashboard accent)
   - Minutes: #4ECDC4 (Teal)
   - Transcriptions: #FF6B6B (Coral)
   - Background: Dashboard card colors

2. **Interactive Elements**
   - Hover tooltips with exact values
   - Click to drill down
   - Zoom and pan on charts
   - Export chart as image

3. **Responsive Behavior**
   - Mobile: Simplified charts, swipeable
   - Tablet: 2-column layout
   - Desktop: Full dashboard view

### Loading States
- Skeleton screens for charts
- Progressive data loading
- Cached previous view
- Optimistic updates

## 🧪 Test Scenarios

### Unit Tests
- Data aggregation logic
- Prediction algorithms
- Insight generation
- Chart data formatting

### Integration Tests
- API endpoint responses
- Data flow from backend
- Chart rendering
- Export functionality

### Performance Tests
- Large dataset handling (1M+ records)
- Chart rendering speed
- API response times
- Cache effectiveness

## 📊 Success Metrics

### User Engagement
- 70% of users view history monthly
- Average session time: 3+ minutes
- Export usage: 30% of users
- Email report subscriptions: 40%

### Technical Performance
- Chart load time: <1 second
- API response: <300ms
- Data freshness: <1 hour
- Cache hit rate: >80%

### Business Impact
- Proactive upgrades: +30%
- Support tickets: -25%
- User retention: +15%
- Feature adoption: +40%

## 📋 Definition of Done

- [ ] Database schema implemented
- [ ] API endpoints functional
- [ ] React components built
- [ ] Charts integrated
- [ ] Insights algorithm working
- [ ] Export functionality complete
- [ ] Email reports configured
- [ ] Tests written (>80% coverage)
- [ ] Performance optimized
- [ ] Documentation complete
- [ ] Deployed to production

## 🔗 Dependencies

- Chart library (Recharts/D3.js)
- Data aggregation pipeline
- Email service for reports
- Export service (PDF generation)
- Analytics database optimization

## 🚀 Deployment Plan

### Phase 1: Data Collection (Week 1)
- Deploy usage tracking
- Start collecting historical data
- Test aggregation jobs

### Phase 2: Basic Visualization (Week 2)
- Deploy chart components
- Simple trend views
- Basic time range selection

### Phase 3: Advanced Features (Week 3)
- Predictions and insights
- Export functionality
- Email reports

### Phase 4: Optimization (Week 4)
- Performance tuning
- Cache implementation
- A/B testing

## 📝 Future Enhancements

1. **Machine Learning**
   - Anomaly detection
   - Advanced predictions
   - User segmentation
   - Churn prediction

2. **Comparative Analytics**
   - Industry benchmarks
   - Peer comparisons
   - Best practices

3. **Cost Analysis**
   - ROI calculations
   - Cost per session
   - Optimization recommendations

4. **API Analytics**
   - API usage patterns
   - Endpoint performance
   - Rate limit tracking

## 👥 Stakeholders

**Product Owner**: Analytics Team  
**Technical Lead**: Data Engineering  
**Designer**: Data Visualization Team  
**Data Scientist**: ML Team  
**QA Lead**: Performance Testing Team

---

**Last Updated**: 2025-08-15  
**Status**: Planning Complete  
**Priority**: High  
**Estimated Effort**: 4 weeks  
**Version**: 1.0.0