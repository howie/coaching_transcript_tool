# Post-Commit Updater Subagent ✅ ACTIVE

**Status**: Available - Can be invoked via Task tool  
**Agent Type**: `post-commit-updater`

## Overview

The post-commit-updater subagent handles maintenance tasks that should be performed after code commits. It ensures project state remains consistent and documentation stays up-to-date.

## Capabilities

- **Memory bank updates** - Refresh project context and documentation
- **Documentation sync** - Keep documentation current with code changes
- **Progress tracking** - Update project progress indicators
- **Artifact generation** - Run repomix and other documentation tools
- **Cleanup tasks** - Remove temporary files and outdated artifacts

## When to Use

### ✅ Ideal Scenarios
- **After major commits** - When significant changes have been made
- **Feature completion** - When a feature is fully implemented
- **Documentation updates needed** - When docs need to reflect code changes
- **Project milestone reached** - At completion of significant work
- **Before team handoffs** - Ensure everything is current for other developers

### ✅ Automatic Triggers
The CLAUDE.md specifies this agent should be used proactively after commits:
- User explicitly requests post-commit tasks
- After completing significant feature work
- When memory bank needs updating

## Usage Pattern

```typescript
// Invoke via Task tool
Task(
  subagent_type: "post-commit-updater",
  description: "Update project after commits",
  prompt: "I just committed changes for [feature/fix description]. 
  Please update the memory bank, run repomix, and execute the progress sync script."
)
```

## Core Tasks

### 1. Memory Bank Updates
- Update project context files
- Refresh architectural documentation
- Sync feature status and progress

### 2. Documentation Generation  
- Run repomix to update codebase summaries
- Generate updated API documentation
- Refresh configuration guides

### 3. Progress Synchronization
- Execute progress sync scripts
- Update project status indicators
- Refresh milestone tracking

### 4. Artifact Maintenance
- Clean up temporary debug files
- Update build artifacts if needed
- Refresh dependency documentation

## Examples

### After Feature Implementation
```
Description: "Update after authentication feature"
Prompt: "I just committed the new JWT authentication system including:
- User login/logout endpoints
- Database schema changes  
- Frontend integration
- Security middleware

Please update the memory bank, run repomix, and sync all documentation."
```

### After Bug Fixes
```
Description: "Update after critical bug fixes"
Prompt: "Just committed fixes for 3 critical bugs in the session management system.
Need to update project state and ensure all documentation reflects the fixes."
```

### After Architecture Changes
```
Description: "Update after Clean Architecture refactoring"
Prompt: "Completed Phase 1 of Clean Architecture implementation with repository 
pattern and use cases. Need comprehensive project state update including 
memory bank refresh and progress sync."
```

## Tool Usage

This agent has access to all tools and typically uses:

- **Read/Write/Edit** - Update documentation files
- **Bash** - Run scripts (repomix, progress sync)
- **Glob/Grep** - Find and analyze project files  
- **TodoWrite** - Update task tracking if needed
- **WebFetch** - Update external documentation if needed

## Integration Points

### With Development Workflow
```
Code Changes → Commit → post-commit-updater → Team Handoff
```

### With Documentation Pipeline
```
post-commit-updater → Memory Bank → repomix → Updated Context
```

### With Progress Tracking
```
Feature Complete → post-commit-updater → Progress Sync → Status Updates
```

## Best Practices

### When to Invoke
- **After significant commits** - Don't use for tiny changes
- **Before team handoffs** - Ensure clean state for others
- **At milestone completion** - Keep progress current
- **After architectural changes** - Major changes need full updates

### What to Include in Prompt
- **Summary of changes** - What was implemented/fixed
- **Scope of impact** - Which parts of system were affected
- **Documentation needs** - What docs might need updating
- **Special considerations** - Any unique aspects of the changes

## Expected Outcomes

### Successful Completion
- ✅ Memory bank reflects current code state
- ✅ repomix output is current 
- ✅ Progress indicators are accurate
- ✅ Documentation is synchronized
- ✅ Temporary files cleaned up

### Quality Checks
- All documentation files have consistent formatting
- No broken internal links in documentation
- Progress indicators match actual completion state
- Generated artifacts are current and valid

## Common Workflows

### Standard Post-Commit Flow
1. **Assess changes** - Understand scope of updates needed
2. **Update memory bank** - Refresh project context
3. **Run documentation tools** - Execute repomix and similar
4. **Sync progress** - Update status and milestone tracking
5. **Clean up** - Remove outdated artifacts

### Feature Completion Flow  
1. **Document feature** - Ensure feature is properly documented
2. **Update architecture docs** - If architectural changes were made
3. **Refresh API docs** - If API changes were made
4. **Progress milestone** - Mark feature as complete
5. **Team notification** - Prepare handoff materials

## Troubleshooting

### Common Issues
- **Script failures** - Check for missing dependencies or permissions
- **Documentation conflicts** - Resolve merge conflicts in generated docs
- **Progress sync errors** - Verify progress tracking infrastructure

### Recovery
- **Partial completion** - Re-run with specific focus areas
- **Script errors** - Debug and fix individual components
- **Rollback needs** - Restore previous states if needed

## Related Agents

- **[general-purpose](./general-purpose.md)** - For complex multi-step tasks that need post-commit work
- **[web-research-agent](./web-research-agent.md)** - May be used for documentation research
- Workflow patterns in `../planned/` - Follow manual patterns when agent unavailable

---

**Agent Type**: `post-commit-updater`  
**Availability**: ✅ Active  
**Tool Access**: All available tools  
**Primary Use**: Maintenance tasks after code commits