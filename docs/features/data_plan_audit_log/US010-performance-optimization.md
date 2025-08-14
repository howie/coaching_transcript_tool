# US010: Performance Optimization

## 📋 User Story

**As a** platform operator and end user  
**I want** optimized system performance with data governance features  
**So that** the enhanced data management capabilities don't impact user experience or system scalability

## 💼 Business Value

### Current Problem
- Adding comprehensive data governance features may impact system performance
- Large-scale audit logging and analytics could slow down core transcription workflows
- Database growth from usage logs and audit trails needs optimization
- User experience should remain fast despite additional data processing

### Business Impact
- **User Experience**: Slow performance affects user satisfaction and retention
- **Operational Cost**: Inefficient queries and storage increase infrastructure costs
- **Scalability**: Poor performance limits platform growth and user capacity
- **Competitive Advantage**: Fast, reliable service is key differentiator

### Value Delivered
- **Optimized Performance**: Data governance features with minimal performance impact
- **Efficient Scaling**: System handles increased data volume without degradation
- **Cost Optimization**: Efficient queries and storage reduce operational expenses
- **User Satisfaction**: Fast, responsive experience maintains user engagement

## 🎯 Acceptance Criteria

### Database Performance
1. **Query Optimization**
   - [ ] All audit logging queries execute in <50ms
   - [ ] Usage analytics queries complete in <200ms
   - [ ] Dashboard API responses under 500ms
   - [ ] Export generation doesn't block other operations

2. **Index Strategy**
   - [ ] Optimal indexes for all audit log and analytics tables
   - [ ] Composite indexes for complex filtering scenarios
   - [ ] Partitioning for large time-series data
   - [ ] Regular index maintenance and optimization

3. **Database Schema Optimization**
   - [ ] Efficient data types and storage formats
   - [ ] Normalized schema with minimal redundancy
   - [ ] Appropriate constraints and relationships
   - [ ] Archive strategies for historical data

### Application Performance  
4. **Async Processing**
   - [ ] All heavy operations (exports, analytics) run in background
   - [ ] Non-blocking audit logging implementation
   - [ ] Async data retention policy execution
   - [ ] Queue-based processing for scalability

5. **Caching Strategy**
   - [ ] Dashboard metrics cached for 1-5 minutes
   - [ ] Frequently accessed data cached in Redis
   - [ ] API response caching where appropriate
   - [ ] Cache invalidation for real-time accuracy

### Resource Management
6. **Memory and CPU Optimization**
   - [ ] Efficient memory usage in analytics processing
   - [ ] CPU optimization for data aggregation tasks
   - [ ] Resource limits for background jobs
   - [ ] Monitoring and alerting for resource usage

## 🏗️ Technical Implementation

### Database Optimization
```sql
-- Optimized indexes for audit logs
CREATE INDEX CONCURRENTLY idx_audit_log_user_timestamp 
ON audit_log (user_id, timestamp DESC) 
WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_audit_log_entity_timestamp 
ON audit_log (entity_type, entity_id, timestamp DESC) 
WHERE entity_type IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_audit_log_critical_events
ON audit_log (timestamp DESC) 
WHERE severity IN ('high', 'critical');

-- Partitioned tables for time-series data
CREATE TABLE audit_log_y2025m08 PARTITION OF audit_log
FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');

CREATE TABLE audit_log_y2025m09 PARTITION OF audit_log
FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

-- Optimized indexes for usage logs
CREATE INDEX CONCURRENTLY idx_usage_log_user_created 
ON usage_log (user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_usage_log_billing_analysis
ON usage_log (created_at, is_billable, stt_provider)
WHERE is_billable = true;

-- Materialized view for dashboard metrics
CREATE MATERIALIZED VIEW dashboard_daily_metrics AS
SELECT 
    date_trunc('day', created_at) as day,
    count(*) as total_sessions,
    sum(duration_minutes) as total_minutes,
    sum(CASE WHEN is_billable THEN cost_usd ELSE 0 END) as revenue,
    count(DISTINCT user_id) as active_users,
    avg(duration_minutes) as avg_duration,
    count(*) FILTER (WHERE stt_provider = 'google') as google_sessions,
    count(*) FILTER (WHERE stt_provider = 'assemblyai') as assemblyai_sessions
FROM usage_log 
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY date_trunc('day', created_at)
ORDER BY day DESC;

CREATE UNIQUE INDEX ON dashboard_daily_metrics (day);

-- Refresh materialized view daily
SELECT cron.schedule('refresh-dashboard-metrics', '0 2 * * *', 'REFRESH MATERIALIZED VIEW dashboard_daily_metrics;');
```

