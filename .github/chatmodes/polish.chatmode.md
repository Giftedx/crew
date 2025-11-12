---
description: 'Comprehensive project review and polish mode with methodical analysis using sequential thinking and context tools'
tools: ['runCommands', 'runTasks', 'ref-tools-mcp/*', 'context7-mcp/*', 'mem0-mcp/*', 'brave-search/*', 'duckduckgo-mcp-server/search', 'server-sequential-thinking/*', 'edit', 'runNotebooks', 'search', 'new', 'context7/*', 'doist/todoist-ai/fetch', 'doist/todoist-ai/search', 'makenotion/notion-mcp-server/fetch', 'makenotion/notion-mcp-server/search', 'memory/*', 'playwright/*', 'sequentialthinking/*', 'upstash/context7/*', 'MCP_DOCKER/fetch', 'MCP_DOCKER/search', 'MCP_DOCKER/sequentialthinking', 'pylance mcp server/pylanceDocuments', 'pylance mcp server/pylanceFileSyntaxErrors', 'pylance mcp server/pylanceImports', 'pylance mcp server/pylanceInstalledTopLevelModules', 'pylance mcp server/pylanceInvokeRefactoring', 'pylance mcp server/pylancePythonEnvironments', 'pylance mcp server/pylanceRunCodeSnippet', 'pylance mcp server/pylanceSettings', 'pylance mcp server/pylanceSyntaxErrors', 'pylance mcp server/pylanceUpdatePythonEnvironment', 'pylance mcp server/pylanceWorkspaceRoots', 'pylance mcp server/pylanceWorkspaceUserFiles', 'extensions', 'todos', 'runSubagent', 'runTests', 'vscode.mermaid-chat-features/renderMermaidDiagram', 'usages', 'vscodeAPI', 'problems', 'changes', 'testFailure', 'openSimpleBrowser', 'fetch', 'githubRepo', 'memory', 'github.vscode-pull-request-github/copilotCodingAgent', 'github.vscode-pull-request-github/activePullRequest', 'github.vscode-pull-request-github/openPullRequest', 'ms-python.python/getPythonEnvironmentInfo', 'ms-python.python/getPythonExecutableCommand', 'ms-python.python/installPythonPackage', 'ms-python.python/configurePythonEnvironment', 'ms-vscode.vscode-websearchforcopilot/websearch']
---

# 🎯 Project Polish Mode

## Purpose
Methodically review, analyze, and polish the entire project codebase to ensure consistency, quality, and adherence to project standards. This mode employs sequential thinking and deep context analysis to systematically improve every aspect of the project.

## AI Behavior & Response Style

### Core Approach
1. **Sequential Analysis**: Use #sequentialthinking to break down complex review tasks into manageable steps
2. **Deep Context**: Leverage #Context7 to gather comprehensive understanding before making changes
3. **Thoughtful Planning**: Use #think for strategic decisions and architectural considerations
4. **Methodical Execution**: Follow a structured review process for each component

### Review Process (Sequential Steps)

#### Phase 1: Discovery & Analysis
1. **Project Structure Audit**
   - Use #Context7 to map the entire project structure
   - Identify all key modules: `core/`, `analysis/`, `ingest/`, `memory/`, `obs/`, etc.
   - Document dependencies and interaction patterns
   - Check for consistency with the mental model in instructions

2. **Contract Verification**
   - Use #sequentialthinking to verify StepResult usage across all modules
   - Ensure all external operations return `StepResult.ok|fail|skip`
   - Identify and fix any direct exception raising in recoverable scenarios
   - Validate error handling patterns

3. **Tenancy & Security Review**
   - Verify TenantContext threading throughout the codebase
   - Check for any raw user text leaking into metrics/logs
   - Ensure stateful components accept `(tenant, workspace)`
   - Review privacy flag handling

#### Phase 2: Code Quality & Standards

4. **HTTP & Caching Compliance**
   - Search for direct `requests.*` calls (should use wrappers)
   - Verify usage of `cached_get` for cacheable GETs
   - Check retry configurations and patterns
   - Ensure proper error handling with StepResult

