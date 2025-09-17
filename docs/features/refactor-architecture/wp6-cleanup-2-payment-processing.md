# WP6-Cleanup-2: Payment Processing Vertical - ECPay Integration Complete

**Status**: 🔥 **Critical Priority** (Not Started)
**Work Package**: WP6-Cleanup-2 - Payment Processing Vertical Complete Implementation
**Epic**: Clean Architecture Cleanup Phase

## Overview

Complete the ECPay payment integration that has 8 critical TODOs blocking core revenue functionality. This vertical slice handles subscription billing, payment retries, and cancellations - directly impacting business revenue.

## User Value Statement

**As a subscribing user**, I want **reliable payment processing with automatic retries and proper cancellation handling** so that **my subscription works smoothly without billing issues**.

## Business Impact

- **Revenue**: Critical payment processing functionality (direct revenue impact)
- **User Experience**: Prevents billing failures and subscription disruptions
- **Business Operations**: Enables proper payment retry and cancellation workflows

## Critical TODOs Being Resolved

### 🔥 Payment API Integration Missing (8 items)
- `src/coaching_assistant/core/services/ecpay_service.py:761`
  ```python
  # TODO: Call ECPay API to cancel authorization
  ```
- `src/coaching_assistant/core/services/ecpay_service.py:881`
  ```python
  # TODO: Implement ECPay manual retry API call
  ```
- `src/coaching_assistant/core/services/ecpay_service.py:999`
  ```python
  # TODO: If there's a net charge, process payment via ECPay
  ```
- `src/coaching_assistant/core/services/ecpay_service.py:1109`
  ```python
  # TODO: In production, call ECPay API to cancel authorization
  ```
- `src/coaching_assistant/core/services/ecpay_service.py:1113`
  ```python
  # TODO: Calculate refund if applicable
  ```
- `src/coaching_assistant/core/services/ecpay_service.py:672`
  ```python
  # TODO: Queue email notification (integrate with existing email system)
  ```
- `src/coaching_assistant/core/services/ecpay_service.py:820`
  ```python
  # TODO: Queue downgrade notification email
  ```
- `src/coaching_assistant/core/services/ecpay_service.py:1198`
  ```python
  # TODO: Implement actual notification sending
  ```

### 🔥 Background Task Integration Missing (3 items)
- `src/coaching_assistant/tasks/subscription_maintenance_tasks.py:120`
  ```python
  # TODO: Implement actual ECPay payment retry API call
  ```
- `src/coaching_assistant/tasks/subscription_maintenance_tasks.py:352`
  ```python
  # TODO: Replace with actual ECPay payment retry API call
  ```
- `src/coaching_assistant/tasks/subscription_maintenance_tasks.py:367`
  ```python
  # TODO: Replace with actual email service integration
  ```

## Architecture Compliance Issues Fixed

### Current Violations
- **Service Layer Incomplete**: Core payment service missing API integration
- **Task Queue Incomplete**: Background retry logic stubbed with TODOs
- **Notification System Missing**: Email integration not implemented

### Clean Architecture Solutions
- **Complete Service Implementation**: Full ECPay API integration in service layer
- **Infrastructure Integration**: Proper HTTP client adapters for external APIs
- **Notification Port Implementation**: Proper email service abstraction

## Implementation Tasks

### 1. ECPay API Client Implementation
- **File**: `src/coaching_assistant/infrastructure/http/ecpay_client.py` (new)
- **Requirements**:
  - HTTP client for ECPay API endpoints
  - Payment authorization cancellation
  - Manual payment retry API calls
  - Refund calculation and processing
  - Proper error handling and logging

### 2. Complete ECPay Service Implementation
- **File**: `src/coaching_assistant/core/services/ecpay_service.py`
- **Requirements**:
  - Remove all 8 TODO comments
  - Implement complete payment processing logic
  - Proper business rule validation
  - Integration with HTTP client adapter

### 3. Notification Service Integration
- **Files**:
  - `src/coaching_assistant/core/repositories/ports.py` (add NotificationPort)
  - `src/coaching_assistant/infrastructure/email/notification_service.py` (new)
- **Requirements**:
  - Email notification port definition
  - Email service implementation
  - Integration with ECPay service for payment notifications

### 4. Background Task Completion
- **File**: `src/coaching_assistant/tasks/subscription_maintenance_tasks.py`
- **Requirements**:
  - Remove all 3 TODO comments
  - Implement actual payment retry logic
  - Complete email notification integration
  - Proper error handling and retry strategies

### 5. API Layer Integration
- **File**: `src/coaching_assistant/api/v1/subscriptions.py`
- **Requirements**:
  - Update subscription management endpoints
  - Add payment retry and cancellation endpoints
  - Proper error responses for payment failures

### 6. Factory Pattern Integration
- **File**: `src/coaching_assistant/infrastructure/factories.py`
- **Requirements**:
  - Add ECPay service factory with HTTP client injection
  - Add notification service factory
  - Complete dependency injection

## E2E Demonstration Workflow

### Demo Script: "Subscription Payment Lifecycle"