### Performance Monitoring Service
```python
# packages/core-logic/src/coaching_assistant/services/performance_monitoring.py

import time
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Service for monitoring and optimizing performance"""
    
    def __init__(self, db: Session):
        self.db = db
        self.query_cache = {}
        self.performance_thresholds = {
            'query_slow_threshold_ms': 100,
            'api_slow_threshold_ms': 1000,
            'memory_threshold_percent': 85,
            'cpu_threshold_percent': 80
        }
    
    @contextmanager
    def monitor_query(self, query_name: str):
        """Context manager to monitor query performance"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self._log_query_performance(query_name, duration_ms)
    
    def _log_query_performance(self, query_name: str, duration_ms: float):
        """Log query performance metrics"""
        if duration_ms > self.performance_thresholds['query_slow_threshold_ms']:
            logger.warning(f"Slow query detected: {query_name} took {duration_ms:.2f}ms")
        
        # Store performance metrics (could be sent to monitoring system)
        self.query_cache[query_name] = {
            'last_duration_ms': duration_ms,
            'timestamp': datetime.utcnow()
        }
    
    def optimize_database_performance(self) -> Dict:
        """Run database optimization tasks"""
        optimization_results = {
            'vacuum_analyze': self._run_vacuum_analyze(),
            'index_usage': self._check_index_usage(),
            'slow_queries': self._identify_slow_queries(),
            'table_sizes': self._analyze_table_sizes()
        }
        
        return optimization_results
    
    def _run_vacuum_analyze(self) -> Dict:
        """Run VACUUM ANALYZE on key tables"""
        tables_to_optimize = [
            'audit_log',
            'usage_log', 
            'usage_analytics',
            'data_export',
            'billing_analytics'
        ]
        
        results = {}
        for table in tables_to_optimize:
            try:
                start_time = time.time()
                self.db.execute(text(f"VACUUM ANALYZE {table}"))
                duration = time.time() - start_time
                results[table] = {'status': 'success', 'duration_seconds': duration}
                logger.info(f"VACUUM ANALYZE completed for {table} in {duration:.2f}s")
            except Exception as e:
                results[table] = {'status': 'error', 'error': str(e)}
                logger.error(f"VACUUM ANALYZE failed for {table}: {e}")
        
        return results
    
    def _check_index_usage(self) -> List[Dict]:
        """Check index usage statistics"""
        query = text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
            LIMIT 20
        """)
        
        result = self.db.execute(query)
        return [
            {
                'table': row.tablename,
                'index': row.indexname,
                'scans': row.index_scans,
                'tuples_read': row.tuples_read,
                'efficiency': row.tuples_fetched / max(row.tuples_read, 1)
            }
            for row in result
        ]
    
    def _identify_slow_queries(self) -> List[Dict]:
        """Identify slow queries from pg_stat_statements"""
        # Requires pg_stat_statements extension
        query = text("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                max_time,
                rows / calls as avg_rows
            FROM pg_stat_statements 
            WHERE mean_time > :threshold
            ORDER BY mean_time DESC 
            LIMIT 10
        """)
        
        try:
            result = self.db.execute(query, {'threshold': self.performance_thresholds['query_slow_threshold_ms']})
            return [
                {
                    'query': row.query[:200] + '...' if len(row.query) > 200 else row.query,
                    'calls': row.calls,
                    'avg_time_ms': row.mean_time,
                    'max_time_ms': row.max_time,
                    'avg_rows': row.avg_rows
                }
                for row in result
            ]
        except Exception as e:
            logger.warning(f"Could not retrieve slow queries (pg_stat_statements not available?): {e}")
            return []
    
    def _analyze_table_sizes(self) -> List[Dict]:
        """Analyze table sizes and growth"""
        query = text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 15
        """)
        
        result = self.db.execute(query)
        return [
            {
                'table': row.tablename,
                'size_pretty': row.size,
                'size_bytes': row.size_bytes
            }
            for row in result
        ]
    
    def get_system_performance_metrics(self) -> Dict:
        """Get current system performance metrics"""
        
        # CPU and Memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database connection stats
        db_stats = self._get_database_stats()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            },
            'database': db_stats,
            'alerts': self._generate_performance_alerts(cpu_percent, memory.percent, db_stats)
        }
    
    def _get_database_stats(self) -> Dict:
        """Get database connection and performance stats"""
        try:
            # Connection stats
            conn_query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            conn_result = self.db.execute(conn_query).first()
            
            # Transaction stats
            tx_query = text("""
                SELECT 
                    xact_commit,
                    xact_rollback,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            
            tx_result = self.db.execute(tx_query).first()
            
            return {
                'connections': {
                    'total': conn_result.total_connections,
                    'active': conn_result.active_connections,
                    'idle': conn_result.idle_connections
                },
                'transactions': {
                    'commits': tx_result.xact_commit,
                    'rollbacks': tx_result.xact_rollback,
                    'rollback_ratio': tx_result.xact_rollback / max(tx_result.xact_commit + tx_result.xact_rollback, 1)
                },
                'tuples': {
                    'returned': tx_result.tup_returned,
                    'fetched': tx_result.tup_fetched,
                    'inserted': tx_result.tup_inserted,
                    'updated': tx_result.tup_updated,
                    'deleted': tx_result.tup_deleted
                }
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def _generate_performance_alerts(self, cpu_percent: float, memory_percent: float, db_stats: Dict) -> List[str]:
        """Generate performance alerts based on thresholds"""
        alerts = []
        
        if cpu_percent > self.performance_thresholds['cpu_threshold_percent']:
            alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        if memory_percent > self.performance_thresholds['memory_threshold_percent']:
            alerts.append(f"High memory usage: {memory_percent:.1f}%")
        
        if db_stats and db_stats.get('connections', {}).get('active', 0) > 50:
            alerts.append(f"High database connections: {db_stats['connections']['active']}")
        
        if db_stats and db_stats.get('transactions', {}).get('rollback_ratio', 0) > 0.1:
            alerts.append(f"High transaction rollback ratio: {db_stats['transactions']['rollback_ratio']:.2%}")
        
        return alerts

# Performance monitoring decorator
def monitor_performance(operation_name: str):
    """Decorator to monitor operation performance"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > 1000:  # Log operations taking >1s
                    logger.info(f"Performance: {operation_name} completed in {duration_ms:.2f}ms")
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Performance: {operation_name} failed after {duration_ms:.2f}ms: {e}")
                raise
        return wrapper
    return decorator
```

