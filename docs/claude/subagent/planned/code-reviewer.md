# Code Reviewer Workflow Pattern 📋 PLANNED

**Status**: Workflow Pattern (Not an Invokable Agent)  
**Type**: Manual Process Following Best Practices

## Overview

This document outlines a systematic approach to code review that ensures quality, maintainability, and adherence to project standards. Follow this workflow when conducting thorough code reviews.

## Purpose

Provide a structured process for:
- **Quality assurance** - Identify bugs and code issues
- **Knowledge sharing** - Ensure team understanding of changes
- **Standards compliance** - Maintain consistent code quality
- **Best practices** - Apply proven patterns and approaches
- **Risk mitigation** - Catch potential problems early

## When to Use This Pattern

### ✅ Ideal Scenarios
- **After significant code changes** - New features or major refactoring
- **Pull request reviews** - Systematic review of team contributions
- **Pre-deployment validation** - Final quality check before release
- **Knowledge transfer** - Understanding complex code changes
- **Team onboarding** - Teaching standards to new team members

### ✅ Code Change Types
- New feature implementations
- Bug fixes and patches
- Performance optimizations
- Security improvements
- Architecture changes
- API modifications

## Step-by-Step Workflow

### Phase 1: Initial Assessment (5-10 minutes)

1. **Understand the Context**
   - [ ] Read PR/commit description and requirements
   - [ ] Review linked issues or tickets
   - [ ] Understand business context and goals
   - [ ] Check if changes align with project architecture

2. **Scope Analysis**
   - [ ] Identify all modified files and their relationships
   - [ ] Check for impact on existing functionality
   - [ ] Verify that scope matches stated objectives
   - [ ] Look for unexpected or unrelated changes

### Phase 2: Code Quality Review (15-30 minutes)

3. **Architecture & Design**
   - [ ] Verify adherence to Clean Architecture principles (if applicable)
   - [ ] Check separation of concerns
   - [ ] Validate dependency injection and inversion
   - [ ] Ensure proper layer boundaries are maintained
   - [ ] Review design patterns usage

4. **Code Style & Standards**
   - [ ] Check naming conventions (functions, variables, classes)
   - [ ] Verify code formatting and consistency
   - [ ] Ensure proper documentation and comments
   - [ ] Validate type hints and interface compliance
   - [ ] Check for code duplication

5. **Logic & Implementation**
   - [ ] Verify algorithm correctness and efficiency
   - [ ] Check edge case handling
   - [ ] Review error handling and recovery
   - [ ] Validate input sanitization and validation
   - [ ] Ensure proper resource management

### Phase 3: Security & Performance (10-15 minutes)

6. **Security Review**
   - [ ] Check for SQL injection vulnerabilities
   - [ ] Verify proper authentication and authorization
   - [ ] Review data exposure and privacy concerns
   - [ ] Check for hardcoded secrets or credentials
   - [ ] Validate input sanitization

7. **Performance Assessment**
   - [ ] Identify potential N+1 query problems
   - [ ] Check for expensive operations in loops
   - [ ] Review database query efficiency
   - [ ] Assess memory usage patterns
   - [ ] Validate caching strategies

### Phase 4: Testing & Documentation (10-15 minutes)

8. **Test Coverage**
   - [ ] Verify new functionality has appropriate tests
   - [ ] Check test quality and coverage
   - [ ] Ensure tests are maintainable and clear
   - [ ] Validate edge cases are tested
   - [ ] Review test data and mocking strategies

9. **Documentation Review**
   - [ ] Check API documentation updates
   - [ ] Verify README and setup instructions
   - [ ] Review inline code documentation
   - [ ] Ensure architectural docs are current
   - [ ] Validate changelog updates

### Phase 5: Integration & Deployment (5-10 minutes)

10. **Integration Concerns**
    - [ ] Check backward compatibility
    - [ ] Verify migration scripts if needed
    - [ ] Review environment variable changes
    - [ ] Check deployment configuration updates
    - [ ] Validate CI/CD pipeline changes

## Quality Checklists

### Critical Issues ❌ (Must Fix)
- [ ] **Security vulnerabilities** - SQL injection, XSS, authentication bypass
- [ ] **Data corruption risks** - Improper data handling or validation  
- [ ] **Performance regressions** - Significantly slower operations
- [ ] **Breaking changes** - Unintentional API or interface changes
- [ ] **Architecture violations** - Breaking established patterns

