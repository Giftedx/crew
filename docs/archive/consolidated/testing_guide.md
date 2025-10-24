# Testing Guide for Ultimate Discord Intelligence Bot

## Overview

This guide provides comprehensive testing patterns, best practices, and guidelines for testing the Ultimate Discord Intelligence Bot codebase.

## Testing Philosophy

- **Test-Driven Development**: Write tests before or alongside implementation
- **Comprehensive Coverage**: Test success paths, error paths, and edge cases
- **Isolation**: Each test should be independent and not rely on external state
- **Fast Feedback**: Tests should run quickly and provide immediate feedback
- **Maintainable**: Tests should be easy to understand, modify, and extend

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests for individual components
│   ├── tools/                  # Tool tests
│   ├── services/               # Service tests
│   ├── agents/                 # Agent tests
│   └── utils/                  # Utility tests
├── integration/                # Integration tests
│   ├── pipeline/               # End-to-end pipeline tests
│   ├── api/                    # API integration tests
│   └── external/               # External service integration tests
└── e2e/                        # End-to-end tests
    ├── discord/                # Discord bot tests
    └── workflows/              # Complete workflow tests
```

## Testing Patterns

### 1. Tool Testing Pattern

Tools should be tested with:

- Input validation
- Success scenarios
- Error handling
- Tenant isolation
- StepResult compliance

```python
import pytest
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.template_tool import TemplateTool

class TestTemplateTool:
    def setup_method(self) -> None:
        self.tool = TemplateTool()
        self.tenant = "test_tenant"
        self.workspace = "test_workspace"

    def test_successful_execution(self) -> None:
        """Test successful tool execution."""
        result = self.tool.run("test input", self.tenant, self.workspace)
        
        assert result.success
        assert result.data is not None
        assert "processed_text" in result.data

    def test_input_validation(self) -> None:
        """Test input validation."""
        result = self.tool.run("", self.tenant, self.workspace)
        
        assert not result.success
        assert "must be a non-empty string" in result.error

    def test_tenant_isolation(self) -> None:
        """Test tenant isolation."""
        result1 = self.tool.run("test", "tenant1", self.workspace)
        result2 = self.tool.run("test", "tenant2", self.workspace)
        
        assert result1.success
        assert result2.success
        assert result1.data["tenant_specific_result"] != result2.data["tenant_specific_result"]
```

### 2. Service Testing Pattern

Services should be tested with:

- Dependency injection
- Error handling
- Caching behavior
- Configuration validation

```python
import pytest
from unittest.mock import Mock, patch
from ultimate_discord_intelligence_bot.services.memory_service import MemoryService

class TestMemoryService:
    def setup_method(self) -> None:
        self.mock_qdrant = Mock()
        self.service = MemoryService(qdrant_client=self.mock_qdrant)

    def test_store_content_success(self) -> None:
        """Test successful content storage."""
        result = self.service.store_content("test content", "tenant", "workspace")
        
        assert result.success
        assert result.data["stored"] is True

    def test_store_content_failure(self) -> None:
        """Test content storage failure."""
        self.mock_qdrant.upsert.side_effect = Exception("Database error")
        
        result = self.service.store_content("test content", "tenant", "workspace")
        
        assert not result.success
        assert "Database error" in result.error
```

### 3. Agent Testing Pattern

Agents should be tested with:

- Tool assignment
- Configuration validation
- Execution scenarios
- Error handling

```python
import pytest
from unittest.mock import Mock
from ultimate_discord_intelligence_bot.config.agent_factory import AgentFactory

