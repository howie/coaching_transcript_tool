# Planned Subagents - Workflow Patterns 📋

This directory contains documentation for workflow patterns and future subagent implementations. These are **not actual agents** that can be invoked via the Task tool - they represent best practices and structured approaches to common development tasks.

## Purpose

These documents serve as:
- **Workflow guidelines** - Structured approaches to common tasks
- **Best practices** - Proven patterns for development activities
- **Future implementations** - Specifications for potential agents
- **Team standards** - Consistent approaches across the team

## How to Use

### ❌ Cannot Invoke as Agents
```typescript
// This will NOT work - these are not real agents:
Task(subagent_type: "code-reviewer", ...)  // ❌ Does not exist
```

### ✅ Use as Workflow Patterns
Instead, follow the documented patterns manually:
1. Read the relevant pattern documentation
2. Follow the step-by-step workflow
3. Use the checklists and best practices
4. Adapt the pattern to your specific needs

## Available Patterns

### Code Quality & Testing
- **[code-reviewer](./code-reviewer.md)** - Systematic code review process
- **[test-writer](./test-writer.md)** - Comprehensive test creation workflow
- **[debugger](./debugger.md)** - Structured debugging methodology
- **[error-analyzer](./error-analyzer.md)** - Production error analysis process

### Architecture & Design  
- **[api-designer](./api-designer.md)** - RESTful API design process
- **[database-migrator](./database-migrator.md)** - Database schema change workflow
- **[performance-optimizer](./performance-optimizer.md)** - Performance analysis methodology
- **[celery-task-designer](./celery-task-designer.md)** - Background task design patterns

### DevOps & Maintenance
- **[security-auditor](./security-auditor.md)** - Security review checklist
- **[docker-builder](./docker-builder.md)** - Container optimization process
- **[dependency-updater](./dependency-updater.md)** - Package update workflow
- **[i18n-translator](./i18n-translator.md)** - Internationalization process

### Feature Development & Planning
- **[feature-analyst](./feature-analyst.md)** - Feature breakdown methodology
- **[user-story-designer](./user-story-designer.md)** - User story creation process
- **[product-planner](./product-planner.md)** - Epic planning workflow
- **[requirements-analyst](./requirements-analyst.md)** - Requirements analysis process

## Migration Path

When these patterns become actual agents:
1. **Implementation** - Convert pattern to agent specification
2. **Testing** - Validate agent capabilities
3. **Documentation** - Move from `planned/` to `active/`
4. **Integration** - Update CLAUDE.md and references

## Pattern Structure

Each pattern document includes:
- **Purpose** - What the pattern accomplishes
- **When to Use** - Scenarios where pattern applies
- **Step-by-Step Process** - Detailed workflow
- **Checklists** - Quality gates and validation points
- **Tools Required** - What tools/skills are needed
- **Best Practices** - Tips for optimal results
- **Common Pitfalls** - What to avoid
- **Examples** - Real-world usage scenarios

## Integration with Active Agents

Planned patterns often work well with active agents:

```typescript
// Use active agent for complex analysis
Task(subagent_type: "general-purpose", 
     prompt: "Follow the code-reviewer pattern from docs/claude/subagent/planned/code-reviewer.md...")

// Use active agent for research aspects
Task(subagent_type: "web-research-agent",
     prompt: "Research best practices for the security-auditor workflow...")
```

---

**Status**: 📋 Workflow Patterns (Not Invokable Agents)  
**Usage**: Manual workflow implementation  
**Future**: Potential conversion to active agents