# Python Performance Best Practices

This guide establishes performance best practices for the repository. Following these patterns will help maintain efficient code and prevent performance regressions.

## Table of Contents
- [List and Dictionary Operations](#list-and-dictionary-operations)
- [Exception Handling](#exception-handling)
- [Iteration Patterns](#iteration-patterns)
- [Memory Management](#memory-management)
- [Profiling and Benchmarking](#profiling-and-benchmarking)

---

## List and Dictionary Operations

### ✅ DO: Use List Comprehensions

List comprehensions are faster and more memory-efficient than manual list building.

```python
# ✅ GOOD - List comprehension
results = [transform(item) for item in items]

# ❌ BAD - Manual append loop
results = []
for item in items:
    results.append(transform(item))
```

**Performance Gain**: 20-40% faster, lower memory overhead

### ✅ DO: Use `list.extend()` for Multiple Items

When adding multiple items, use `extend()` instead of multiple `append()` calls.

```python
# ✅ GOOD - Use extend
results.extend([item.field1, item.field2] for item in items)

# ❌ BAD - Multiple appends in loop
for item in items:
    results.append(item.field1)
    results.append(item.field2)
```

### ✅ DO: Use Dictionary Comprehensions

Dictionary comprehensions are more efficient than manual dict building.

```python
# ✅ GOOD - Dict comprehension
mapping = {key: transform(value) for key, value in items}

# ❌ BAD - Manual dict building
mapping = {}
for key, value in items:
    mapping[key] = transform(value)
```

### ✅ DO: Use Appropriate Dictionary Methods

Use `.keys()` or `.values()` when you only need one part of the dictionary.

```python
# ✅ GOOD - Only iterate over values
for value in my_dict.values():
    process(value)

# ✅ GOOD - Only iterate over keys
for key in my_dict:  # or my_dict.keys()
    process(key)

# ❌ BAD - Iterate over items when only values needed
for key, value in my_dict.items():
    process(value)  # Not using key
```

**Performance Gain**: 10-20% faster iteration

---

## Exception Handling

### ✅ DO: Avoid Try-Except in Loops

Exception handling has overhead even when no exceptions occur. Avoid placing try-except blocks inside loops.

```python
# ✅ GOOD - Handle errors outside the loop
def process_items_safe(items: list) -> StepResult:
    errors = []
    for item in items:
        result = process_item(item)  # Returns StepResult
        if not result.success:
            errors.append((item, result.error))
    
    if errors:
        return StepResult.fail(
            f"Failed to process {len(errors)} items",
            metadata={"errors": errors}
        )
    return StepResult.ok()

# ❌ BAD - Try-except in every iteration
for item in items:
    try:
        process(item)
    except Exception as e:
        handle_error(e)
```

**Performance Gain**: 30-50% faster loop execution

### ✅ DO: Use StepResult Pattern

Instead of exceptions for control flow, use the `StepResult` pattern.

```python
from platform.core.step_result import StepResult

# ✅ GOOD - StepResult pattern
def process_item(item: dict) -> StepResult:
    if not item.get("id"):
        return StepResult.fail("Missing item ID")
    
    result = expensive_operation(item)
    return StepResult.ok(result=result)

# Usage
for item in items:
    result = process_item(item)
    if not result.success:
        logger.error(f"Failed: {result.error}")
        continue
    # Use result.data
```

### ✅ DO: Batch Error Collection

When processing multiple items, collect errors rather than stopping on first error.

```python
# ✅ GOOD - Collect all errors
def process_batch(items: list) -> tuple[list, list]:
    """Returns (successful_results, errors)."""
    results = []
    errors = []
    
    for item in items:
        result = process_item(item)
        if result.success:
            results.append(result.data)
        else:
            errors.append((item, result.error))
    
    return results, errors
```

---

## Iteration Patterns

### ✅ DO: Use `enumerate()` Instead of Range

Python's `enumerate()` is clearer and avoids indexing overhead.

```python
# ✅ GOOD - Use enumerate
for i, item in enumerate(items):
    print(f"{i}: {item}")

# ❌ BAD - C-style loop
for i in range(len(items)):
    print(f"{i}: {items[i]}")
```

### ✅ DO: Use `zip()` for Parallel Iteration

When iterating over multiple sequences, use `zip()`.

```python
# ✅ GOOD - Use zip
for name, value in zip(names, values):
    process(name, value)

# ❌ BAD - Index-based iteration
for i in range(len(names)):
    process(names[i], values[i])
```

### ✅ DO: Use Generator Expressions for Large Datasets

For large datasets, use generator expressions to avoid loading everything into memory.

```python
# ✅ GOOD - Generator expression for large data
total = sum(expensive_transform(item) for item in large_dataset)

# ❌ BAD - List comprehension loads everything
total = sum([expensive_transform(item) for item in large_dataset])
```

---

## Memory Management

### ✅ DO: Use Shallow Copies When Possible

Deep copies are expensive. Use shallow copies when you don't need recursive copying.

```python
# ✅ GOOD - Shallow copy
new_list = old_list.copy()
new_dict = old_dict.copy()

# ✅ GOOD - Alternative shallow copy
new_list = list(old_list)
new_dict = dict(old_dict)

# ⚠️ USE SPARINGLY - Deep copy (expensive)
import copy
new_obj = copy.deepcopy(old_obj)  # Only when necessary
```

### ✅ DO: Use `__slots__` for Classes with Many Instances

If you create many instances of a class, use `__slots__` to reduce memory usage.

```python
# ✅ GOOD - Uses __slots__ to save memory
class Point:
    __slots__ = ['x', 'y']
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# Memory savings: ~40% per instance
```

### ✅ DO: Clear Large Data Structures When Done

Explicitly clear or delete large data structures when no longer needed.

```python
# ✅ GOOD - Clear when done
large_cache = {}
# ... use cache ...
large_cache.clear()  # Free memory

# ✅ GOOD - Use context managers for cleanup
from contextlib import contextmanager

@contextmanager
def cached_data():
    cache = load_large_dataset()
    try:
        yield cache
    finally:
        cache.clear()
```

---

## Profiling and Benchmarking

### ✅ DO: Use Built-in Benchmarking Tools

Use the repository's benchmarking infrastructure.

```python
from benchmarks.performance_benchmarks import PerformanceBenchmarker

# ✅ GOOD - Benchmark operations
benchmarker = PerformanceBenchmarker()
results = await benchmarker.benchmark_operation(
    "my_operation",
    my_function,
    arg1, arg2,
    iterations=10
)
analysis = benchmarker.analyze_results(results)
```

### ✅ DO: Profile Before Optimizing

Don't guess at performance bottlenecks. Use profiling tools.

```python
# ✅ GOOD - Profile to find bottlenecks
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... code to profile ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### ✅ DO: Use Time Measurement for Quick Checks

For quick performance checks, use `time.perf_counter()`.

```python
import time

# ✅ GOOD - Simple timing
start = time.perf_counter()
result = expensive_operation()
elapsed = time.perf_counter() - start
print(f"Operation took {elapsed:.3f}s")
```

---

## Automated Performance Checking

### Using Ruff for Performance Linting

The repository uses Ruff's PERF rules to catch common performance issues.

```bash
# Check for performance issues
python3 -m ruff check src --select PERF

# Auto-fix safe issues
python3 -m ruff check src --select PERF401,PERF403,PERF102 --fix

# Use the custom performance improvement script
python3 scripts/performance_improvements.py --check
python3 scripts/performance_improvements.py --fix-dry-run
```

### Pre-commit Hook

Add performance linting to your pre-commit hooks:

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.6
  hooks:
    - id: ruff
      args: [--select, PERF, --fix]
```

---

## Anti-Patterns to Avoid

### ❌ DON'T: String Concatenation in Loops

```python
# ❌ BAD - Quadratic time complexity
result = ""
for item in items:
    result += str(item)  # Creates new string each time

# ✅ GOOD - Linear time complexity
result = "".join(str(item) for item in items)
```

### ❌ DON'T: Repeated Function Calls in Loops

```python
# ❌ BAD - Calls len() on every iteration
for i in range(len(items)):
    if i < len(items) - 1:  # len() called repeatedly
        process(items[i])

# ✅ GOOD - Cache the length
length = len(items)
for i in range(length):
    if i < length - 1:
        process(items[i])

# ✅ BETTER - Avoid indexing altogether
for i, item in enumerate(items[:-1]):
    process(item)
```

### ❌ DON'T: Unnecessary List Conversions

```python
# ❌ BAD - Converts to list unnecessarily
if len(list(items)) > 0:
    process(items)

# ✅ GOOD - Use iterator directly
if any(items):
    process(items)
```

---

## Performance Checklist

Before committing code, verify:

- [ ] No try-except blocks inside loops (unless absolutely necessary)
- [ ] List/dict comprehensions used instead of manual loops
- [ ] Appropriate dict methods (.keys(), .values()) used
- [ ] No C-style `range(len())` loops
- [ ] Large datasets use generators or streaming
- [ ] Deep copies avoided when shallow copies suffice
- [ ] Performance-critical code has been profiled
- [ ] Ruff PERF checks pass: `python3 -m ruff check --select PERF`

---

## References

- **Performance Analysis Report**: `docs/PERFORMANCE_IMPROVEMENT_RECOMMENDATIONS.md`
- **Benchmarking Suite**: `benchmarks/performance_benchmarks.py`
- **Performance Script**: `scripts/performance_improvements.py`
- **Ruff PERF Rules**: https://docs.astral.sh/ruff/rules/#perflint-perf
- **Python Performance Tips**: https://wiki.python.org/moin/PythonSpeed/PerformanceTips

---

## Questions?

For performance-related questions or discussions, see:
- Performance monitoring: `docs/performance/`
- Baseline data: `benchmarks/baselines.json`
- Current metrics: `memory_profiling_results.json`, `pipeline_profiling_results.json`