class TestAgentFactory:
    def setup_method(self) -> None:
        self.factory = AgentFactory()

    @patch('ultimate_discord_intelligence_bot.config.agent_factory.Agent')
    def test_create_agent_success(self, mock_agent_class: Mock) -> None:
        """Test successful agent creation."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        agent = self.factory.create_agent("mission_orchestrator")
        
        assert agent is not None
        mock_agent_class.assert_called_once()
```

## Test Fixtures

### Common Fixtures

The `conftest.py` file provides common fixtures:

- `temp_dir`: Temporary directory for testing
- `sample_url`: Sample URL for testing
- `sample_content`: Sample content for testing
- `tenant_context`: Sample tenant and workspace
- `mock_metrics`: Mock metrics object
- `mock_step_result`: Mock StepResult
- `mock_tool`: Mock tool
- `mock_agent`: Mock agent
- `mock_crew`: Mock crew

### Custom Fixtures

Create custom fixtures for specific test modules:

```python
@pytest.fixture
def sample_video_data() -> dict[str, Any]:
    """Sample video data for testing."""
    return {
        "url": "https://youtube.com/watch?v=test",
        "title": "Test Video",
        "duration": 300,
        "transcript": "Test transcript content"
    }
```

## Mocking Patterns

### External Services

Mock external services to avoid network calls and API dependencies:

```python
@patch('ultimate_discord_intelligence_bot.services.openai.OpenAI')
def test_openai_integration(mock_openai: Mock) -> None:
    """Test OpenAI integration with mocked client."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    
    # Configure mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Mock response"
    mock_client.chat.completions.create.return_value = mock_response
    
    # Test your code
    result = your_function()
    assert result.success
```

### Database Operations

Mock database operations for unit tests:

```python
@patch('ultimate_discord_intelligence_bot.services.memory_service.QdrantClient')
def test_memory_service(mock_qdrant_class: Mock) -> None:
    """Test memory service with mocked database."""
    mock_client = Mock()
    mock_qdrant_class.return_value = mock_client
    
    # Configure mock responses
    mock_client.search.return_value = []
    mock_client.upsert.return_value = Mock()
    
    # Test your code
    service = MemoryService()
    result = service.search_content("query", "tenant", "workspace")
    assert result.success
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_long_running_operation() -> None:
    """Test that takes a long time to run."""
    pass

@pytest.mark.integration
def test_api_integration() -> None:
    """Test API integration."""
    pass

@pytest.mark.requires_network
def test_download_functionality() -> None:
    """Test that requires network access."""
    pass

@pytest.mark.requires_api_key
def test_openai_integration() -> None:
    """Test that requires API key."""
    pass
```

Run specific test categories:

```bash
# Run only unit tests
pytest -m unit

# Run tests excluding slow ones
pytest -m "not slow"

# Run integration tests
pytest -m integration
```

## Assertion Patterns

### StepResult Assertions

Use the TestUtils class for consistent StepResult assertions:

```python
def test_tool_execution(test_utils: TestUtils) -> None:
    """Test tool execution with proper assertions."""
    result = tool.run("input", "tenant", "workspace")
    
    # Assert success with expected data keys
    test_utils.assert_step_result_success(result, ["processed_text", "word_count"])
    
    # Or assert failure with expected error
    test_utils.assert_step_result_failure(result, "Invalid input")
```

### Data Validation

Validate data structure and content:

```python
def test_data_structure(result: StepResult) -> None:
    """Test data structure validation."""
    assert result.success
    assert isinstance(result.data, dict)
    assert "processed_text" in result.data
    assert isinstance(result.data["word_count"], int)
    assert result.data["word_count"] > 0
```

## Performance Testing

### Timing Tests

Test execution time for performance-critical operations:

```python
import time

def test_execution_time() -> None:
    """Test that operation completes within time limit."""
    start_time = time.time()
    result = tool.run("input", "tenant", "workspace")
    execution_time = time.time() - start_time
    
    assert result.success
    assert execution_time < 5.0  # Should complete within 5 seconds
```

### Memory Usage Tests

Test memory usage for memory-intensive operations:

```python
import psutil
import os