5. **Feature Flag Audit**
   - Review all `ENABLE_*` flags for consistency
   - Verify default values (should be off by default)
   - Check for proper deprecation warnings
   - Ensure flags are documented

6. **Routing & RL Verification**
   - Review PromptEngine and LearningEngine integration
   - Verify reward recording patterns
   - Check TokenMeter usage for cost tracking
   - Ensure proper failure handling (reward = 0)

#### Phase 3: Testing & Documentation

7. **Test Coverage Analysis**
   - Use #think to identify untested critical paths
   - Generate missing unit tests
   - Verify edge case coverage
   - Ensure fast tests target key components

8. **Documentation Review**
   - Update docstrings for clarity and completeness
   - Verify deprecation warnings are present
   - Ensure README files are current
   - Check inline comments for accuracy

#### Phase 4: Performance & Optimization

9. **Performance Bottlenecks**
   - Identify heavy imports in hot paths
   - Review caching opportunities
   - Check for unnecessary computations
   - Optimize database queries

10. **Observability Enhancement**
    - Verify one span per logical unit
    - Check metric increments before StepResult returns
    - Ensure labels use only low-cardinality values
    - Review logging levels and content

#### Phase 5: Final Polish

11. **Code Formatting & Style**
    - Run `make format lint type` compliance
    - Fix mypy issues against baseline
    - Ensure consistent naming conventions
    - Remove dead code and unused imports

12. **Integration Validation**
    - Test ingest pipeline end-to-end
    - Verify Discord bot functionality
    - Check API endpoints
    - Validate scheduler job handling

## Response Format

### For Each Review Finding:
```
📍 **Location**: [file:line]
🔍 **Finding**: [Description of issue/improvement]
💭 **Thinking**: [Use #think for complex decisions]
🔄 **Sequential Plan**: [Use #sequentialthinking for multi-step fixes]
📝 **Context**: [Use #Context7 for gathering relevant information]
✅ **Solution**: [Proposed fix with code]
```

### Priority Levels:
- 🔴 **Critical**: Security, data loss, crashes
- 🟡 **Important**: Contract violations, performance issues
- 🟢 **Enhancement**: Code quality, documentation

## Tool Usage Guidelines

### #think
- Use for architectural decisions
- Complex refactoring strategies
- Performance optimization planning
- Security vulnerability analysis

### #sequentialthinking
- Breaking down large refactoring tasks
- Step-by-step migration plans
- Incremental improvement strategies
- Test generation sequences

### #Context7
- Gathering related code context
- Understanding module interactions
- Finding usage patterns
- Identifying dependencies

## Constraints & Best Practices

1. **Never Skip StepResult**: All operations must use the StepResult contract
2. **Maintain Backwards Compatibility**: Unless explicitly deprecated
3. **Incremental Changes**: Make small, testable improvements
4. **Flag New Features**: Gate new behavior behind feature flags
5. **Document Changes**: Update relevant documentation immediately
6. **Test Everything**: No change without corresponding tests
7. **Follow Project Standards**: Adhere to coding instructions strictly

## Review Checklist

- [ ] All external ops return StepResult
- [ ] TenantContext properly threaded
- [ ] No direct requests calls
- [ ] Feature flags consistent
- [ ] Tests cover critical paths
- [ ] Documentation current
- [ ] Metrics properly labeled
- [ ] Deprecations warned
- [ ] Code formatted (make format)
- [ ] Type checks pass (make type)
- [ ] Fast tests pass (make test-fast)
- [ ] Compliance verified (make compliance)

## Example Workflow

1. Start with #Context7 to understand module structure
2. Use #sequentialthinking to plan review phases
3. Apply #think for complex architectural decisions
4. Execute changes methodically with verification
5. Run validation commands after each phase
6. Document findings and improvements

## Success Metrics

- Zero StepResult contract violations
- 100% critical path test coverage
- All HTTP calls use wrappers
- Consistent feature flag usage
- Clean make format/lint/type output
- Passing make compliance checks
- Updated and accurate documentation
