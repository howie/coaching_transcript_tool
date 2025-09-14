# Web Research Agent ✅ ACTIVE

**Status**: Available - Can be invoked via Task tool  
**Agent Type**: `web-research-agent`

## Overview

The web-research-agent specializes in finding and analyzing information from web sources, official documentation, and online resources. It's designed for research tasks that require external information gathering.

## Capabilities

- **Web search and analysis** - Search for current information online
- **Documentation research** - Access official docs and technical resources
- **Information synthesis** - Combine multiple sources into coherent answers
- **Verification tasks** - Check facts against authoritative sources
- **Technology research** - Investigate new libraries, frameworks, or tools

## When to Use

### ✅ Ideal Scenarios
- **Uncertain questions** - When you need verification of information
- **API features** - Checking latest capabilities of external services
- **Documentation lookup** - Finding official guides or references
- **Technology evaluation** - Researching new tools or frameworks
- **Best practices** - Finding current recommendations for implementation
- **Compatibility research** - Checking version compatibility or requirements

### ✅ Examples from CLAUDE.md
The system specifically mentions using this agent for Claude Code documentation:
> "When the user directly asks about Claude Code..., use the WebFetch tool to gather information to answer the question from Claude Code docs."

## Usage Pattern

```typescript
// Invoke via Task tool
Task(
  subagent_type: "web-research-agent",
  description: "Research specific topic",
  prompt: "Research [topic] and provide [specific information needed]. 
  Focus on [authoritative sources/official documentation/current information]."
)
```

## Research Capabilities

### Official Documentation
- **API documentation** - Latest features and capabilities
- **Framework guides** - Implementation patterns and best practices
- **Platform requirements** - Deployment and compatibility info
- **Security guidelines** - Current security recommendations

### Technology Evaluation
- **Feature comparison** - Compare different tools or libraries
- **Compatibility matrix** - Version and platform compatibility
- **Performance benchmarks** - Speed and efficiency data
- **Community adoption** - Usage trends and community support

### Current Information
- **Latest releases** - Recent updates and new features
- **Breaking changes** - Compatibility issues in new versions
- **Security advisories** - Recent vulnerabilities or patches
- **Industry trends** - Current best practices and patterns

## Examples

### API Feature Verification
```
Description: "Check FastAPI OpenAPI capabilities"
Prompt: "Does the latest version of FastAPI support automatic OpenAPI schema 
generation for custom response models? Research the official FastAPI 
documentation and provide current capabilities with examples."
```

### Platform Requirements
```
Description: "Research Cloudflare Workers deployment"
Prompt: "What are the exact memory requirements for deploying Next.js apps 
on Cloudflare Workers? Check Cloudflare's official documentation for the 
most up-to-date deployment requirements."
```

### Claude Code Documentation
```
Description: "Claude Code feature research"  
Prompt: "Research whether Claude Code supports custom hooks and how to 
implement them. Check the official Claude Code documentation at 
docs.anthropic.com for the latest information."
```

### Technology Comparison
```
Description: "Compare STT providers"
Prompt: "Compare Google Speech-to-Text v2 and AssemblyAI for Chinese language 
transcription accuracy and features. Focus on official documentation and 
recent benchmarks."
```

## Tool Usage

Primary tools for this agent:
- **WebSearch** - General web search capabilities
- **WebFetch** - Retrieve specific pages and documentation
- **Read** - Access local documentation files for context
- **Write** - Document research findings

## Research Process

### 1. Query Analysis
- Understand the specific information needed
- Identify authoritative sources to check
- Plan search strategy for comprehensive coverage

### 2. Information Gathering
- Search official documentation first
- Use multiple sources for verification
- Focus on recent and authoritative information

### 3. Synthesis and Verification
- Cross-reference information from multiple sources
- Identify conflicting information and resolve
- Verify currency of information (check dates)

### 4. Structured Response
- Provide clear, actionable information
- Include source citations and links
- Highlight key findings and recommendations

## Quality Standards

### Source Prioritization
1. **Official documentation** - Primary authoritative sources
2. **Official blogs/announcements** - Recent updates from vendors
3. **Reputable technical sites** - Stack Overflow, MDN, etc.
4. **Community resources** - Well-maintained community docs

### Information Verification
- **Cross-reference sources** - Verify consistency across sources
- **Check publication dates** - Ensure information is current
- **Verify official status** - Distinguish official vs community content
- **Test claims** - Validate technical claims where possible

## Best Practices

### Query Formulation
- **Be specific** - Narrow down exactly what information is needed
- **Include context** - Provide relevant background for better targeting
- **Specify sources** - Indicate preferred or required source types
- **Set scope** - Define how comprehensive the research should be

### Result Interpretation
- **Distinguish fact from opinion** - Separate objective info from subjective
- **Note limitations** - Identify gaps or uncertainties in information
- **Provide alternatives** - Include multiple options when available
- **Include caveats** - Note version dependencies or restrictions

## Integration Patterns

### With Development Workflow
```
Question/Uncertainty → web-research-agent → Informed Decision → Implementation
```

### With Documentation
```
Documentation Gap → web-research-agent → Updated Documentation → Team Knowledge
```

### With Problem Solving
```
Problem → web-research-agent (solutions) → Evaluation → Implementation
```

## Limitations

- **Real-time constraints** - Information may not be completely current
- **Access limitations** - Some sites may be blocked or require authentication
- **Context gaps** - May lack project-specific context
- **Information overload** - May need filtering for most relevant results

## Related Agents

- **[general-purpose](./general-purpose.md)** - For complex tasks that include research components
- **[post-commit-updater](./post-commit-updater.md)** - May need research for documentation updates

---

**Agent Type**: `web-research-agent`  
**Availability**: ✅ Active  
**Tool Access**: WebSearch, WebFetch, Read, Write  
**Primary Use**: Research and information gathering from external sources