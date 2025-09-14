# Git Worktree Feature Manager ✅ ACTIVE

**Status**: Available - Can be invoked via Task tool  
**Agent Type**: `git-worktree-feature-manager`

## Overview

The git-worktree-feature-manager provides isolated development environments using git worktrees. It handles the complete lifecycle of feature branch development including creation, validation, and cleanup with database migration safety checks.

## Capabilities

- **Isolated worktree creation** - Set up separate directories for feature development
- **Automatic branch creation** - Create and configure feature branches
- **Database migration safety** - Check for migration conflicts before switching
- **Clean branch switching** - Safely transition between development contexts
- **Worktree cleanup** - Remove completed feature environments
- **State consistency** - Maintain proper git and database state

## When to Use

### ✅ Ideal Scenarios
- **New feature development** - Starting work on isolated features
- **Database schema changes** - Features that modify database structure
- **Experimental work** - Testing approaches without affecting main development
- **Parallel development** - Multiple features being developed simultaneously
- **Clean environment needs** - When main workspace has conflicts or issues

### ✅ Database Safety Features
This agent is especially valuable when:
- Working with database migrations
- Features involve schema changes
- Multiple developers working on DB-related features
- Need to prevent migration conflicts

## Usage Pattern

```typescript
// Invoke via Task tool
Task(
  subagent_type: "git-worktree-feature-manager",
  description: "Set up isolated feature development",
  prompt: "I want to start working on [feature description]. 
  Set up an isolated git worktree with proper branch creation and 
  database migration safety checks."
)
```

## Core Operations

### 1. Feature Development Setup
- Create isolated worktree directory
- Set up new feature branch
- Validate database state
- Configure development environment

### 2. Safe Branch Switching
- Check for uncommitted changes
- Validate database migration state
- Switch to target branch safely
- Update development environment

### 3. Feature Completion
- Merge feature branch (if requested)
- Clean up worktree directory
- Switch back to main development
- Maintain state consistency

### 4. Abandonment/Cleanup
- Safe removal of failed experiments
- Cleanup of temporary worktrees
- Restoration of main development state

## Examples

### New Feature Development
```
Description: "Start user authentication feature"
Prompt: "I want to start developing a new user authentication feature that will 
include database changes for user tables and JWT token management. Set up an 
isolated development environment with proper safety checks."
```

### Experimental Implementation
```
Description: "Test Clean Architecture approach" 
Prompt: "I want to experiment with implementing Clean Architecture patterns 
without affecting the main codebase. Set up an isolated worktree for this 
experimental work."
```

### Switch Back to Main
```
Description: "Return to main development"
Prompt: "I'm done with the authentication feature development. Switch me back 
to the main branch and clean up the feature worktree safely."
```

### Abandon Failed Approach
```
Description: "Abandon experimental feature"
Prompt: "This experimental approach isn't working out. I want to abandon this 
feature branch and clean up the worktree safely."
```

## Safety Mechanisms

### Database Migration Checks
- **Migration state validation** - Ensure migrations are in sync
- **Conflict detection** - Identify potential migration conflicts
- **Safe rollback** - Revert database changes if needed
- **State consistency** - Maintain database integrity

### Git State Management
- **Working directory checks** - Ensure clean working state
- **Branch validation** - Verify branch relationships
- **Remote synchronization** - Keep branches in sync with remote
- **Conflict prevention** - Avoid merge conflicts

### Environment Validation
- **Dependency checks** - Ensure environment is properly configured
- **Configuration validation** - Check environment variables and settings
- **Service availability** - Verify required services are running

## Workflow Integration

### Feature Development Lifecycle
```
Idea → worktree setup → development → testing → completion → cleanup
```

### Database Change Workflow
```
Schema Planning → isolated worktree → migration development → testing → merge
```

### Experimental Development
```
Hypothesis → isolated environment → experimentation → evaluation → decision
```

## Best Practices

### When Starting Features
- **Clear feature scope** - Define what the feature will include
- **Database impact** - Identify any schema changes needed
- **Timeline estimation** - Consider how long development will take
- **Dependency analysis** - Understand what other features might be affected

### During Development
- **Regular commits** - Keep work saved and trackable
- **Migration testing** - Test database changes thoroughly
- **Documentation updates** - Keep docs current in the worktree
- **Integration testing** - Test with other features periodically

### When Completing Features
- **Code review** - Review all changes before merging
- **Testing validation** - Ensure all tests pass
- **Documentation sync** - Update main documentation
- **Clean closure** - Properly close and clean up worktree

## Common Workflows

### Standard Feature Development
1. **Setup** - Create isolated worktree and branch
2. **Development** - Implement feature in isolation
3. **Testing** - Validate functionality and integration
4. **Review** - Code review and refinement
5. **Merge** - Integrate into main codebase
6. **Cleanup** - Remove worktree and temporary files

### Database Schema Changes
1. **Isolation** - Create worktree for schema work
2. **Migration development** - Create and test migrations
3. **Data migration** - Test with real data scenarios
4. **Rollback testing** - Ensure safe rollback capability
5. **Integration** - Merge with migration safety checks
6. **Cleanup** - Clean worktree and validate final state

## Troubleshooting

### Common Issues
- **Migration conflicts** - Multiple developers changing schema
- **Worktree conflicts** - Overlapping worktree directories
- **Branch sync issues** - Remote/local branch inconsistencies
- **Database state problems** - Migration state mismatches

### Recovery Strategies
- **State validation** - Check and fix git and database state
- **Manual cleanup** - Remove problematic worktrees manually
- **Branch recovery** - Restore branches from remote if needed
- **Database rollback** - Revert database to known good state

## Integration Points

### With Development Workflow
- **CI/CD integration** - Ensure worktree changes work with build systems
- **Team coordination** - Communicate worktree usage to team
- **Testing infrastructure** - Integrate with testing environments

### With Database Management
- **Migration tools** - Work with Alembic or other migration systems
- **Database snapshots** - Use snapshots for safety
- **Backup strategies** - Ensure data safety during development

## Related Agents

- **[general-purpose](./general-purpose.md)** - For complex feature work requiring multiple capabilities
- **[database-query-analyzer](./database-query-analyzer.md)** - For analyzing database state and changes

---

**Agent Type**: `git-worktree-feature-manager`  
**Availability**: ✅ Active  
**Tool Access**: All available tools  
**Primary Use**: Isolated feature development with git worktrees and database safety