# Subagents Documentation

This directory organizes documentation for Claude Code subagents based on their actual availability and implementation status.

## Directory Structure

### 📁 [active/](./active/) - Available Subagents ✅
Contains documentation for subagents that are **actually available** in the Claude Code system and can be invoked via the Task tool.

**Currently Available:**
- **[general-purpose](./active/general-purpose.md)** - Complex multi-step tasks
- **[post-commit-updater](./active/post-commit-updater.md)** - Post-commit maintenance tasks  
- **[web-research-agent](./active/web-research-agent.md)** - Web research and documentation lookups
- **[git-worktree-feature-manager](./active/git-worktree-feature-manager.md)** - Git worktree and branch management
- **[database-query-analyzer](./active/database-query-analyzer.md)** - Database analysis and monitoring

### 📁 [planned/](./planned/) - Planned Subagents 📋
Contains documentation for subagents that are **conceptual workflow patterns** or **future implementations**. These serve as guidelines but cannot be directly invoked as agents.

**Workflow Patterns:**
- **Code Quality & Testing**: code-reviewer, debugger, test-writer, error-analyzer
- **Architecture & Design**: api-designer, database-migrator, celery-task-designer, performance-optimizer
- **DevOps & Maintenance**: security-auditor, docker-builder, dependency-updater, i18n-translator
- **Feature Development**: feature-analyst, user-story-designer, product-planner, requirements-analyst

## How to Use This Documentation

### ✅ For Available Subagents
Use the Task tool to invoke these agents:
```
Task tool with subagent_type: "general-purpose"
Task tool with subagent_type: "post-commit-updater"
Task tool with subagent_type: "web-research-agent"
Task tool with subagent_type: "git-worktree-feature-manager" 
Task tool with subagent_type: "database-query-analyzer"
```

### 📋 For Planned Subagents
Follow the documented patterns manually or as implementation guides:
- Use the workflow descriptions as best practices
- Follow the responsibility breakdowns for task organization
- Consider the patterns when planning complex tasks

## Quick Reference

| Need | Available Agent | Alternative Pattern |
|------|----------------|-------------------|
| Complex tasks | ✅ `general-purpose` | - |
| Post-commit work | ✅ `post-commit-updater` | - |
| Web research | ✅ `web-research-agent` | Manual web search |
| Git workflows | ✅ `git-worktree-feature-manager` | Manual git commands |
| Database queries | ✅ `database-query-analyzer` | Manual SQL queries |
| Code review | ❌ | Follow `planned/code-reviewer.md` |
| API design | ❌ | Follow `planned/api-designer.md` |
| Testing | ❌ | Follow `planned/test-writer.md` |
| Performance | ❌ | Follow `planned/performance-optimizer.md` |

## Migration Notes

When new subagents become available:
1. Move documentation from `planned/` to `active/`
2. Update this README with the new agent
3. Update CLAUDE.md references
4. Test the agent invocation

## See Also

- **[Main Subagents Guide](../subagents.md)** - Comprehensive overview and usage patterns
- **[CLAUDE.md Work Modes](../../../CLAUDE.md#work-modes--subagents)** - Integration with development workflow
- **[Quick Reference](../subagents-quick-reference.md)** - Cheat sheet for common scenarios

---

**Last Updated**: 2025-01-14  
**Active Agents**: 5  
**Planned Patterns**: 16