### Optimized Analytics Service
```python
# packages/core-logic/src/coaching_assistant/services/optimized_analytics_service.py

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import json
import logging

logger = logging.getLogger(__name__)

class OptimizedAnalyticsService:
    """Performance-optimized analytics service with caching"""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client
        self.cache_ttl = {
            'realtime_kpis': 60,      # 1 minute
            'daily_metrics': 300,     # 5 minutes
            'monthly_analytics': 1800  # 30 minutes
        }
    
    def get_cached_or_compute(self, cache_key: str, compute_func: callable, ttl: int = 300) -> Dict:
        """Get from cache or compute and cache result"""
        if not self.redis:
            return compute_func()
        
        try:
            cached_result = self.redis.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
        except Exception as e:
            logger.warning(f"Cache read error for {cache_key}: {e}")
        
        # Compute fresh result
        result = compute_func()
        
        # Cache the result
        try:
            self.redis.setex(cache_key, ttl, json.dumps(result, default=str))
        except Exception as e:
            logger.warning(f"Cache write error for {cache_key}: {e}")
        
        return result
    
    def get_realtime_kpis_optimized(self) -> Dict:
        """Get real-time KPIs with caching and optimized queries"""
        
        def compute_kpis():
            # Use materialized view for better performance
            query = text("""
                WITH recent_stats AS (
                    SELECT 
                        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as recent_sessions,
                        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as daily_sessions,
                        COUNT(DISTINCT user_id) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as daily_active_users,
                        SUM(cost_usd) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours' AND is_billable = true) as daily_revenue,
                        AVG(duration_minutes) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as avg_duration
                    FROM usage_log
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                ),
                session_stats AS (
                    SELECT 
                        COUNT(*) FILTER (WHERE status = 'processing') as active_transcriptions,
                        COUNT(*) FILTER (WHERE status = 'failed' AND updated_at >= NOW() - INTERVAL '1 hour') as failed_recent
                    FROM session
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                )
                SELECT 
                    rs.*,
                    ss.active_transcriptions,
                    ss.failed_recent,
                    CASE 
                        WHEN rs.recent_sessions > 0 
                        THEN (ss.failed_recent::float / rs.recent_sessions * 100) 
                        ELSE 0 
                    END as error_rate_percent
                FROM recent_stats rs, session_stats ss
            """)
            
            result = self.db.execute(query).first()
            
            return {
                'real_time': {
                    'active_transcriptions': result.active_transcriptions or 0,
                    'transcriptions_last_hour': result.recent_sessions or 0,
                    'active_users_24h': result.daily_active_users or 0,
                    'error_rate_percent': float(result.error_rate_percent or 0),
                    'daily_revenue_usd': float(result.daily_revenue or 0),
                    'avg_duration_minutes': float(result.avg_duration or 0)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        
        cache_key = "analytics:realtime_kpis"
        return self.get_cached_or_compute(cache_key, compute_kpis, self.cache_ttl['realtime_kpis'])
    
    def get_usage_trends_optimized(self, start_date: datetime, end_date: datetime, granularity: str = "daily") -> Dict:
        """Get usage trends using optimized queries and materialized views"""
        
        cache_key = f"analytics:trends:{granularity}:{start_date.date()}:{end_date.date()}"
        
        def compute_trends():
            if granularity == "daily" and (end_date - start_date).days <= 90:
                # Use materialized view for recent daily data
                query = text("""
                    SELECT 
                        day,
                        total_sessions,
                        total_minutes,
                        revenue,
                        active_users,
                        avg_duration,
                        google_sessions,
                        assemblyai_sessions
                    FROM dashboard_daily_metrics 
                    WHERE day BETWEEN :start_date AND :end_date
                    ORDER BY day DESC
                """)
                
                result = self.db.execute(query, {
                    'start_date': start_date.date(),
                    'end_date': end_date.date()
                })
                
                return {
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'granularity': granularity
                    },
                    'transcription_trend': [
                        {
                            'period': row.day.isoformat(),
                            'session_count': row.total_sessions,
                            'total_minutes': row.total_minutes,
                            'total_cost': float(row.revenue)
                        }
                        for row in result
                    ],
                    'provider_breakdown': [
                        {
                            'provider': 'google',
                            'session_count': sum(row.google_sessions for row in result),
                            'percentage': (sum(row.google_sessions for row in result) / max(sum(row.total_sessions for row in result), 1)) * 100
                        },
                        {
                            'provider': 'assemblyai', 
                            'session_count': sum(row.assemblyai_sessions for row in result),
                            'percentage': (sum(row.assemblyai_sessions for row in result) / max(sum(row.total_sessions for row in result), 1)) * 100
                        }
                    ]
                }
            else:
                # Fall back to original implementation for other cases
                return self._compute_trends_fallback(start_date, end_date, granularity)
        
        return self.get_cached_or_compute(cache_key, compute_trends, self.cache_ttl['daily_metrics'])
    
    def _compute_trends_fallback(self, start_date: datetime, end_date: datetime, granularity: str) -> Dict:
        """Fallback method for trends computation"""
        # Implementation similar to original but with query optimizations
        pass
    
    def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if not self.redis:
            return
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
    
    def warm_cache(self):
        """Pre-warm frequently accessed cache entries"""
        logger.info("Starting cache warm-up process")
        
        try:
            # Warm up real-time KPIs
            self.get_realtime_kpis_optimized()
            
            # Warm up recent trends
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            self.get_usage_trends_optimized(start_date, end_date, "daily")
            
            logger.info("Cache warm-up completed successfully")
        except Exception as e:
            logger.error(f"Cache warm-up failed: {e}")
```

