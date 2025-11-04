# Crew Consolidation Guide

This guide explains how to use the crew consolidation system to manage different crew implementations using feature flags.

## Overview

The crew consolidation system allows you to switch between different crew implementations using feature flags without modifying the main application logic. This enables gradual migration and A/B testing of different crew configurations.

## Feature Flags

The following feature flags control which crew implementation is used:

- `ENABLE_LEGACY_CREW` - Enable legacy crew variants
- `ENABLE_CREW_MODULAR` - Enable modular crew system
- `ENABLE_CREW_REFACTORED` - Enable refactored crew system
- `ENABLE_CREW_NEW` - Enable new crew system

**Important**: Only one crew flag should be enabled at a time. If none are enabled, the canonical crew is used.

## Configuration

### Environment Variables

Set the appropriate environment variable to enable a specific crew:

```bash
# Enable the new crew system
export ENABLE_CREW_NEW=true

# Enable the modular crew system
export ENABLE_CREW_MODULAR=true

# Enable the refactored crew system
export ENABLE_CREW_REFACTORED=true

# Enable the legacy crew system
export ENABLE_LEGACY_CREW=true
```

### .env File

Add the configuration to your `.env` file:

```bash
# Crew Consolidation Flags
ENABLE_LEGACY_CREW=false
ENABLE_CREW_MODULAR=false
ENABLE_CREW_REFACTORED=false
ENABLE_CREW_NEW=false
```

## Usage

### Basic Usage

The crew consolidation system is automatically used in the main application:

```python
from ultimate_discord_intelligence_bot.crew_consolidation import get_crew

# Get the appropriate crew based on feature flags
crew = get_crew()

# Use the crew
result = crew.crew().kickoff(inputs={"url": "https://example.com"})
```

### Programmatic Usage

You can also use the crew consolidation system programmatically:

```python
from ultimate_discord_intelligence_bot.crew_consolidation import get_crew
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags

# Check which crew is enabled
flags = FeatureFlags.from_env()
if flags.is_enabled("ENABLE_CREW_NEW"):
    print("Using new crew system")
elif flags.is_enabled("ENABLE_CREW_MODULAR"):
    print("Using modular crew system")
else:
    print("Using canonical crew system")

# Get the crew
crew = get_crew()
```

## Crew Implementations

### Canonical Crew (Default)

The canonical crew is used when no specific crew flag is enabled. This is the main crew implementation in `crew.py`.

```python
# No flags enabled - uses canonical crew
crew = get_crew()  # Returns crew from crew.py
```

### New Crew System

Enable with `ENABLE_CREW_NEW=true`:

```python
# Uses crew_new.py implementation
export ENABLE_CREW_NEW=true
crew = get_crew()  # Returns crew from crew_new.py
```

### Modular Crew System

Enable with `ENABLE_CREW_MODULAR=true`:

```python
# Uses crew_modular.py implementation
export ENABLE_CREW_MODULAR=true
crew = get_crew()  # Returns crew from crew_modular.py
```

### Refactored Crew System

Enable with `ENABLE_CREW_REFACTORED=true`:

```python
# Uses crew_refactored.py implementation
export ENABLE_CREW_REFACTORED=true
crew = get_crew()  # Returns crew from crew_refactored.py
```

### Legacy Crew System

Enable with `ENABLE_LEGACY_CREW=true`:

```python
# Uses crew_new.py as legacy implementation
export ENABLE_LEGACY_CREW=true
crew = get_crew()  # Returns crew from crew_new.py
```

## Migration Examples

### Gradual Migration

1. **Start with canonical crew** (default)
2. **Enable new crew for testing**:

   ```bash
   export ENABLE_CREW_NEW=true
   ```

3. **Test and validate** the new crew
4. **Switch to new crew** when ready
5. **Disable old crew** flags

### A/B Testing

```python
import random
from ultimate_discord_intelligence_bot.crew_consolidation import get_crew

def get_crew_for_testing():
    """Get crew based on A/B testing logic."""
    if random.random() < 0.5:
        # 50% chance of using new crew
        return get_crew_with_flag("ENABLE_CREW_NEW")
    else:
        # 50% chance of using canonical crew
        return get_crew_with_flag("")  # No flag = canonical

def get_crew_with_flag(flag_name):
    """Get crew with specific flag enabled."""
    import os
    # Temporarily set flag
    if flag_name:
        os.environ[flag_name] = "true"
    try:
        return get_crew()
    finally:
        # Clean up
        if flag_name:
            os.environ.pop(flag_name, None)
```

