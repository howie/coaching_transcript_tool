# Clean Architecture Migration Status

This document tracks the ongoing migration to Clean Architecture principles and the status of legacy component transitions.

## Migration Overview

The Coaching Assistant platform is undergoing a systematic migration to Clean Architecture to improve maintainability, testability, and separation of concerns.

## Current Status (Updated 2025-09-21)

### ✅ Phase 1 Complete - Foundation
- Repository ports defined in `core/repositories/ports.py`
- Infrastructure layer setup with dependency injection
- Pilot use case implementations demonstrate pattern

### ✅ Phase 2 Complete - API Endpoints Migration
- **CRITICAL FIX APPLIED**: User repository temporarily uses legacy User model to resolve database connection errors
- **API Functional**: All endpoints now working properly with Clean Architecture
- Use case implementations for key business workflows
- API controllers properly inject use cases via dependency injection

### 📅 Phase 3 Planned - Pure Domain Models
- Complete ORM model consolidation when time allows
- Pure domain model retirement of legacy models
- Full separation of business logic from infrastructure concerns

## Legacy Component Status

### 📁 Legacy Root Models (`src/coaching_assistant/models/`)
**Migration Status**: 🚨 **Being phased out** - use infrastructure/db/models/ for new code

**Current Legacy Models**:
- `PlanConfiguration` - being migrated to infrastructure layer
- `EcpaySubscription` - legacy payment integration
- Various ORM models mixed with business logic

**Guidance**:
- ❌ Avoid for new features
- ⚠️ Migrate when touching existing code
- ✅ Use infrastructure/db/models/ for new ORM entities

### 📁 Legacy Root Services (`src/coaching_assistant/services/`)
**Migration Status**: 🚨 **Being migrated** to core/services/ (use cases) and infrastructure/

**Current Legacy Services**:
- `GoogleSTT` - external service integration
- `TranscriptSmoother` - data processing logic
- `BillingAnalyticsService` - business logic mixed with data access

**Issues**:
- Often contain both business logic AND infrastructure concerns
- Direct database access mixed with domain logic
- Difficult to test in isolation

**Guidance**:
- ❌ Don't create new legacy services
- 🏗️ Use existing services for now
- ✅ Create new features using Clean Architecture (core/services/)

## Migration Strategy

### For New Features
1. Create business logic in `core/services/` as use cases
2. Define repository ports in `core/repositories/ports.py`
3. Implement repositories in `infrastructure/db/repositories/`
4. Keep API controllers thin - only HTTP concerns

### For Existing Code Modifications
1. Consider migrating to new structure when touching legacy code
2. Extract business logic to use cases
3. Use repository pattern for all data access
4. Maintain **dependency direction**: Core ← Infrastructure

### Migration Priorities
1. **High Priority**: Services with mixed business logic and infrastructure
2. **Medium Priority**: Models with complex business rules
3. **Low Priority**: Simple data models and utilities

## Key Architectural Rules (Never Violate)

1. **Core Services**: ZERO SQLAlchemy imports or Session dependencies
2. **API Layer**: Only HTTP concerns, no business logic or direct DB access
3. **Repository Pattern**: All data access through repository ports
4. **Dependency Direction**: Core → Infrastructure, never the reverse

## Success Metrics

- ✅ Zero SQLAlchemy imports in core/services/
- ✅ All new features use Clean Architecture patterns
- ✅ Business logic testable without database dependencies
- 🔄 Legacy services gradually replaced with use cases
- 🔄 Legacy models migrated to infrastructure layer

## Resources

- **Architectural Rules**: `@docs/features/refactor-architecture/architectural-rules.md`
- **Phase 3 Planning**: `@docs/features/refactor-architecture/phase-3-domain-models.md`
- **Success Metrics**: `@docs/features/refactor-architecture/success-metrics.md`
- **Implementation Guide**: `@docs/features/refactor-architecture/README.md`