# Subagents Quick Reference

## 🎯 Quick Selection Guide

### "I need to..."

| Task | Use This Agent | Example Command |
|------|---------------|-----------------|
| Review my code | `code-reviewer` | "Review the changes I just made" |
| Fix a failing test | `debugger` | "Debug why test_transcription is failing" |
| Add tests | `test-writer` | "Add tests for the new API endpoint" |
| Create an API | `api-designer` | "Design API for user preferences" |
| Change database | `database-migrator` | "Add a status field to sessions table" |
| Fix slow queries | `performance-optimizer` | "Optimize the transcript search query" |
| Update packages | `dependency-updater` | "Update all Python packages" |
| Setup Docker | `docker-builder` | "Create Dockerfile for the API service" |
| Analyze errors | `error-analyzer` | "Analyze the 500 errors from yesterday" |
| Security check | `security-auditor` | "Review code for security issues" |
| Add background job | `celery-task-designer` | "Create task for email notifications" |
| Add translations | `i18n-translator` | "Add Spanish translations" |

## 🔄 Common Workflows

### New Feature
```
api-designer → database-migrator → test-writer → code-reviewer
```

### Bug Fix
```
error-analyzer → debugger → test-writer → code-reviewer
```

### Performance Fix
```
performance-optimizer → database-migrator (if indexes needed) → test-writer
```

### Pre-Deployment
```
dependency-updater → security-auditor → docker-builder → test-writer
```

## 💡 Decision Tree

```
Is it a bug?
├─ YES → debugger or error-analyzer
└─ NO → Is it a new feature?
    ├─ YES → Is it an API?
    │   ├─ YES → api-designer
    │   └─ NO → Is it a background task?
    │       ├─ YES → celery-task-designer
    │       └─ NO → general-purpose
    └─ NO → Is it optimization?
        ├─ YES → performance-optimizer
        └─ NO → Is it maintenance?
            ├─ YES → dependency-updater or docker-builder
            └─ NO → code-reviewer
```

## ⚡ Slash Commands

```bash
/test-quick     # Fast unit tests only
/test-full      # Complete test suite
/lint-fix       # Auto-fix code style
/coverage       # Coverage report
/deps-check     # Check outdated packages
/db-status      # Migration status
/api-docs       # Generate API docs
/clean          # Clean temp files
```

## 🎭 Agent Capabilities

### 👀 Read-Only (Safe)
- `code-reviewer` - Reviews without changing
- `security-auditor` - Scans for vulnerabilities
- `error-analyzer` - Analyzes logs
- `performance-optimizer` - Profiles code

### ✏️ Can Modify Code
- `api-designer` - Creates/modifies APIs
- `database-migrator` - Changes schema
- `test-writer` - Adds/updates tests
- `debugger` - Fixes bugs
- `celery-task-designer` - Creates tasks
- `docker-builder` - Updates containers
- `dependency-updater` - Updates packages
- `i18n-translator` - Manages translations

### 🔧 System Commands
- `database-migrator` - Runs alembic
- `docker-builder` - Docker/compose commands
- `dependency-updater` - pip/npm commands
- `post-commit-updater` - git/make commands

## 📊 Agent Selection Matrix

| Your Situation | Best Agent | Alternative |
|---------------|------------|-------------|
| Tests are failing | `debugger` | `error-analyzer` |
| Need new endpoint | `api-designer` | `general-purpose` |
| Database changes | `database-migrator` | - |
| Slow performance | `performance-optimizer` | `database-migrator` |
| Security review | `security-auditor` | `code-reviewer` |
| Update dependencies | `dependency-updater` | - |
| Container setup | `docker-builder` | - |
| Production errors | `error-analyzer` | `debugger` |
| Add async processing | `celery-task-designer` | `general-purpose` |
| Multiple languages | `i18n-translator` | - |
| Complex task | `general-purpose` | Multiple specific agents |
| After commit | `post-commit-updater` | - |

## 🚀 Pro Tips

1. **Use specific agents over general-purpose** when possible
2. **Chain agents** for complex workflows
3. **Run independent agents in parallel** for speed
4. **Always run test-writer** after making changes
5. **Use code-reviewer** before committing
6. **Run security-auditor** before deployment
7. **Let agents handle their specialty** - don't micromanage

## 📝 Example Commands

```bash
# Fix a bug
"The login endpoint returns 500 errors, use debugger to fix it"

# Add feature
"Use api-designer to create a notification preferences endpoint"

# Optimize
"The dashboard is slow, use performance-optimizer to improve it"

# Deploy prep
"Prepare for deployment: run security-auditor then docker-builder"

# Maintenance
"Use dependency-updater to update all packages to latest stable"
```

## ⚠️ Common Mistakes

❌ Using `general-purpose` for specific tasks  
✅ Use specialized agents

❌ Running agents sequentially when they could run in parallel  
✅ Run independent agents concurrently

❌ Not using `test-writer` after changes  
✅ Always add tests for new code

❌ Skipping `code-reviewer` before commit  
✅ Review all changes before committing

❌ Manual debugging instead of using `debugger`  
✅ Let debugger analyze systematically