def test_memory_usage() -> None:
    """Test memory usage during operation."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    result = tool.run("input", "tenant", "workspace")
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert result.success
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
```

## Error Testing

### Exception Handling

Test that tools handle exceptions gracefully:

```python
def test_exception_handling() -> None:
    """Test exception handling."""
    with patch.object(tool, '_process_data', side_effect=Exception("Test error")):
        result = tool.run("input", "tenant", "workspace")
        
        assert not result.success
        assert "Test error" in result.error
```

### Network Error Simulation

Test network error handling:

```python
def test_network_error() -> None:
    """Test network error handling."""
    with patch('requests.get', side_effect=ConnectionError("Network error")):
        result = tool.run("input", "tenant", "workspace")
        
        assert not result.success
        assert "Network error" in result.error
```

## Test Data Management

### Test Data Files

Store test data in dedicated files:

```
tests/data/
├── sample_transcripts.json
├── sample_analysis_results.json
├── sample_videos.json
└── expected_outputs.json
```

### Dynamic Test Data

Generate test data dynamically:

```python
@pytest.fixture
def random_content() -> str:
    """Generate random content for testing."""
    import random
    import string
    
    words = ["test", "content", "analysis", "sentiment", "political"]
    return " ".join(random.choices(words, k=10))
```

## Continuous Integration

### GitHub Actions

Configure CI to run tests automatically:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
```

### Test Coverage

Monitor test coverage:

```bash
# Run tests with coverage
pytest --cov=src/ultimate_discord_intelligence_bot

# Generate coverage report
pytest --cov=src/ultimate_discord_intelligence_bot --cov-report=html

# Check coverage threshold
pytest --cov=src/ultimate_discord_intelligence_bot --cov-fail-under=80
```

## Best Practices

### 1. Test Naming

Use descriptive test names that explain what is being tested:

```python
def test_should_return_success_when_valid_input_provided() -> None:
    """Test that tool returns success with valid input."""
    pass

def test_should_return_error_when_invalid_tenant_provided() -> None:
    """Test that tool returns error with invalid tenant."""
    pass
```

### 2. Test Organization

Organize tests by functionality and use classes for related tests:

```python
class TestContentAnalysis:
    """Test content analysis functionality."""
    
    def test_political_topic_detection(self) -> None:
        """Test political topic detection."""
        pass
    
    def test_sentiment_analysis(self) -> None:
        """Test sentiment analysis."""
        pass
```

### 3. Test Independence

Ensure tests are independent and can run in any order:

```python
def setup_method(self) -> None:
    """Set up fresh state for each test."""
    self.tool = Tool()
    self.tool.reset()  # Reset tool state
```

### 4. Test Documentation

Document complex tests and edge cases:

```python
def test_edge_case_empty_input() -> None:
    """Test edge case: empty input string.
    
    This test verifies that the tool handles empty input strings
    gracefully by returning a validation error rather than crashing.
    """
    result = tool.run("", "tenant", "workspace")
    assert not result.success
    assert "empty" in result.error.lower()
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/tools/test_template_tool.py

# Run specific test method
pytest tests/unit/tools/test_template_tool.py::TestTemplateTool::test_successful_execution

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### Advanced Test Execution

```bash
# Run tests in parallel
pytest -n auto

# Run tests with coverage
pytest --cov=src/ultimate_discord_intelligence_bot

# Run tests matching pattern
pytest -k "test_tool"

# Run tests excluding slow ones
pytest -m "not slow"
```

## Debugging Tests

### Debugging Failed Tests

```bash
# Run with debug output
pytest --tb=short

# Drop into debugger on failure
pytest --pdb

# Run with print statements visible
pytest -s
```

### Test Debugging Tools

```python
def test_debug_example() -> None:
    """Example of debugging test failures."""
    result = tool.run("input", "tenant", "workspace")
    
    # Print debug information
    print(f"Result: {result}")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Data: {result.data}")
    
    assert result.success
```

This testing guide provides a comprehensive foundation for testing the Ultimate Discord Intelligence Bot codebase. Follow these patterns and practices to ensure robust, maintainable, and reliable tests.
