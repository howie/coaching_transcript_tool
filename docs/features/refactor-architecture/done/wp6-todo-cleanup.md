# WP6 TODO Cleanup Analysis

**Status**: 📋 **DOCUMENTED**
**Date**: 2025-09-17
**Priority**: P2 - Maintenance (Technical Debt Management)

## Overview

Comprehensive analysis of TODO comments, technical debt, and pending tasks throughout the codebase. This document categorizes and prioritizes cleanup items to maintain code quality during the Clean Architecture migration.

## Executive Summary

**Total Items Found**: 67 TODO/FIXME comments + 45+ technical debt items
- **🔥 Critical**: 8 items (immediate action needed)
- **⚠️ High**: 15 items (address in next sprint)
- **📋 Medium**: 32 items (address within 2-3 sprints)
- **📌 Low**: 17 items (backlog/documentation cleanup)

## Critical Priority (🔥 P0 - Immediate Action)

### Infrastructure & Architecture

**1. Speaker Role Implementation** - `src/coaching_assistant/infrastructure/db/repositories/transcript_repository.py:55`
```python
# TODO: Implement speaker role updates via SegmentRoleModel table
```
- **Impact**: Speaker role assignment functionality incomplete
- **Action**: Implement proper SegmentRole repository and relationship handling
- **Effort**: 4-6 hours

**2. Factory Pattern Migration** - `src/coaching_assistant/infrastructure/factories.py:442`
```python
# TODO: Remove after all API endpoints migrate to factory pattern (WP2-WP4)
```
- **Impact**: Legacy dependencies blocking Clean Architecture completion
- **Action**: Complete API endpoint migration, remove legacy factory functions
- **Effort**: 2-3 days

**3. Session Repository Legacy Fix** - `src/coaching_assistant/infrastructure/db/repositories/session_repository.py:17`
```python
# TEMPORARY FIX: Use legacy model until database migration is complete
```
- **Impact**: Session repository not using proper infrastructure models
- **Action**: Complete SessionModel migration to infrastructure layer
- **Effort**: 1-2 days

### Core Business Logic

**4. Speaker Role Management** - `src/coaching_assistant/core/services/speaker_role_management_use_case.py:90,173`
```python
# TODO: Implement SpeakerRoleRepoPort and update this logic
# TODO: Implement SegmentRoleRepoPort and update this logic
```
- **Impact**: Core use case incomplete, blocking speaker role features
- **Action**: Complete repository port implementation
- **Effort**: 1 day

## High Priority (⚠️ P1 - Next Sprint)

### Payment & Billing System

**5. ECPay Integration** - Multiple locations in `src/coaching_assistant/core/services/ecpay_service.py`
```python
# TODO: Call ECPay API to cancel authorization (line 761)
# TODO: Implement ECPay manual retry API call (line 881)
# TODO: In production, call ECPay API to cancel authorization (line 1109)
```
- **Impact**: Payment cancellation and retry functionality not implemented
- **Action**: Complete ECPay API integration
- **Effort**: 3-4 days

**6. Notification System** - Multiple services
```python
# TODO: Queue email notification (ecpay_service.py:672)
# TODO: Integrate with existing email service (subscription_maintenance_tasks.py:207)
# TODO: Implement actual notification sending (ecpay_service.py:1198)
```
- **Impact**: Payment notifications not being sent to users
- **Action**: Implement email notification service integration
- **Effort**: 2-3 days

### Analytics & Reporting

**7. Usage Analytics** - `src/coaching_assistant/services/usage_analytics_service.py`
```python
# TODO: Track exports separately (line 467)
# TODO: Calculate storage usage (line 468)
# TODO: Track API calls (line 472)
# TODO: Track concurrent sessions (line 473)
```
- **Impact**: Incomplete usage tracking for billing and analytics
- **Action**: Implement comprehensive usage tracking
- **Effort**: 2-3 days

**8. Billing Analytics** - `src/coaching_assistant/services/billing_analytics_service.py`
```python
# TODO: Calculate actual new signups (line 836)
# TODO: Calculate actual churned users (line 837)
# TODO: Calculate from actual billing (line 859)
```
- **Impact**: Revenue analytics showing placeholder data
- **Action**: Implement real billing calculations
- **Effort**: 1-2 days

## Medium Priority (📋 P2 - Within 2-3 Sprints)

### API Endpoints

**9. Export Functionality** - `src/coaching_assistant/api/v1/usage_history.py`
```python
# TODO: Implement CSV export (line 439)
# TODO: Implement PDF export (line 447)
```
- **Impact**: Limited export options for users
- **Action**: Add CSV/PDF export capabilities
- **Effort**: 1-2 days

**10. Bulk Operations** - `src/coaching_assistant/api/v1/plan_limits.py:364`
```python
# TODO: Implement a dedicated UseCase for bulk usage reset operations
```
- **Impact**: Admin operations not optimized
- **Action**: Create bulk operation use cases
- **Effort**: 1 day

### Frontend Components

**11. Payment Settings** - `apps/web/app/dashboard/billing/payment-settings/page.tsx:38`
```python
// TODO: Implement save settings
```
- **Impact**: Payment settings cannot be saved
- **Action**: Complete payment settings implementation
- **Effort**: 0.5-1 day

**12. Profile Management** - `apps/web/app/dashboard/profile/page.tsx:203`
```python
// TODO: Implement actual photo upload to storage service
```
- **Impact**: Profile photo upload not functional
- **Action**: Integrate with cloud storage service
- **Effort**: 1 day