### Major Issues ⚠️ (Should Fix)
- [ ] **Code duplication** - Repeated logic that should be extracted
- [ ] **Poor error handling** - Missing or inadequate error recovery
- [ ] **Maintenance concerns** - Code that will be difficult to maintain
- [ ] **Missing tests** - Important functionality without test coverage
- [ ] **Documentation gaps** - Missing or outdated documentation

### Minor Issues ℹ️ (Nice to Fix)
- [ ] **Style inconsistencies** - Minor formatting or naming issues
- [ ] **Optimization opportunities** - Code that could be more efficient
- [ ] **Readability improvements** - Unclear variable names or logic
- [ ] **Documentation enhancements** - Could be more comprehensive

## Tools and Techniques

### Static Analysis Tools
- **Linting**: flake8, eslint, pylint
- **Type checking**: mypy, TypeScript compiler
- **Security scanning**: bandit, npm audit
- **Dependency analysis**: pip-audit, npm vulnerabilities

### Manual Review Techniques
- **Line-by-line reading** - Careful examination of each change
- **Cross-reference checking** - Verify consistency across related files  
- **Pattern recognition** - Identify common anti-patterns
- **Context switching** - Review from different perspectives (user, maintainer, security)

### Review Documentation
```markdown
## Code Review Checklist

### ✅ Quality Gates Passed
- [ ] Architecture compliance verified
- [ ] Security review completed
- [ ] Performance impact assessed
- [ ] Test coverage adequate
- [ ] Documentation updated

### 🔍 Issues Found
**Critical**: [List critical issues]
**Major**: [List major concerns]
**Minor**: [List minor suggestions]

### 💡 Recommendations
- [Specific improvement suggestions]
- [Best practice applications]
- [Future considerations]

### ✏️ Overall Assessment
[Summary of review findings and recommendation]
```

## Best Practices

### Reviewer Guidelines
- **Be constructive** - Focus on improving code, not criticizing author
- **Provide context** - Explain why changes are suggested
- **Suggest alternatives** - Don't just point out problems, offer solutions
- **Prioritize issues** - Distinguish between critical and minor concerns
- **Ask questions** - Clarify unclear logic or decisions

### Author Guidelines
- **Self-review first** - Review your own code before submitting
- **Provide context** - Explain complex decisions in PR descriptions
- **Address feedback** - Respond to review comments thoughtfully
- **Ask for clarification** - Don't guess what reviewers mean
- **Learn from feedback** - Use reviews as learning opportunities

## Common Pitfalls

### Review Process Issues
- **Rushed reviews** - Taking shortcuts reduces effectiveness
- **Scope creep** - Expanding review beyond intended changes
- **Perfectionism** - Blocking good code for minor style issues
- **Inconsistent standards** - Applying different criteria to different changes

### Technical Blind Spots
- **Missing security implications** - Not considering attack vectors
- **Performance assumptions** - Not validating performance claims
- **Integration impacts** - Missing how changes affect other systems
- **Future maintenance** - Not considering long-term maintainability

## Integration with Development Workflow

### With Version Control
```
Feature Development → Self-Review → Pull Request → Code Review → Merge
```

### With Testing Pipeline
```
Code Review → Test Validation → Performance Check → Security Scan → Deploy
```

### With Team Process
```
Individual Review → Team Discussion → Consensus → Implementation → Follow-up
```

## Success Metrics

### Quality Indicators
- **Bug reduction** - Fewer bugs found in production
- **Review turnaround** - Faster review completion times
- **Team knowledge** - Better understanding of codebase across team
- **Standards compliance** - More consistent code quality

### Process Metrics
- **Review coverage** - Percentage of changes reviewed
- **Issue detection rate** - Problems caught before production
- **Review participation** - Team engagement in review process
- **Knowledge transfer** - Learning and skill development

## Usage with Available Agents

This pattern can be enhanced with active agents:

```typescript
// Use general-purpose agent to apply this pattern
Task(
  subagent_type: "general-purpose",
  description: "Comprehensive code review",
  prompt: "Please follow the code-reviewer workflow pattern from 
  docs/claude/subagent/planned/code-reviewer.md to review the recent 
  changes in [specific files/features]. Focus on architecture compliance, 
  security, and test coverage."
)

// Use web-research-agent for best practices
Task(
  subagent_type: "web-research-agent", 
  description: "Research code review best practices",
  prompt: "Research current best practices for code review in Python/FastAPI 
  projects, focusing on security and performance review techniques."
)
```

---

**Status**: 📋 Workflow Pattern (Manual Process)  
**Usage**: Follow step-by-step for systematic code review  
**Integration**: Can be applied via general-purpose agent