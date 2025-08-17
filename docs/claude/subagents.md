# Subagents Guide

Specialized agents for specific tasks in the coaching assistant platform.

## Subagent Catalog

### Code Quality & Testing

#### code-reviewer
**Purpose**: Review code changes for quality, patterns, and best practices  
**Trigger**: After writing or modifying code  
**Tools**: Read, Grep, Glob  
**Responsibilities**:
- Check code style compliance
- Identify potential bugs
- Suggest refactoring opportunities
- Verify test coverage
- Ensure documentation is updated

#### debugger
**Purpose**: Diagnose and fix bugs or test failures  
**Trigger**: When tests fail or errors occur  
**Tools**: Read, Grep, Bash (test commands), Edit  
**Responsibilities**:
- Analyze error messages and stack traces
- Identify root causes
- Suggest fixes
- Verify fixes don't break other functionality

#### test-writer
**Purpose**: Create comprehensive test coverage  
**Trigger**: New features or insufficient coverage  
**Tools**: Read, Write, Edit  
**Responsibilities**:
- Write unit tests
- Create integration tests
- Add edge case coverage
- Mock external dependencies
- Ensure 85% minimum coverage

#### error-analyzer
**Purpose**: Analyze production errors and logs  
**Trigger**: Production issues or error pattern analysis  
**Tools**: Read, Grep, WebFetch  
**Responsibilities**:
- Parse error logs
- Identify error patterns
- Track down root causes
- Suggest preventive measures
- Create error reproduction tests

### Architecture & Design

#### api-designer
**Purpose**: Design and implement RESTful API endpoints  
**Trigger**: New API feature requirements  
**Tools**: Read, Write, Edit, Grep  
**Responsibilities**:
- Design API specifications (OpenAPI format)
- Implement FastAPI routers
- Create request/response schemas
- Add validation logic
- Update API documentation
- Ensure RESTful best practices

#### database-migrator
**Purpose**: Handle database schema changes and migrations  
**Trigger**: Model changes or new database requirements  
**Tools**: Read, Edit, Bash (alembic commands)  
**Responsibilities**:
- Analyze schema change requirements
- Generate Alembic migrations
- Verify upgrade/downgrade scripts
- Update SQLAlchemy models
- Update repository layer
- Test migration rollback

#### celery-task-designer
**Purpose**: Design and implement background tasks  
**Trigger**: Async processing requirements  
**Tools**: Read, Write, Edit  
**Responsibilities**:
- Design task architecture
- Implement retry logic
- Configure task routing
- Set up task monitoring
- Handle task failures
- Optimize task performance

#### performance-optimizer
**Purpose**: Analyze and optimize performance bottlenecks  
**Trigger**: Slow queries, high latency, performance issues  
**Tools**: Read, Bash, Grep  
**Responsibilities**:
- Analyze SQL query performance
- Identify N+1 query problems
- Suggest index optimizations
- Profile code execution
- Optimize Celery task execution
- Recommend caching strategies

### DevOps & Maintenance

#### security-auditor
**Purpose**: Review code for security vulnerabilities  
**Trigger**: Before deployment or security review  
**Tools**: Read, Grep, Glob  
**Responsibilities**:
- Check for SQL injection risks
- Identify authentication issues
- Review authorization logic
- Find exposed secrets
- Verify input validation
- Check dependency vulnerabilities

#### docker-builder
**Purpose**: Manage Docker configurations and builds  
**Trigger**: Container setup or deployment preparation  
**Tools**: Read, Write, Edit, Bash (docker commands)  
**Responsibilities**:
- Optimize Dockerfile
- Configure docker-compose
- Implement multi-stage builds
- Handle environment variables
- Minimize image size
- Set up health checks

#### dependency-updater
**Purpose**: Manage and update project dependencies  
**Trigger**: Scheduled maintenance or security updates  
**Tools**: Read, Edit, Bash (pip, npm commands)  
**Responsibilities**:
- Check for outdated packages
- Analyze breaking changes
- Update requirements.txt
- Update package.json
- Run compatibility tests
- Document upgrade notes

#### i18n-translator
**Purpose**: Handle internationalization and localization  
**Trigger**: New language support or translation updates  
**Tools**: Read, Edit, Write  
**Responsibilities**:
- Extract translatable strings
- Update language files
- Verify translation completeness
- Handle date/time formats
- Manage currency formats
- Test locale switching

### General Purpose

#### general-purpose
**Purpose**: Handle complex multi-step tasks  
**Trigger**: Tasks requiring multiple capabilities  
**Tools**: All available tools  
**Responsibilities**:
- Research and planning
- Multi-file operations
- Complex refactoring
- Feature implementation
- Documentation updates