**13. Session Content** - `apps/web/app/dashboard/sessions/[id]/page.tsx:610`
```python
// TODO: Add API call to save content changes
```
- **Impact**: Session content changes not persisted
- **Action**: Implement content save API
- **Effort**: 0.5 day

## Low Priority (📌 P3 - Backlog)

### Configuration & Infrastructure

**14. Legacy Plan Enum** - Multiple locations
```python
ENTERPRISE = "enterprise"  # Deprecated, kept for backward compatibility
```
- **Impact**: Deprecated enum values in codebase
- **Action**: Remove after confirming no dependencies
- **Effort**: 2-3 hours

**15. Terraform Templates** - `terraform/scripts/env-to-tfvars.py`
```python
# TODO: 填入實際值
```
- **Impact**: Template placeholders need real values
- **Action**: Update deployment configuration
- **Effort**: 1-2 hours

### STT Processing

**16. Google STT Enhancement** - `src/coaching_assistant/services/google_stt.py:1178`
```python
# TODO: Implement post-processing speaker diarization if needed
```
- **Impact**: Speaker diarization could be improved
- **Action**: Research and implement post-processing
- **Effort**: 1-2 days

**17. STT Factory** - `src/coaching_assistant/services/stt_factory.py:47`
```python
# TODO: Implement WhisperSTTProvider when needed
```
- **Impact**: Limited STT provider options
- **Action**: Add Whisper support
- **Effort**: 3-4 days

## Technical Debt Analysis

### Legacy Code Patterns

**High Impact Legacy Items**:

1. **Legacy Model Usage** (Critical)
   - Session repository using temporary legacy model conversion
   - User repository handling both string and enum values
   - Usage log model maintaining legacy field compatibility

2. **Factory Pattern Migration** (High)
   - Legacy factory functions still in use
   - API endpoints not fully migrated to Clean Architecture
   - Circular dependency warnings in tests

3. **Authentication System** (Medium)
   - CryptContext using deprecated="auto" setting
   - Legacy token handling in frontend API client

### Architecture Migration Status

**Clean Architecture Progress**:
- ✅ **Core Domain**: 85% complete (use cases implemented)
- ⚠️ **Infrastructure**: 70% complete (some legacy model usage)
- ⚠️ **API Layer**: 75% complete (some endpoints not migrated)
- ❌ **Legacy Cleanup**: 40% complete (many TODO items remain)

## Cleanup Strategy

### Phase 1: Critical Infrastructure (Week 1)
1. Complete speaker role repository implementation
2. Finish session repository migration
3. Remove factory pattern TODOs
4. Implement speaker role use cases

### Phase 2: Payment & Billing (Week 2-3)
1. Complete ECPay API integration
2. Implement notification system
3. Fix billing analytics calculations
4. Add usage tracking features

### Phase 3: User Experience (Week 4)
1. Complete frontend TODOs (save settings, photo upload)
2. Add export functionality (CSV/PDF)
3. Implement session content persistence
4. Add bulk admin operations

### Phase 4: Technical Debt (Ongoing)
1. Remove deprecated enums and legacy code
2. Update Terraform configurations
3. Enhance STT providers
4. Documentation cleanup

## Recommendations

### Immediate Actions (This Sprint)
1. **Create GitHub Issues**: Convert critical TODOs to tracked issues
2. **Assign Ownership**: Assign specific TODOs to team members
3. **Add TODO Linting**: Prevent new TODO comments without issues
4. **Speaker Role Priority**: Focus on completing speaker role functionality

### Process Improvements
1. **TODO Policy**: All TODO comments must reference GitHub issues
2. **Legacy Markers**: Use consistent markers for legacy code
3. **Migration Tracking**: Track Clean Architecture migration progress
4. **Regular Cleanup**: Schedule monthly technical debt reviews

### Monitoring
1. **TODO Count**: Track reduction in TODO comments over time
2. **Legacy Dependencies**: Monitor and reduce legacy code usage
3. **Architecture Compliance**: Automated checks for Clean Architecture violations
4. **Test Coverage**: Ensure cleanup doesn't reduce test coverage

## Files Requiring Immediate Attention

### Critical Files
- `src/coaching_assistant/infrastructure/db/repositories/transcript_repository.py`
- `src/coaching_assistant/infrastructure/db/repositories/session_repository.py`
- `src/coaching_assistant/core/services/speaker_role_management_use_case.py`
- `src/coaching_assistant/infrastructure/factories.py`

### High Priority Files
- `src/coaching_assistant/core/services/ecpay_service.py`
- `src/coaching_assistant/services/usage_analytics_service.py`
- `src/coaching_assistant/services/billing_analytics_service.py`
- `src/coaching_assistant/tasks/subscription_maintenance_tasks.py`

### Documentation Cleanup
- Remove completed TODO items from documentation
- Update status in feature README files
- Clean up placeholder values in configuration docs

## Success Metrics

### Quantitative Targets
- **TODO Reduction**: Reduce TODO count by 50% within 4 weeks
- **Legacy Code**: Remove 80% of legacy model usage within 6 weeks
- **Architecture Compliance**: Achieve 90% Clean Architecture compliance
- **Test Coverage**: Maintain >85% coverage during cleanup

### Qualitative Goals
- **Code Maintainability**: Easier onboarding for new developers
- **System Reliability**: Fewer bugs from incomplete implementations
- **Feature Velocity**: Faster feature development with clean architecture
- **Technical Confidence**: Team confidence in system architecture

---

**Next Actions**: Create GitHub issues for critical TODOs and begin speaker role implementation to resolve the most impactful technical debt items.