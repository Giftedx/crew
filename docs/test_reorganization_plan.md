# Test Reorganization Plan

## Current State Analysis

The test directory contains:

- **400+ test files** in a flat structure
- **Existing organization**: `fast/`, `integration/`, `e2e/` directories
- **Mixed test types**: Unit tests, integration tests, and E2E tests in the same directory
- **Performance impact**: Many integration tests slow down the fast test suite

## Target Structure

```
tests/
├── unit/                          # Fast unit tests (<1s each)
│   ├── tools/                     # Tool unit tests
│   │   ├── acquisition/           # Download and ingestion tools
│   │   ├── analysis/             # Analysis and processing tools
│   │   ├── verification/         # Fact-checking and verification tools
│   │   ├── memory/               # Memory and storage tools
│   │   └── observability/        # Monitoring and status tools
│   ├── services/                 # Service layer unit tests
│   │   ├── prompt_engine/
│   │   ├── memory_service/
│   │   └── openrouter_service/
│   ├── crew/                     # CrewAI agent and task tests
│   └── core/                     # Core functionality tests
├── integration/                  # Integration tests (1-10s each)
│   ├── pipeline/                 # Content pipeline integration
│   ├── memory/                   # Vector storage integration
│   ├── discord/                  # Discord bot integration
│   └── agents/                   # Agent coordination tests
├── e2e/                          # End-to-end tests (10s+ each)
│   ├── full_workflow/            # Complete user workflows
│   ├── performance/              # Performance and stress tests
│   └── real_world/               # Real-world scenario tests
└── fixtures/                     # Shared test fixtures
    ├── conftest.py
    ├── factories.py
    └── data/
```

## Migration Strategy

### Phase 1: Create New Structure

1. Create new directory structure
2. Move existing organized tests (`fast/`, `integration/`, `e2e/`)
3. Update import paths

### Phase 2: Categorize Remaining Tests

1. Analyze each test file to determine category
2. Move tests to appropriate directories
3. Update test markers and configuration

### Phase 3: Optimize Fast Test Suite

1. Ensure all unit tests run in <5s total
2. Mock external dependencies
3. Use in-memory databases
4. Update pytest configuration

## Test Categorization Rules

### Unit Tests (`tests/unit/`)

- **Criteria**: Fast (<1s), no external dependencies, isolated
- **Mocking**: All external services (APIs, databases, file system)
- **Examples**: Tool logic, service methods, utility functions

### Integration Tests (`tests/integration/`)

- **Criteria**: Medium speed (1-10s), limited external dependencies
- **Mocking**: External APIs, but use real internal services
- **Examples**: Service interactions, pipeline components, database operations

### E2E Tests (`tests/e2e/`)

- **Criteria**: Slow (10s+), full system testing
- **Mocking**: Minimal, use real external services where appropriate
- **Examples**: Complete workflows, performance tests, real-world scenarios

## Pytest Configuration Updates

### Test Markers

```python
# pytest.ini or pyproject.toml
markers =
    unit: Fast unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take >10s
    fast: Tests that run in <5s total
```

### Test Discovery

```python
# conftest.py
def pytest_configure(config):
    # Auto-categorize tests based on directory
    for item in config.items:
        if "tests/unit/" in str(item.fspath):
            item.add_marker("unit")
        elif "tests/integration/" in str(item.fspath):
            item.add_marker("integration")
        elif "tests/e2e/" in str(item.fspath):
            item.add_marker("e2e")
```

## Fast Test Suite Optimization

### Target Performance

- **Total runtime**: <5 seconds
- **Individual tests**: <1 second each
- **Coverage**: 95% of unit tests in fast suite

### Optimization Techniques

1. **Mocking Strategy**:

   ```python
   @pytest.fixture
   def mock_openai():
       with patch('openai.OpenAI') as mock:
           mock.return_value.chat.completions.create.return_value = MockResponse()
           yield mock
   ```

2. **In-Memory Databases**:

   ```python
   @pytest.fixture
   def in_memory_qdrant():
       # Use in-memory Qdrant for tests
       pass
   ```

3. **Test Data Fixtures**:

   ```python
   @pytest.fixture
   def sample_content():
       return {
           "text": "Sample content for testing",
           "metadata": {"source": "test"}
       }
   ```

## Implementation Steps

### Step 1: Create Directory Structure

```bash
mkdir -p tests/{unit/{tools/{acquisition,analysis,verification,memory,observability},services,crew,core},integration/{pipeline,memory,discord,agents},e2e/{full_workflow,performance,real_world},fixtures}
```

### Step 2: Move Existing Organized Tests

```bash
# Move existing organized tests
mv tests/fast/* tests/unit/
mv tests/integration/* tests/integration/
mv tests/e2e/* tests/e2e/
```

### Step 3: Categorize Remaining Tests

- Analyze each test file
- Determine appropriate category
- Move to correct directory
- Update imports

### Step 4: Update Configuration

- Update `pytest.ini` or `pyproject.toml`
- Update `conftest.py`
- Update CI configuration

### Step 5: Optimize Fast Suite

- Add comprehensive mocking
- Use in-memory databases
- Remove slow dependencies
- Validate <5s runtime

## Benefits

1. **Clear Test Organization**: Easy to find and maintain tests
2. **Fast CI Pipeline**: Unit tests run quickly for rapid feedback
3. **Selective Test Execution**: Run only relevant tests for specific changes
4. **Better Test Coverage**: Clear separation of test types
5. **Improved Maintainability**: Easier to understand and modify tests

## Success Metrics

- **Fast suite runtime**: <5 seconds
- **Test organization**: Clear directory structure
- **Test coverage**: Maintained or improved
- **CI performance**: Faster feedback loops
- **Developer experience**: Easier test discovery and execution
