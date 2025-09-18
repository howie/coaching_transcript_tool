# WP6-Cleanup-4: Analytics & Export Features - User Value Implementation

**Status**: ⚠️ **High Priority** (Not Started)
**Work Package**: WP6-Cleanup-4 - Analytics & Export Features Implementation
**Epic**: Clean Architecture Cleanup Phase

## Overview

Implement missing analytics tracking and export features that users have been requesting. This includes usage analytics, billing analytics, and CSV/PDF export functionality.

## User Value Statement

**As a business user**, I want **detailed usage analytics and export capabilities** so that **I can track my coaching session usage, analyze billing patterns, and generate reports for my practice**.

## Business Impact

- **User Satisfaction**: Deliver requested analytics and export features
- **Data Insights**: Enable users to understand their usage patterns
- **Professional Use**: Support coaches who need data for their business

## Critical TODOs Being Resolved

### 🔥 Analytics Tracking Missing (10 items)
- `src/coaching_assistant/services/usage_analytics_service.py:467-473`
  ```python
  "exports_generated": 0,  # TODO: Track exports separately
  "storage_used_mb": 0,  # TODO: Calculate storage usage
  "api_calls_made": 0,  # TODO: Track API calls
  "concurrent_sessions_peak": 1,  # TODO: Track concurrent sessions
  "exports_by_format": {},  # TODO: Track export formats
  "failed_transcriptions": 0,  # TODO: Track failed transcriptions
  ```

- `src/coaching_assistant/services/billing_analytics_service.py:836-875`
  ```python
  "new_signups": 0,  # TODO: Calculate actual new signups
  "churned_users": 0,  # TODO: Calculate actual churned users
  "total_revenue": 0,  # TODO: Calculate from actual billing
  "timezone": None,  # TODO: Get from user preferences
  "country": None,  # TODO: Get from user profile
  ```

### 🔥 Export Features Missing (2 items)
- `src/coaching_assistant/api/v1/usage_history.py:439`
  ```python
  # TODO: Implement CSV export
  ```
- `src/coaching_assistant/api/v1/usage_history.py:447`
  ```python
  # TODO: Implement PDF export
  ```

### 🔥 Bulk Operations Missing (1 item)
- `src/coaching_assistant/api/v1/plan_limits.py:364`
  ```python
  # TODO: Implement a dedicated UseCase for bulk usage reset operations
  ```

## Architecture Compliance Issues Fixed

### Current Violations
- **Service Layer Incomplete**: Analytics services missing core functionality
- **API Layer Incomplete**: Export endpoints stubbed with TODOs
- **Use Case Missing**: Bulk operations not implemented properly

### Clean Architecture Solutions
- **Complete Analytics Implementation**: Real tracking and calculation logic
- **Export Use Cases**: Proper business logic for data export
- **Bulk Operations Use Case**: Clean separation of bulk operation concerns

## Implementation Tasks

### 1. Complete Usage Analytics Implementation
- **File**: `src/coaching_assistant/services/usage_analytics_service.py`
- **Requirements**:
  - Implement storage calculation from session data
  - Track exports by format type
  - Calculate API call metrics
  - Track concurrent session peaks
  - Monitor failed transcription rates
  - Real-time usage statistics

### 2. Complete Billing Analytics Implementation
- **File**: `src/coaching_assistant/services/billing_analytics_service.py`
- **Requirements**:
  - Calculate actual new signups from user data
  - Calculate churn rate from subscription cancellations
  - Calculate total revenue from payment records
  - Integrate user timezone preferences
  - Add user profile country data

### 3. Implement Export Use Cases
- **File**: `src/coaching_assistant/core/services/export_use_case.py` (new)
- **Requirements**:
  - CSV export use case for usage history
  - PDF export use case for professional reports
  - Data formatting and validation
  - Export permission checking

### 4. Export Infrastructure Implementation
- **Files**:
  - `src/coaching_assistant/infrastructure/export/csv_exporter.py` (new)
  - `src/coaching_assistant/infrastructure/export/pdf_exporter.py` (new)
- **Requirements**:
  - CSV generation with proper formatting
  - PDF generation with professional layout
  - File handling and cleanup
  - Performance optimization for large datasets

### 5. Complete Export API Endpoints
- **File**: `src/coaching_assistant/api/v1/usage_history.py`
- **Requirements**:
  - Remove TODO comments
  - Implement CSV export endpoint
  - Implement PDF export endpoint
  - Proper error handling and file delivery

### 6. Bulk Operations Use Case
- **File**: `src/coaching_assistant/core/services/bulk_operations_use_case.py` (new)
- **Requirements**:
  - Bulk usage reset operations
  - Admin bulk user management
  - Performance optimized batch processing
  - Proper error handling for partial failures

### 7. Frontend Analytics Integration
- **File**: `apps/web/components/billing/UsageHistory.tsx`
- **Requirements**:
  - Replace API call TODOs with actual implementations
  - Add export buttons for CSV/PDF
  - Display analytics charts and metrics
  - Real-time usage updates

## E2E Demonstration Workflow

### Demo Script: "Usage Analytics and Export Workflow"

**Pre-requisites**: User with session history and usage data

1. **View Usage Analytics Dashboard** - GET `/api/v1/usage/analytics`
   ```json
   {
     "exports_generated": 15,
     "storage_used_mb": 245.7,
     "api_calls_made": 1247,
     "concurrent_sessions_peak": 3,
     "exports_by_format": {
       "csv": 8,
       "pdf": 7
     },
     "failed_transcriptions": 2
   }
   ```
   - Verify real analytics data displayed
   - Expected: Actual calculated values, not zeros

