# Configuration Migration Guide

## Overview
This guide helps migrate from the complex, multi-file configuration system to the new unified configuration loader.

## Migration Steps

### 1. Update Imports
**Before:**
```python
from ultimate_discord_intelligence_bot.settings import Settings
from ultimate_discord_intelligence_bot.config import BaseConfig, FeatureFlags
```

**After:**
```python
from ultimate_discord_intelligence_bot.config.unified import get_config
```

### 2. Update Configuration Access
**Before:**
```python
settings = Settings()
api_key = settings.openai_api_key
enable_debate = settings.feature_flags.ENABLE_DEBATE_ANALYSIS
```

**After:**
```python
config = get_config()
api_key = config.openai_api_key
enable_debate = config.enable_debate_analysis
```

### 3. Update Feature Flag Access
**Before:**
```python
if settings.feature_flags.ENABLE_DEBATE_ANALYSIS:
    # do something
```

**After:**
```python
if config.get_feature_flag("ENABLE_DEBATE_ANALYSIS"):
    # do something
```

### 4. Environment Variable Changes
Feature flags now use lowercase with underscores:
- `ENABLE_DEBATE_ANALYSIS` → `enable_debate_analysis`
- `ENABLE_FACT_CHECKING` → `enable_fact_checking`

### 5. Configuration Validation
The new system provides automatic validation:
```python
try:
    config = get_config()
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Benefits of Migration

1. **Simplified Access**: Single configuration object
2. **Clear Precedence**: Environment → .env → defaults
3. **Automatic Validation**: Catches configuration errors early
4. **Type Safety**: Full type hints and validation
5. **Better Documentation**: Clear structure and examples

## Backward Compatibility

The old `Settings` class is still available but deprecated. Update your code to use the new unified configuration system.