**Pre-requisites**: Test ECPay sandbox environment, test user with subscription

1. **Create Subscription** - POST `/api/v1/subscriptions`
   ```json
   {
     "plan_id": "PRO",
     "payment_method": "ecpay_credit_card"
   }
   ```
   - Verify ECPay authorization created
   - Expected: 201 Created with subscription details

2. **Simulate Payment Failure** - Trigger payment retry scenario
   - Background task detects failed payment
   - Expected: Automatic retry via ECPay API

3. **Manual Payment Retry** - POST `/api/v1/subscriptions/{id}/retry-payment`
   - Verify manual retry triggers ECPay API call
   - Expected: 200 OK with retry status

4. **Plan Upgrade with Payment** - PATCH `/api/v1/subscriptions/{id}/plan`
   ```json
   {
     "new_plan_id": "ENTERPRISE"
   }
   ```
   - Verify prorated payment calculation
   - Verify ECPay charge processing
   - Expected: Successful upgrade with payment confirmation

5. **Subscription Cancellation** - DELETE `/api/v1/subscriptions/{id}`
   - Verify ECPay authorization cancellation
   - Verify refund calculation (if applicable)
   - Verify cancellation notification email
   - Expected: Proper cancellation with refund processing

6. **Email Notifications Verification** - Check notification system
   - Payment failure notification sent
   - Retry success notification sent
   - Cancellation confirmation sent
   - Expected: All relevant emails delivered

## Success Metrics

### Functional Validation
- ✅ All payment-related TODOs removed from codebase
- ✅ Complete payment lifecycle functional (create → retry → upgrade → cancel)
- ✅ ECPay API integration working in sandbox environment
- ✅ Email notifications sent for all payment events
- ✅ Refund calculations and processing working correctly

### Architecture Validation
- ✅ ECPay service uses HTTP client adapter (no direct API calls)
- ✅ Notification system uses port abstraction
- ✅ Clean Architecture compliance: Core ← Infrastructure
- ✅ Factory pattern provides proper dependency injection

### Business Validation
- ✅ Payment retry logic prevents subscription cancellations
- ✅ Refund processing handles cancellations properly
- ✅ User receives clear notifications about payment status
- ✅ Billing operations can manage failed payments effectively

## Testing Strategy

### Unit Tests (Required)
```bash
# Test ECPay service business logic
pytest tests/unit/core/services/test_ecpay_service.py -v

# Test notification service
pytest tests/unit/infrastructure/test_notification_service.py -v
```

### Integration Tests (Required)
```bash
# Test ECPay API client
pytest tests/integration/infrastructure/test_ecpay_client.py -v

# Test subscription tasks
pytest tests/integration/tasks/test_subscription_maintenance_tasks.py -v
```

### E2E Tests (Required)
```bash
# Complete payment workflow
pytest tests/e2e/test_subscription_payment_lifecycle.py -v
```

### Manual Verification (Required)
- ECPay sandbox environment payment processing
- Email notifications received in test inbox
- Billing dashboard shows proper payment status
- Refund processing visible in admin interface

## Dependencies

### Blocked By
- None (can start immediately)

### Blocking
- **WP6-Cleanup-4**: Notification system completion enables other features
- **Revenue Operations**: Billing reliability depends on this

### External Dependencies
- **ECPay Sandbox Access**: Required for testing
- **Email Service Configuration**: Required for notifications

## Definition of Done

- [ ] All 11 payment-related TODO comments removed
- [ ] ECPay API client fully implemented with proper error handling
- [ ] Payment retry logic working in background tasks
- [ ] Email notification system integrated and functional
- [ ] Refund calculation and processing implemented
- [ ] E2E payment lifecycle demo passes automated tests
- [ ] ECPay sandbox testing successful
- [ ] All payment failure scenarios handled gracefully
- [ ] Admin interface shows payment status correctly
- [ ] Code review completed and approved
- [ ] Documentation updated with payment API behavior

## Risk Assessment

### Technical Risks
- **Medium**: ECPay API integration complexity
- **Medium**: Email service integration reliability
- **Low**: Background task queue performance

### Business Risks
- **High Impact if Delayed**: Revenue processing remains unreliable
- **Customer Impact**: Payment failures could cause subscription cancellations
- **Compliance Risk**: Proper refund handling required for customer protection

## Security Considerations

- **Payment Data**: Ensure PCI compliance in API handling
- **API Keys**: Secure ECPay credential management
- **Audit Trail**: Proper logging of all payment operations
- **Error Handling**: No sensitive data in error messages

## Delivery Timeline

- **Estimated Effort**: 3-4 days (1 developer)
- **Critical Path**: ECPay client → service integration → task completion → testing
- **Deliverable**: Fully functional payment processing with E2E demo

---

## Related Work Packages

- **WP6-Cleanup-1**: Independent (can run in parallel)
- **WP6-Cleanup-3**: Independent (can run in parallel)
- **WP6-Cleanup-4**: Notification system enables other features

This work package resolves critical revenue-impacting functionality and ensures reliable subscription billing operations.