### Background Task Optimization
```python
# packages/core-logic/src/coaching_assistant/tasks/optimized_tasks.py

from celery import Task
from ..core.celery_app import celery_app
from ..services.performance_monitoring import monitor_performance
import logging

logger = logging.getLogger(__name__)

class OptimizedTask(Task):
    """Base task class with performance monitoring"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Log successful task completion"""
        logger.info(f"Task {self.name} completed successfully: {task_id}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure with performance context"""
        logger.error(f"Task {self.name} failed: {task_id} - {exc}")

@celery_app.task(bind=True, base=OptimizedTask)
@monitor_performance("database_optimization")
def optimize_database_performance(self):
    """Periodic database optimization task"""
    from ..core.database import get_db_session
    from ..services.performance_monitoring import PerformanceMonitor
    
    with get_db_session() as db:
        monitor = PerformanceMonitor(db)
        results = monitor.optimize_database_performance()
        
        logger.info(f"Database optimization completed: {results}")
        return results

@celery_app.task(bind=True, base=OptimizedTask)
@monitor_performance("cache_warmup")
def warm_analytics_cache(self):
    """Warm up analytics cache"""
    from ..core.database import get_db_session
    from ..services.optimized_analytics_service import OptimizedAnalyticsService
    import redis
    
    with get_db_session() as db:
        redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        analytics_service = OptimizedAnalyticsService(db, redis_client)
        analytics_service.warm_cache()
        
        return {"status": "cache_warmed"}

@celery_app.task(bind=True, base=OptimizedTask)
@monitor_performance("materialized_view_refresh")
def refresh_materialized_views(self):
    """Refresh materialized views for analytics"""
    from ..core.database import get_db_session
    from sqlalchemy import text
    
    with get_db_session() as db:
        try:
            # Refresh dashboard metrics
            db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_daily_metrics"))
            db.commit()
            
            logger.info("Materialized views refreshed successfully")
            return {"status": "views_refreshed"}
        except Exception as e:
            logger.error(f"Failed to refresh materialized views: {e}")
            raise

# Schedule optimizations
from celery.schedules import crontab

celery_app.conf.beat_schedule.update({
    'optimize-database': {
        'task': 'coaching_assistant.tasks.optimized_tasks.optimize_database_performance',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        'options': {'queue': 'maintenance'}
    },
    'warm-cache': {
        'task': 'coaching_assistant.tasks.optimized_tasks.warm_analytics_cache', 
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'options': {'queue': 'cache'}
    },
    'refresh-views': {
        'task': 'coaching_assistant.tasks.optimized_tasks.refresh_materialized_views',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {'queue': 'maintenance'}
    }
})
```