## Testing

### Unit Tests

```python
def test_crew_consolidation():
    """Test crew consolidation with different flags."""
    from ultimate_discord_intelligence_bot.crew_consolidation import get_crew

    # Test canonical crew (no flags)
    crew = get_crew()
    assert crew is not None
    assert hasattr(crew, 'crew')

    # Test that crew can be instantiated
    crew_instance = crew.crew()
    assert crew_instance is not None

def test_feature_flag_priority():
    """Test that feature flags are respected in priority order."""
    import os
    from ultimate_discord_intelligence_bot.crew_consolidation import get_crew

    # Test ENABLE_CREW_NEW has highest priority
    os.environ["ENABLE_CREW_NEW"] = "true"
    os.environ["ENABLE_CREW_MODULAR"] = "true"

    try:
        crew = get_crew()
        # Should use new crew despite modular being enabled
        assert "new" in str(crew.__class__)
    finally:
        os.environ.pop("ENABLE_CREW_NEW", None)
        os.environ.pop("ENABLE_CREW_MODULAR", None)
```

### Integration Tests

```python
def test_crew_execution():
    """Test that crew execution works with consolidation."""
    from ultimate_discord_intelligence_bot.crew_consolidation import get_crew

    crew = get_crew()
    crew_instance = crew.crew()

    # Test that crew can be executed
    inputs = {"url": "https://example.com"}
    result = crew_instance.kickoff(inputs=inputs)

    assert result is not None
```

## Error Handling

### Missing Crew Module

If a crew module cannot be imported:

```python
try:
    crew = get_crew()
except RuntimeError as e:
    print(f"Failed to load crew: {e}")
    # Fallback to canonical crew
    from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew
    crew = UltimateDiscordIntelligenceBotCrew()
```

### Invalid Crew Class

If the crew class is not found:

```python
try:
    crew = get_crew()
except RuntimeError as e:
    print(f"Crew class not found: {e}")
    # Handle gracefully
    return None
```

## Monitoring

### Logging

The crew consolidation system logs which crew is being used:

```python
import logging

logger = logging.getLogger(__name__)

# Log crew selection
crew = get_crew()
logger.info(f"Using crew: {crew.__class__.__name__}")
```

### Metrics

Track crew usage with metrics:

```python
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

metrics = get_metrics()

# Track crew selection
crew = get_crew()
metrics.counter(
    "crew_selection_total",
    labels={"crew_type": crew.__class__.__name__}
).inc()
```

## Best Practices

1. **Use feature flags** - Don't hardcode crew selection
2. **Test thoroughly** - Validate each crew implementation
3. **Monitor performance** - Track crew execution metrics
4. **Handle errors gracefully** - Provide fallbacks for missing crews
5. **Document changes** - Keep track of crew modifications
6. **Use gradual migration** - Don't switch all at once
7. **Validate inputs** - Ensure crew inputs are compatible
8. **Clean up flags** - Remove unused feature flags

## Troubleshooting

### Common Issues

1. **Multiple flags enabled**

   ```bash
   # Check for conflicting flags
   env | grep ENABLE_CREW

   # Disable all flags to use canonical
   unset ENABLE_CREW_NEW
   unset ENABLE_CREW_MODULAR
   unset ENABLE_CREW_REFACTORED
   unset ENABLE_LEGACY_CREW
   ```

2. **Crew module not found**

   ```python
   # Check if crew module exists
   ls src/ultimate_discord_intelligence_bot/crew*.py

   # Verify import path
   python -c "from ultimate_discord_intelligence_bot.crew_new import UltimateDiscordIntelligenceBotCrew"
   ```

3. **Crew class not found**

   ```python
   # Check if crew class exists
   python -c "from ultimate_discord_intelligence_bot.crew_new import UltimateDiscordIntelligenceBotCrew; print(UltimateDiscordIntelligenceBotCrew)"
   ```

### Debug Mode

Enable debug logging to see crew selection:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show which crew is being selected
crew = get_crew()
```

## Conclusion

The crew consolidation system provides a flexible way to manage different crew implementations using feature flags. This enables gradual migration, A/B testing, and easy rollback capabilities while maintaining a consistent interface for the main application.
