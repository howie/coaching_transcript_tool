# User Repository Critical Fix - September 15, 2025

## Problem Summary

During Phase 2 Clean Architecture migration, the application encountered critical database connection errors when accessing user-related endpoints like `/api/plans/current` and `/api/v1/subscriptions/current`.

## Technical Root Cause

The issue occurred because:

1. **Two Separate ORM Model Systems**: The codebase had both legacy models (`src/coaching_assistant/models/`) and new infrastructure models (`src/coaching_assistant/infrastructure/db/models/`)
2. **Registry Mismatch**: The new `UserModel` in infrastructure was not registered with the existing database session's SQLAlchemy metadata
3. **Repository Mismatch**: The user repository was trying to use the new `UserModel` but the session only knew about legacy models

## Solution Applied

**File Modified**: `src/coaching_assistant/infrastructure/db/repositories/user_repository.py`

### Changes Made:

1. **Import Update**:
   ```python
   # Before:
   from ..models.user_model import UserModel

   # After:
   from ....models.user import User as UserModel  # Temporarily use legacy model
   ```

2. **Domain Conversion Method Added**:
   ```python
   def _to_domain(self, orm_user: UserModel) -> DomainUser:
       """Convert ORM User to domain User."""
       return DomainUser(
           id=orm_user.id,
           email=orm_user.email,
           name=orm_user.name,
           # ... other field mappings
       )
   ```

3. **Method Updates**: All repository methods updated to use `self._to_domain()` instead of `orm_user.to_domain()`

4. **Manual Field Mapping**: Updated save/update operations to manually map domain model fields to ORM fields

## Architecture Benefits Maintained

✅ **Clean Architecture Preserved**:
- Repository still implements the `UserRepoPort` interface
- Domain models still used in use cases and controllers
- Dependency injection still works through factories
- No business logic in the repository

✅ **Immediate Functionality**:
- All API endpoints now work properly
- No more database connection errors
- Frontend can successfully load user plans and subscriptions

## Current State

**Hybrid Approach**: Using legacy User ORM model in repository with proper domain model conversion

**Why This Works**:
- Legacy User model is registered with the existing database session
- Repository converts between ORM and domain models properly
- Clean Architecture principles maintained at the boundaries
- Zero impact on use cases or API controllers

## Future Migration Path (Phase 3)

When ready for complete infrastructure model consolidation:

1. **Update Database Initialization**: Register infrastructure models with the session
2. **Switch Back to Infrastructure UserModel**: Revert to using the new UserModel
3. **Complete Migration**: Move all repositories to infrastructure models
4. **Retire Legacy Models**: Remove legacy model files

## Lessons Learned

1. **SQLAlchemy Registry Matters**: All ORM models must be registered with the same metadata/session
2. **Gradual Migration**: Hybrid approaches can provide stable bridges during large migrations
3. **Architecture Benefits**: Clean Architecture patterns made this fix much easier by isolating the change to one repository
4. **Testing Critical**: Repository pattern allowed the fix without changing any use cases or controllers

## Files Changed

- `src/coaching_assistant/infrastructure/db/repositories/user_repository.py` - Main fix
- `docs/features/refactor-architecture/phase-2-api-migration.md` - Documentation update
- `docs/features/refactor-architecture/README.md` - Status update
- `CLAUDE.md` - Migration status update

## Verification

✅ API server starts without errors
✅ `/api/plans/current` returns proper responses
✅ `/api/v1/subscriptions/current` works correctly
✅ Frontend no longer shows database connection errors
✅ All existing functionality preserved