## 🧪 Test Scenarios

### Performance Tests
```python
def test_dashboard_kpi_performance():
    """Test dashboard KPI query performance"""
    # Create test data
    for i in range(1000):
        create_usage_log(db, cost_usd=0.01, duration_minutes=5)
    
    # Measure KPI query performance
    start_time = time.time()
    
    analytics_service = OptimizedAnalyticsService(db)
    kpis = analytics_service.get_realtime_kpis_optimized()
    
    duration_ms = (time.time() - start_time) * 1000
    
    assert duration_ms < 500  # Should complete in <500ms
    assert kpis['real_time']['daily_revenue_usd'] >= 10

def test_audit_logging_performance():
    """Test that audit logging doesn't impact main operations"""
    # Enable audit logging
    from ..services.audit_service import get_audit_service, AuditEventType
    
    # Measure session creation with audit logging
    start_time = time.time()
    
    for i in range(100):
        session = create_test_session(db, user_id)
        audit_service = get_audit_service(db)
        audit_service.log_data_change(
            event_type=AuditEventType.SESSION_CREATE,
            entity_type="session",
            entity_id=session.id,
            operation="create",
            description=f"Session {session.title} created"
        )
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Should not significantly impact performance
    assert duration_ms < 2000  # 100 operations in <2 seconds
```

