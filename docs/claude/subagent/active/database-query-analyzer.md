# Database Query Analyzer ✅ ACTIVE

**Status**: Available - Can be invoked via Task tool  
**Agent Type**: `database-query-analyzer`

## Overview

The database-query-analyzer specializes in querying and analyzing database information about system status, user growth, session processing, and system health. It provides insights into system performance and business metrics.

## Capabilities

- **System status monitoring** - Check current system health and performance
- **User growth analysis** - Track registration trends and user engagement
- **Session processing metrics** - Monitor transcription and processing statistics
- **Performance analysis** - Identify bottlenecks and optimization opportunities
- **Business intelligence** - Generate reports on key business metrics
- **Data validation** - Verify data integrity and consistency

## When to Use

### ✅ Ideal Scenarios
- **System health checks** - Monitor overall system performance
- **Business reporting** - Generate analytics and growth reports
- **Performance troubleshooting** - Identify database performance issues
- **Data analysis** - Understand user behavior and system usage
- **Capacity planning** - Analyze growth trends for infrastructure planning
- **Quality assurance** - Validate data integrity and consistency

### ✅ Common Use Cases
- **Daily health checks** - Regular system status monitoring
- **Growth analysis** - User registration and engagement trends
- **Performance monitoring** - Query performance and optimization
- **Business metrics** - Revenue, usage, and conversion analytics

## Usage Pattern

```typescript
// Invoke via Task tool
Task(
  subagent_type: "database-query-analyzer", 
  description: "Analyze system status",
  prompt: "Check the current system status and performance metrics. 
  Analyze user growth trends and identify any issues that need attention."
)
```

## Analysis Categories

### 1. System Status & Health
- **Database performance** - Query execution times and resource usage
- **System availability** - Uptime and error rates
- **Processing capacity** - Current load vs capacity limits
- **Error monitoring** - Recent errors and failure patterns

### 2. User Growth & Engagement  
- **Registration trends** - New user sign-ups over time
- **User activity** - Active users and engagement metrics
- **Plan distribution** - Breakdown by subscription plan
- **Retention analysis** - User retention and churn rates

### 3. Session Processing Analytics
- **Transcription volume** - Processing statistics and trends
- **Processing time** - Performance metrics and bottlenecks
- **Success rates** - Completion vs failure rates
- **Resource utilization** - STT provider usage and costs

### 4. Business Intelligence
- **Revenue metrics** - Subscription revenue and growth
- **Usage patterns** - Feature adoption and usage trends
- **Cost analysis** - Processing costs and profitability
- **Performance benchmarks** - Key performance indicators

## Examples

### System Health Check
```
Description: "Check current system status"
Prompt: "Analyze the current system status including database performance, 
recent error rates, processing capacity, and any issues that need immediate 
attention. Provide a comprehensive health report."
```

### User Growth Analysis
```
Description: "Analyze user growth patterns"
Prompt: "Generate a user growth analysis including registration trends over 
the past month, plan distribution, active user metrics, and retention rates. 
Identify any concerning patterns or opportunities."
```

### Performance Investigation
```
Description: "Investigate performance issues"
Prompt: "The system seems slower than usual. Analyze database query 
performance, identify slow queries, check for resource bottlenecks, and 
recommend optimizations."
```

### Business Metrics Report
```
Description: "Generate business metrics report"
Prompt: "Create a comprehensive business report including user growth, 
revenue trends, processing volume, cost analysis, and key performance 
indicators for the past month."
```

## Tool Usage

Primary tools for this agent:
- **Bash** - Execute database queries and system commands
- **Read** - Access configuration files and logs
- **Write** - Generate reports and analysis documents
- **Grep** - Search through logs and data files
- **WebFetch** - Access external monitoring services if needed

## Analysis Process

### 1. Data Collection
- Execute database queries for metrics
- Gather system performance data
- Collect relevant log information
- Access monitoring service data

