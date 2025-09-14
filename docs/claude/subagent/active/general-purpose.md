# General-Purpose Subagent ✅ ACTIVE

**Status**: Available - Can be invoked via Task tool  
**Agent Type**: `general-purpose`

## Overview

The general-purpose subagent handles complex, multi-step tasks that require diverse capabilities and coordination across multiple domains. It's the most versatile agent available.

## Capabilities

- **Multi-domain expertise** - Can handle code, documentation, research, and planning
- **Complex task coordination** - Orchestrates multi-step workflows
- **Comprehensive analysis** - Deep investigation of problems across the codebase
- **Research and planning** - Gathering information and creating implementation plans

## When to Use

### ✅ Ideal Scenarios
- **Complex refactoring** - Major architectural changes
- **Feature implementation** - End-to-end feature development
- **Multi-file operations** - Changes spanning multiple files/directories
- **Research tasks** - Investigating unfamiliar codebases or technologies
- **Planning complex work** - Breaking down large tasks into steps
- **Cross-cutting concerns** - Tasks affecting multiple layers/domains

### ❌ Avoid For
- **Simple, single-domain tasks** - Use specific patterns instead
- **Quick file edits** - Direct tool usage is faster
- **Single-purpose research** - Use web-research-agent instead

## Usage Pattern

```typescript
// Invoke via Task tool
Task(
  subagent_type: "general-purpose",
  description: "Brief task description",
  prompt: "Detailed task requirements and context"
)
```

## Examples

### Complex Architecture Refactoring
```
Description: "Implement Clean Architecture refactoring"
Prompt: "Analyze the current codebase architecture, identify violations of 
Clean Architecture principles, and implement a comprehensive refactoring plan 
including repository patterns, use cases, and dependency injection."
```

### Feature Implementation
```
Description: "Implement user authentication system" 
Prompt: "Design and implement a complete user authentication system including:
- JWT token management
- Database schema updates
- API endpoints for login/logout/register
- Frontend integration
- Security best practices"
```

### Cross-Project Analysis
```
Description: "Analyze performance bottlenecks"
Prompt: "Investigate performance issues across the application stack:
- Database query optimization
- API response time analysis  
- Frontend rendering performance
- Caching opportunities
- Provide specific recommendations with implementation details"
```

## Strengths

- **Comprehensive approach** - Considers all aspects of a problem
- **Context awareness** - Understands relationships between different parts
- **Tool versatility** - Can use any available tool as needed
- **Planning capability** - Creates structured approaches to complex problems
- **Quality focus** - Maintains high standards across all work

## Limitations

- **May be overkill** - For simple tasks, direct approaches are faster
- **Resource intensive** - Uses more context and processing time
- **Broad focus** - May not have the specific expertise of domain agents

## Best Practices

### Task Definition
- **Be specific about outcomes** - Clearly state what success looks like
- **Provide context** - Include relevant background information
- **Set boundaries** - Specify what's in/out of scope
- **Include constraints** - Time, resource, or compatibility limitations

### Working with Results
- **Review comprehensively** - Check all aspects of complex deliverables  
- **Test thoroughly** - Multi-step changes need comprehensive testing
- **Document decisions** - Complex work should be well-documented
- **Plan rollback** - Have backup plans for major changes

## Integration with Workflow

### Sequential Pattern
```
general-purpose (analysis) → specific patterns (implementation)
```

### Parallel Coordination
```
general-purpose coordinates multiple specific agents
```

### Iterative Refinement
```
general-purpose (initial) → feedback → general-purpose (refined)
```

## Success Metrics

- **Task completion** - All specified objectives achieved
- **Quality maintenance** - Code quality and standards preserved  
- **Documentation updates** - All changes properly documented
- **Test coverage** - Appropriate testing implemented
- **Integration success** - Changes work correctly with existing system

## Related Patterns

- **[post-commit-updater](./post-commit-updater.md)** - For maintenance after complex changes
- **[web-research-agent](./web-research-agent.md)** - For research components of complex tasks
- **[database-query-analyzer](./database-query-analyzer.md)** - For data analysis aspects

---

**Agent Type**: `general-purpose`  
**Availability**: ✅ Active  
**Tool Access**: All available tools  
**Use Cases**: Complex, multi-step, multi-domain tasks