#### post-commit-updater
**Purpose**: Update project state after commits  
**Trigger**: After code commits  
**Tools**: All available tools  
**Responsibilities**:
- Update memory bank
- Run repomix
- Execute progress sync
- Update documentation
- Tag releases

## Usage Patterns

### Sequential Pattern
When tasks have dependencies:
```
api-designer → database-migrator → test-writer → code-reviewer
```

### Parallel Pattern
When tasks are independent:
```
dependency-updater + security-auditor + performance-optimizer
```

### Hierarchical Pattern
When subtasks need delegation:
```
general-purpose → {
  api-designer
  database-migrator
  test-writer
}
```

## Subagent Selection Matrix

| Scenario | Primary Agent | Secondary Agents |
|----------|--------------|------------------|
| New Feature | api-designer | database-migrator, test-writer |
| Bug Fix | debugger | error-analyzer, test-writer |
| Performance Issue | performance-optimizer | database-migrator |
| Deployment Prep | docker-builder | security-auditor, dependency-updater |
| Code Quality | code-reviewer | test-writer |
| Database Change | database-migrator | test-writer |
| API Enhancement | api-designer | test-writer, code-reviewer |
| Production Error | error-analyzer | debugger |
| Package Update | dependency-updater | test-writer |
| Security Review | security-auditor | code-reviewer |

## Best Practices

### 1. Agent Selection
- Choose the most specific agent for the task
- Use general-purpose only for truly complex multi-domain tasks
- Consider using multiple specialized agents over one general agent

### 2. Task Decomposition
- Break complex tasks into smaller, agent-specific subtasks
- Define clear boundaries between agent responsibilities
- Document handoff points between agents

### 3. Error Handling
- Always have a fallback plan if an agent fails
- Log agent decisions for debugging
- Implement retry logic for transient failures

### 4. Performance
- Run independent agents in parallel when possible
- Cache agent results to avoid redundant work
- Monitor agent execution time

### 5. Communication
- Provide clear context to each agent
- Include relevant file paths and error messages
- Specify expected outputs explicitly

## Common Workflows

### Feature Development Workflow
```
1. api-designer: Design endpoint and schemas
2. database-migrator: Create necessary migrations
3. api-designer: Implement endpoint logic
4. celery-task-designer: Add background processing (if needed)
5. test-writer: Create comprehensive tests
6. code-reviewer: Review implementation
```

### Bug Fix Workflow
```
1. error-analyzer: Analyze error logs
2. debugger: Identify root cause
3. debugger: Implement fix
4. test-writer: Add regression test
5. code-reviewer: Verify fix
```

### Performance Optimization Workflow
```
1. performance-optimizer: Profile and identify bottlenecks
2. database-migrator: Add indexes (if needed)
3. performance-optimizer: Implement optimizations
4. test-writer: Add performance tests
5. code-reviewer: Review changes
```

### Deployment Workflow
```
1. dependency-updater: Update packages
2. security-auditor: Security review
3. docker-builder: Update containers
4. test-writer: Run full test suite
5. code-reviewer: Final review
```

## Agent Capabilities Reference

### Read-Only Agents
These agents only analyze, never modify:
- code-reviewer
- security-auditor
- error-analyzer
- performance-optimizer (analysis mode)

### Write-Capable Agents
These agents can modify code:
- api-designer
- database-migrator
- test-writer
- debugger
- celery-task-designer
- docker-builder
- dependency-updater
- i18n-translator

### System Command Agents
These agents can execute system commands:
- database-migrator (alembic)
- docker-builder (docker/docker-compose)
- dependency-updater (pip/npm)
- post-commit-updater (git/make)

## Monitoring & Metrics

Track these metrics for agent effectiveness:

1. **Success Rate**: Percentage of successful agent completions
2. **Execution Time**: Average time per agent type
3. **Retry Rate**: How often agents need to retry
4. **Handoff Success**: Success rate of multi-agent workflows
5. **Coverage Impact**: Test coverage change after test-writer
6. **Bug Detection**: Issues found by code-reviewer/security-auditor
7. **Performance Gains**: Improvements from performance-optimizer

## Future Enhancements

Planned improvements to the subagent system:

1. **Learning Capabilities**: Agents learn from past decisions
2. **Cross-Agent Communication**: Direct agent-to-agent messaging
3. **Custom Agent Creation**: User-defined specialized agents
4. **Agent Orchestration**: Automated workflow management
5. **Performance Profiling**: Built-in agent performance monitoring
6. **Rollback Capability**: Undo agent actions if needed