### 2. Data Analysis
- Calculate key metrics and trends
- Identify patterns and anomalies
- Compare against historical data
- Detect performance issues

### 3. Insight Generation
- Interpret data patterns
- Identify root causes of issues
- Recommend optimization actions
- Predict future trends

### 4. Report Creation
- Structure findings clearly
- Provide actionable recommendations
- Include relevant visualizations
- Document methodology and assumptions

## Key Metrics Tracked

### System Health
- Database connection pool usage
- Query execution times
- Error rates and types
- System resource utilization

### User Metrics
- Daily/monthly active users
- New user registrations
- Plan upgrade/downgrade rates
- User retention cohorts

### Processing Metrics
- Transcription success rates
- Processing time distributions
- STT provider performance
- Cost per transcription

### Business Metrics
- Monthly recurring revenue (MRR)
- Customer lifetime value (CLV)
- Churn rates by plan
- Feature adoption rates

## Reporting Formats

### Health Check Reports
- **Executive summary** - High-level status overview
- **Detailed metrics** - Specific performance indicators
- **Issue identification** - Problems requiring attention
- **Recommendations** - Suggested actions and priorities

### Growth Analysis
- **Trend analysis** - Growth patterns and trajectories
- **Cohort analysis** - User behavior by registration period
- **Segmentation** - Analysis by user characteristics
- **Forecasting** - Projected growth scenarios

### Performance Reports
- **Query analysis** - Slow query identification and optimization
- **Resource monitoring** - CPU, memory, and database utilization
- **Bottleneck identification** - System constraints and solutions
- **Optimization recommendations** - Specific improvement actions

## Best Practices

### Query Optimization
- **Use appropriate indexes** - Ensure queries are properly indexed
- **Limit result sets** - Use pagination and filtering
- **Avoid expensive operations** - Minimize complex joins and calculations
- **Cache results** - Store frequently accessed metrics

### Data Interpretation
- **Consider context** - Understand business and technical context
- **Validate assumptions** - Cross-check findings with other data sources
- **Account for seasonality** - Consider time-based patterns
- **Document methodology** - Explain how metrics are calculated

### Report Quality
- **Clear visualizations** - Use appropriate charts and graphs
- **Actionable insights** - Focus on findings that enable decisions
- **Executive summaries** - Provide high-level overviews
- **Detailed appendices** - Include supporting data and methodology

## Common Queries

### User Analysis
```sql
-- User growth by plan
SELECT plan, COUNT(*) as users, 
       COUNT(*) / (SELECT COUNT(*) FROM users) * 100 as percentage
FROM users 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY plan;
```

### Session Processing
```sql
-- Processing success rates
SELECT status, COUNT(*) as count,
       COUNT(*) / (SELECT COUNT(*) FROM sessions) * 100 as percentage
FROM sessions 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY status;
```

### Performance Monitoring
```sql
-- Slow query identification
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000  -- queries taking > 1 second
ORDER BY mean_exec_time DESC;
```

## Integration with Monitoring

### External Services
- **Application monitoring** - Integration with APM tools
- **Log aggregation** - Centralized log analysis
- **Alerting systems** - Automated issue detection
- **Dashboard integration** - Real-time metric display

### Automated Reporting
- **Scheduled analysis** - Regular automated reports
- **Threshold monitoring** - Automatic alerts for unusual patterns
- **Trend detection** - Automated pattern recognition
- **Capacity planning** - Growth-based infrastructure recommendations

## Related Agents

- **[general-purpose](./general-purpose.md)** - For complex analysis requiring multiple capabilities
- **[post-commit-updater](./post-commit-updater.md)** - For updating monitoring after system changes
- **[web-research-agent](./web-research-agent.md)** - For researching monitoring best practices

---

**Agent Type**: `database-query-analyzer`  
**Availability**: ✅ Active  
**Tool Access**: Bash, Read, Write, Grep, WebFetch  
**Primary Use**: Database analysis, system monitoring, and business intelligence