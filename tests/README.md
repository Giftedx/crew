# Discord AI Test Suite

This directory contains comprehensive tests for the Discord AI integration components.

## Test Structure

```
tests/
├── README.md                           # This file
├── conftest.py                         # Test configuration and fixtures
├── test_discord_ai_integration.py      # Main integration test suite
├── unit/                               # Unit tests
│   ├── test_message_evaluator.py       # Message evaluation tests
│   ├── test_personality_manager.py     # Personality management tests
│   └── test_reward_computer.py         # Reward computation tests
├── integration/                        # Integration tests
│   └── test_conversational_pipeline.py # Pipeline integration tests
└── run_discord_ai_tests.py             # Test runner script
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **Message Evaluator Tests** (`test_message_evaluator.py`):
  - Message context building
  - Direct mention detection
  - LLM-based evaluation
  - Confidence threshold filtering
  - Error handling

- **Personality Manager Tests** (`test_personality_manager.py`):
  - Personality traits creation and manipulation
  - Personality adaptation algorithms
  - Memory integration
  - RL recommendation integration
  - Consistency validation

- **Reward Computer Tests** (`test_reward_computer.py`):
  - Reward signal computation
  - Engagement reward calculation
  - Reaction analysis
  - Temporal pattern analysis
  - Content quality assessment

### Integration Tests

Integration tests verify that components work together correctly:

- **Conversational Pipeline Tests** (`test_conversational_pipeline.py`):
  - End-to-end message processing
  - User opt-in/opt-out workflow
  - Personality adaptation integration
  - Memory retrieval and storage
  - Error handling and recovery
  - Concurrent message processing

### Main Integration Test Suite

The main test suite (`test_discord_ai_integration.py`) provides comprehensive coverage of all Discord AI functionality:

- Message evaluation system
- Opt-in management
- Personality management
- Reward computation
- Conversational pipeline
- MCP integration
- Performance testing
- Configuration testing

## Running Tests

### Using the Test Runner

The test runner script provides easy access to different test categories:

```bash
# Run all tests
python run_discord_ai_tests.py all

# Run unit tests only
python run_discord_ai_tests.py unit

# Run integration tests only
python run_discord_ai_tests.py integration

# Run Discord AI specific tests
python run_discord_ai_tests.py discord-ai

# Run tests with coverage
python run_discord_ai_tests.py coverage

# Run performance tests
python run_discord_ai_tests.py performance

# Run specific test file
python run_discord_ai_tests.py specific --test-path tests/unit/test_message_evaluator.py

# Run code linting
python run_discord_ai_tests.py lint

# Run code formatting
python run_discord_ai_tests.py format

# Run type checking
python run_discord_ai_tests.py type
```

### Using pytest Directly

You can also run tests directly with pytest:

```bash
# Run all tests
pytest tests/ -v

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_message_evaluator.py -v

# Run tests with coverage
pytest tests/ --cov=performance_optimization.src.discord --cov-report=html

# Run tests with specific markers
pytest tests/ -m "not integration" -v  # Skip integration tests
pytest tests/ -m performance -v        # Run only performance tests
```

## Test Fixtures

The `conftest.py` file provides common fixtures used across tests:

- **Database Fixtures**: Temporary SQLite databases for testing
- **Mock Services**: Mocked routing managers, prompt engines, memory services
- **Sample Data**: Sample Discord messages, personality traits, interaction metrics
- **Test Utilities**: Performance timers, error simulators, test data factories

## Test Configuration

### Environment Variables

Tests automatically set up the following environment variables:

```bash
ENABLE_DISCORD_AI_RESPONSES=true
ENABLE_DISCORD_PERSONALITY_RL=true
ENABLE_DISCORD_MESSAGE_EVALUATION=true
ENABLE_DISCORD_OPT_IN_SYSTEM=true
ENABLE_DISCORD_CONVERSATIONAL_PIPELINE=true
ENABLE_PERSONALITY_ADAPTATION=true
ENABLE_REWARD_COMPUTATION=true
ENABLE_PERSONALITY_MEMORY=true
ENABLE_MCP_MEMORY=true
ENABLE_MCP_KG=true
ENABLE_MCP_CREWAI=true
ENABLE_MCP_ROUTER=true
ENABLE_MCP_CREATOR_INTELLIGENCE=true
ENABLE_MCP_OBS=true
ENABLE_MCP_INGEST=true
ENABLE_MCP_HTTP=true
ENABLE_MCP_A2A=true
```

### Test Markers

Tests are marked with specific categories:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.asyncio`: Async tests

## Mocking Strategy

Tests use comprehensive mocking to isolate components:

- **External Services**: All external API calls are mocked
- **Database Operations**: SQLite operations use temporary databases
- **Memory Service**: Vector database operations are mocked
- **Learning Engine**: RL operations are mocked
- **Routing Manager**: Model selection is mocked

## Test Data

Tests use realistic test data:

- **Discord Messages**: Realistic message structures with various content types
- **Personality Traits**: Valid personality trait combinations
- **Interaction Metrics**: Various engagement levels (high, medium, low)
- **Memory Contexts**: Relevant memory retrieval scenarios

## Performance Testing

Performance tests measure:

- Message evaluation latency
- Memory retrieval performance
- Personality adaptation speed
- Concurrent processing capabilities
- Memory usage patterns

## Error Testing

Tests verify error handling for:

- Service unavailability
- Network timeouts
- Invalid input data
- Database connection failures
- Memory retrieval errors
- RL computation failures

## Coverage Goals

The test suite aims for:

- **Unit Tests**: 90%+ code coverage
- **Integration Tests**: 80%+ integration coverage
- **Error Paths**: 100% error handling coverage
- **Performance**: All critical paths tested

## Continuous Integration

Tests are designed to run in CI environments:

- No external dependencies
- Deterministic results
- Fast execution
- Comprehensive error reporting
- Coverage reporting

## Debugging Tests

### Running Individual Tests

```bash
# Run specific test function
pytest tests/unit/test_message_evaluator.py::TestMessageEvaluator::test_message_evaluation_success -v

# Run with debugging output
pytest tests/unit/test_message_evaluator.py -v -s --tb=long

# Run with pdb debugging
pytest tests/unit/test_message_evaluator.py --pdb
```

### Test Output

Tests provide detailed output including:

- Test execution time
- Memory usage
- Error details
- Coverage information
- Performance metrics

## Adding New Tests

When adding new tests:

1. **Follow Naming Conventions**: Use descriptive test names
2. **Use Fixtures**: Leverage existing fixtures for common setup
3. **Mock External Dependencies**: Don't rely on external services
4. **Test Error Paths**: Include error handling tests
5. **Add Performance Tests**: For performance-critical code
6. **Update Documentation**: Keep this README updated

## Test Maintenance

Regular test maintenance includes:

- Updating mocks for API changes
- Refreshing test data
- Updating coverage goals
- Performance baseline updates
- Documentation updates

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `performance_optimization/src` is in Python path
2. **Mock Failures**: Check mock configurations in `conftest.py`
3. **Database Issues**: Verify temporary database cleanup
4. **Async Issues**: Ensure proper async/await usage in tests

### Getting Help

- Check test output for detailed error messages
- Use `pytest --tb=long` for full tracebacks
- Enable debug logging with `-v` flag
- Check mock configurations in fixtures