2. **Export Usage History to CSV** - GET `/api/v1/usage-history/export?format=csv`
   - Verify CSV file generated with proper formatting
   - Expected: Download starts with well-formatted CSV

3. **Export Usage History to PDF** - GET `/api/v1/usage-history/export?format=pdf`
   - Verify PDF file generated with professional layout
   - Expected: Download starts with formatted PDF report

4. **View Billing Analytics** - GET `/api/v1/billing-analytics/summary`
   ```json
   {
     "new_signups": 12,
     "churned_users": 2,
     "total_revenue": 1250.00,
     "user_profile": {
       "timezone": "Asia/Taipei",
       "country": "Taiwan"
     }
   }
   ```
   - Verify real billing calculations
   - Expected: Actual calculated revenue and user metrics

5. **Frontend Analytics Display** - Visit `/dashboard/usage`
   - Verify usage charts display real data
   - Verify export buttons work correctly
   - Expected: Rich analytics dashboard with export functionality

6. **Admin Bulk Operations** - POST `/api/v1/admin/bulk/reset-usage`
   ```json
   {
     "user_ids": ["uuid1", "uuid2", "uuid3"],
     "reset_type": "monthly"
   }
   ```
   - Verify bulk operations work efficiently
   - Expected: Multiple users processed correctly

## Success Metrics

### Functional Validation
- ✅ All analytics TODOs removed and implemented with real calculations
- ✅ CSV export generates properly formatted files
- ✅ PDF export creates professional reports
- ✅ Bulk operations handle large datasets efficiently
- ✅ Frontend displays real-time analytics data

### User Experience Validation
- ✅ Export files download correctly in all major browsers
- ✅ Analytics dashboard loads quickly with real data
- ✅ PDF reports have professional formatting
- ✅ CSV files open correctly in Excel/Google Sheets

### Performance Validation
- ✅ Analytics calculations complete within 2 seconds
- ✅ Export generation works for datasets up to 10,000 records
- ✅ Bulk operations handle 1000+ users efficiently
- ✅ Frontend dashboard responsive under load

## Testing Strategy

### Unit Tests (Required)
```bash
# Test analytics calculations
pytest tests/unit/services/test_usage_analytics_service.py -v
pytest tests/unit/services/test_billing_analytics_service.py -v

# Test export use cases
pytest tests/unit/core/services/test_export_use_case.py -v
```

### Integration Tests (Required)
```bash
# Test export infrastructure
pytest tests/integration/infrastructure/test_csv_exporter.py -v
pytest tests/integration/infrastructure/test_pdf_exporter.py -v

# Test API endpoints
pytest tests/integration/api/test_export_endpoints.py -v
```

### E2E Tests (Required)
```bash
# Complete analytics and export workflow
pytest tests/e2e/test_analytics_export_workflow.py -v
```

### Performance Tests (Required)
```bash
# Large dataset export performance
pytest tests/performance/test_export_performance.py -v

# Analytics calculation performance
pytest tests/performance/test_analytics_performance.py -v
```

### Manual Verification (Required)
- Download and verify CSV file formatting
- Download and verify PDF report layout
- Test export functionality in different browsers
- Verify analytics dashboard displays correctly

## Dependencies

### Blocked By
- **WP6-Cleanup-3**: Factory pattern needed for proper use case injection

### Blocking
- None (this is a leaf work package)

### External Dependencies
- **PDF Generation Library**: Need to choose and configure PDF library
- **Frontend Chart Library**: May need chart.js or similar for analytics dashboard

## Definition of Done

- [ ] All 13 analytics and export TODOs removed and implemented
- [ ] Real analytics calculations working with actual data
- [ ] CSV export generates properly formatted files
- [ ] PDF export creates professional reports with charts
- [ ] Bulk operations use case implemented efficiently
- [ ] Frontend analytics dashboard displays real data
- [ ] Export buttons work correctly in frontend
- [ ] Performance tests pass for large datasets
- [ ] All browsers support export downloads
- [ ] Code review completed and approved
- [ ] User documentation updated with export features

## Risk Assessment

### Technical Risks
- **Medium**: PDF generation library integration complexity
- **Medium**: Large dataset export performance
- **Low**: File download browser compatibility

### Business Risks
- **Medium**: User expectations for export formatting
- **Low**: Performance impact on server resources

### Mitigation Strategies
- **PDF Library**: Start with simple library, upgrade if needed
- **Performance**: Implement streaming export for large datasets
- **User Testing**: Get early feedback on export formatting

## Implementation Approach

### Phase 1: Analytics Implementation (Day 1-2)
- Complete usage analytics calculations
- Complete billing analytics calculations
- Test with real data for accuracy

### Phase 2: Export Infrastructure (Day 2-3)
- Implement CSV exporter
- Implement PDF exporter
- Test with various data sizes

### Phase 3: API and Frontend Integration (Day 3-4)
- Complete export API endpoints
- Update frontend components
- End-to-end testing

### Phase 4: Bulk Operations (Day 4)
- Implement bulk operations use case
- Performance testing and optimization

## Delivery Timeline

- **Estimated Effort**: 4 days (1 developer)
- **Critical Path**: Analytics → Export Infrastructure → API Integration → Frontend
- **Deliverable**: Complete analytics and export functionality with professional-quality outputs

---

## Related Work Packages

- **WP6-Cleanup-1**: Independent (can run in parallel)
- **WP6-Cleanup-2**: Independent (can run in parallel)
- **WP6-Cleanup-3**: Dependency (factory pattern needed)

This work package delivers high-value user-requested features and completes the missing functionality that impacts user satisfaction and professional use cases.