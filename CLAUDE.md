# Claude LLM Instructions for Snippets Automation Project

This document contains step-by-step instructions and best practices for Claude to follow when working on the Alfred Snippets Automation project.

## Project Context

**Goal**: Build an intelligent automation system for creating and managing Alfred snippets using Anthropic's Claude API for metadata generation and categorization.

**Key Requirements**:
- Batch creation from JSON files
- Ad hoc creation via Raycast integration
- AI-powered categorization and metadata generation
- Robust error handling and user prompts
- Alfred compatibility and folder structure management

## Development Workflow

### 1. Issue-Driven Development

**Before any implementation**:
- Break down features into atomic GitHub issues
- Each issue should have: title, description, acceptance criteria, dependencies
- Use priority labels (P0, P1, P2) for implementation order
- Reference issue numbers in all commits and PRs

**Issue Creation Guidelines**:
- P0: Core functionality (snippet creation, AI categorization, file operations)
- P1: User experience (error handling, prompts, notifications)
- P2: Enhancement features (advanced categorization, templates)

### 2. Code Organization

**Module Structure**:
```
snippets-automation/
├── src/
│   ├── __init__.py
│   ├── snippet_manager.py      # Core business logic
│   ├── claude_api.py           # Anthropic API integration
│   ├── alfred_utils.py         # Alfred-specific operations
│   └── utils.py               # General utilities
├── scripts/
│   ├── batch_create_alfred_snippets.py
│   └── add_alfred_snippet.py
├── tests/
├── examples/
└── docs/
```

**Key Principles**:
- Separate concerns: API calls, file operations, business logic
- Use dependency injection for testability
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Handle errors gracefully with specific exception types

### 3. Alfred Integration Requirements

**Snippet File Format**:
```json
{
  "alfredsnippet": {
    "snippet": "content here",
    "name": "Display Name",
    "keyword": "trigger_keyword",
    "uid": "UUID4-format-unique-id"
  }
}
```

**Folder Structure**:
- Collections = folders in Alfred snippets directory
- Each snippet = individual JSON file in collection folder
- Filename format: `{keyword}_{uid}.json`

**Critical Operations**:
- Check for duplicate keywords before creation
- Validate Alfred snippets folder exists and is writable
- Create collection folders if they don't exist
- Generate proper UUIDs for snippet identification

### 4. AI Integration Patterns

**Claude API Usage**:
- Model: `claude-3-5-haiku-latest` for speed and cost efficiency
- Purpose: Content analysis and metadata generation
- Fallback: Manual user input if AI categorization fails

**Prompt Engineering**:
```python
CATEGORIZATION_PROMPT = """
Analyze this snippet content and suggest metadata:

Content: {snippet_content}

Existing collections: {existing_collections}

Provide JSON response with:
- collection: existing or new collection name (Title Case)
- name: descriptive name (Title Case, start with topic)
- keyword: trigger keyword (lowercase, topic_function format)
- description: brief description (1-2 sentences)
- confidence: high/medium/low

Rules:
- Use existing collections when appropriate
- Follow naming conventions strictly
- Be concise but descriptive
"""
```

**Error Handling**:
- Retry logic for API failures (3 attempts with backoff)
- Validate JSON responses from Claude
- Graceful degradation to manual input
- Never expose API keys in logs or error messages

### 5. User Experience Guidelines

**Notification Requirements**:
- Use macOS native notifications via `osascript`
- Success: "Snippet 'Name' added to Collection"
- Failure: "Failed to create snippet: [reason]"
- No clipboard modification (as requested)

**Manual Prompts**:
- List existing collections when AI fails to categorize
- Allow creation of new collections
- Validate user inputs before proceeding
- Provide clear instructions and examples

**Input Handling**:
- Clipboard content takes precedence
- Parameter input as fallback
- Validate content is not empty
- Handle special characters and encoding properly

### 6. Testing Strategy

**Unit Tests**:
- Mock Anthropic API responses
- Test snippet file creation and validation
- Test duplicate detection logic
- Test collection folder operations

**Integration Tests**:
- End-to-end snippet creation workflow
- Alfred folder structure validation
- Error handling scenarios
- User prompt flows

**Test Data**:
- Sample snippets for various categories
- Edge cases (empty content, special characters)
- Invalid Alfred folder scenarios
- API failure simulations

### 7. Configuration Management

**Environment Variables**:
```bash
ANTHROPIC_API_KEY=sk-ant-...
ALFRED_SNIPPETS_PATH=/path/to/alfred/snippets
LOG_LEVEL=INFO
```

**Constants**:
- API retry attempts and delays
- Supported snippet content types
- Naming convention patterns
- Default collection names

### 8. Error Handling Patterns

**Exception Hierarchy**:
```python
class SnippetError(Exception): pass
class AlfredFolderError(SnippetError): pass
class APIError(SnippetError): pass
class DuplicateSnippetError(SnippetError): pass
```

**Recovery Strategies**:
- API failures → retry with backoff → manual input
- Duplicate keywords → prompt to overwrite or skip
- Invalid folders → attempt creation → fail gracefully
- Missing dependencies → clear error messages

### 9. Implementation Priority

**Phase 1 (P0 Issues)**:
1. Core snippet creation logic
2. Alfred file format handling
3. Basic AI categorization
4. Folder structure management

**Phase 2 (P1 Issues)**:
1. Robust error handling
2. User prompts and notifications
3. Duplicate detection and handling
4. Comprehensive testing

**Phase 3 (P2 Issues)**:
1. Advanced categorization features
2. Performance optimizations
3. Additional input sources
4. Documentation and examples

### 10. Code Review Checklist

**Before committing**:
- [ ] Code follows PEP 8 style guidelines
- [ ] All functions have proper docstrings
- [ ] Error handling covers edge cases
- [ ] No hardcoded paths or credentials
- [ ] Tests pass and cover new functionality
- [ ] Documentation updated if needed
- [ ] Git commit references relevant issue

**Security Review**:
- [ ] API keys read from environment only
- [ ] No sensitive data in logs
- [ ] Input validation for user data
- [ ] File permissions properly handled

## Troubleshooting Common Issues

**Alfred Integration**:
- Ensure Alfred snippets folder path is correct
- Check folder permissions for write access
- Verify snippet JSON format matches Alfred requirements
- Test snippet import in Alfred after creation

**API Issues**:
- Validate API key format and permissions
- Check network connectivity
- Monitor rate limits and quotas
- Implement proper retry logic

**File Operations**:
- Handle filesystem encoding issues
- Check available disk space
- Manage file locking on network drives
- Validate JSON structure before writing

Remember: Always reference GitHub issues in commits, follow the established patterns, and prioritize user experience over feature complexity.