### Load Tests
```bash
# Load test dashboard endpoint
ab -n 1000 -c 10 -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/dashboard/kpis

# Expected: <500ms average response time, 0% failures

# Load test usage analytics endpoint  
ab -n 500 -c 5 -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/dashboard/usage-trends?start_date=2025-08-01&end_date=2025-08-14"

# Expected: <1s average response time, 0% failures
```

## 📊 Success Metrics

### Performance Targets
- **Dashboard Load Time**: <2 seconds for admin dashboard
- **API Response Times**: <500ms for analytics endpoints
- **Database Query Performance**: <100ms for optimized queries
- **Memory Usage**: <70% of available system memory
- **CPU Usage**: <60% average CPU utilization

### Scalability Metrics
- **Concurrent Users**: Support 1000+ concurrent dashboard users
- **Data Volume**: Handle 1M+ audit log entries without degradation
- **Export Performance**: Generate 100MB exports in <5 minutes
- **Cache Hit Rate**: >90% cache hit rate for dashboard metrics

## 📋 Definition of Done

- [ ] **Database Optimization**: Proper indexing and query optimization
- [ ] **Caching Layer**: Redis caching for frequently accessed data
- [ ] **Performance Monitoring**: Comprehensive performance tracking service
- [ ] **Materialized Views**: Optimized views for complex analytics queries
- [ ] **Background Processing**: Non-blocking async processing for heavy operations
- [ ] **Resource Monitoring**: System resource monitoring and alerting
- [ ] **Load Testing**: Performance validated under realistic load
- [ ] **Optimization Tasks**: Automated database maintenance and optimization
- [ ] **Performance Tests**: Comprehensive performance test suite
- [ ] **Documentation**: Performance optimization guide and monitoring procedures

## 🔄 Dependencies & Risks

### Dependencies
- ✅ Redis for caching infrastructure
- ✅ Celery for background task processing
- ✅ PostgreSQL with proper extensions (pg_stat_statements)
- ⏳ Load testing tools and monitoring infrastructure

### Risks & Mitigations
- **Risk**: Optimization complexity introduces bugs
  - **Mitigation**: Comprehensive testing, gradual rollout, rollback procedures
- **Risk**: Caching introduces data consistency issues
  - **Mitigation**: Appropriate cache TTL, cache invalidation strategies
- **Risk**: Background processing overloads system resources
  - **Mitigation**: Queue management, resource limits, monitoring

## 📞 Stakeholders

**Product Owner**: Platform Engineering Team  
**Technical Lead**: Backend Engineering, DevOps, Database Administration  
**Reviewers**: Site Reliability Engineering, Performance Team  
**QA Focus**: Performance testing, Load testing, Scalability verification