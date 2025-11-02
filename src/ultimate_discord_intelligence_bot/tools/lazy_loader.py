"""Lazy Tool Loading System.

This module provides a comprehensive lazy loading system for tools to reduce
startup time and memory usage by only loading tools when they are actually needed.
"""
from __future__ import annotations
import time
from functools import lru_cache
from typing import Any
from ultimate_discord_intelligence_bot.tools._base import BaseTool

class LazyToolLoader:
    """Lazy tool loader that defers tool instantiation until needed."""

    def __init__(self):
        """Initialize the lazy tool loader."""
        self._tool_cache: dict[str, BaseTool] = {}
        self._loading_times: dict[str, float] = {}
        self._import_errors: dict[str, Exception] = {}
        self._class_cache: dict[str, type[BaseTool]] = {}

    def get_tool(self, tool_name: str, *args, **kwargs) -> BaseTool:
        """Get a tool instance, loading it lazily if not already cached."""
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]
        start_time = time.time()
        try:
            tool_class = self._import_tool_class(tool_name)
            tool_instance = tool_class(*args, **kwargs)
            self._tool_cache[tool_name] = tool_instance
            self._loading_times[tool_name] = time.time() - start_time
            return tool_instance
        except Exception as e:
            self._import_errors[tool_name] = e
            return self._create_stub_tool(tool_name, e)

    def _import_tool_class(self, tool_name: str) -> type[BaseTool]:
        """Import a tool class with caching."""
        if tool_name in self._class_cache:
            return self._class_cache[tool_name]
        try:
            from ultimate_discord_intelligence_bot.tools import __getattr__
            cls = __getattr__(tool_name)
            self._class_cache[tool_name] = cls
            return cls
        except Exception as e:
            raise ImportError(f'Failed to import {tool_name}: {e}') from e

    def _create_stub_tool(self, tool_name: str, error: Exception) -> BaseTool:
        """Create a stub tool that fails gracefully when unavailable."""
        from platform.core.step_result import StepResult

        class StubTool(BaseTool):

            def __init__(self, name: str, error: Exception):
                super().__init__()
                self.name = name
                self.description = f'{name} unavailable: {type(error).__name__}'
                self._error = error

            def _run(self, *args, **kwargs) -> StepResult:
                return StepResult.fail(error=f'{self.name} is unavailable', details=str(self._error))
        return StubTool(tool_name, error)

    def preload_tools(self, tool_names: list[str]) -> dict[str, bool]:
        """Preload a list of tools and return success status."""
        results = {}
        for tool_name in tool_names:
            try:
                self.get_tool(tool_name)
                results[tool_name] = True
            except Exception:
                results[tool_name] = False
        return results

    def get_loading_stats(self) -> dict[str, Any]:
        """Get statistics about tool loading."""
        return {'cached_tools': list(self._tool_cache.keys()), 'loading_times': self._loading_times.copy(), 'import_errors': {name: str(err) for name, err in self._import_errors.items()}, 'total_cached': len(self._tool_cache), 'total_errors': len(self._import_errors)}

    def clear_cache(self):
        """Clear the tool cache."""
        self._tool_cache.clear()
        self._loading_times.clear()
        self._import_errors.clear()

class LazyToolFactory:
    """Factory for creating lazy tool instances."""

    def __init__(self):
        """Initialize the lazy tool factory."""
        self._loader = LazyToolLoader()

    def create_tool(self, tool_name: str, *args, **kwargs) -> BaseTool:
        """Create a tool instance using lazy loading."""
        return self._loader.get_tool(tool_name, *args, **kwargs)

    def create_tools(self, tool_specs: list[dict[str, Any]]) -> list[BaseTool]:
        """Create multiple tools from specifications."""
        tools = []
        for spec in tool_specs:
            tool_name = spec.get('name')
            if not tool_name:
                continue
            args = spec.get('args', [])
            kwargs = spec.get('kwargs', {})
            try:
                tool = self.create_tool(tool_name, *args, **kwargs)
                tools.append(tool)
            except Exception as e:
                print(f'Warning: Failed to create tool {tool_name}: {e}')
                tools.append(self._loader._create_stub_tool(tool_name, e))
        return tools

    def get_loader_stats(self) -> dict[str, Any]:
        """Get loader statistics."""
        return self._loader.get_loading_stats()
_lazy_factory = LazyToolFactory()

def get_lazy_tool(tool_name: str, *args, **kwargs) -> BaseTool:
    """Get a tool instance using lazy loading."""
    return _lazy_factory.create_tool(tool_name, *args, **kwargs)

def get_lazy_tools(tool_specs: list[dict[str, Any]]) -> list[BaseTool]:
    """Get multiple tool instances using lazy loading."""
    return _lazy_factory.create_tools(tool_specs)

def get_lazy_loader_stats() -> dict[str, Any]:
    """Get lazy loader statistics."""
    return _lazy_factory.get_loader_stats()

def clear_lazy_cache():
    """Clear the lazy tool cache."""
    _lazy_factory._loader.clear_cache()

class LazyToolWrapper:
    """Wrapper that provides lazy loading for tool collections."""

    def __init__(self, tool_specs: list[dict[str, Any]]):
        """Initialize with tool specifications."""
        self._tool_specs = tool_specs
        self._tools: list[BaseTool] | None = None
        self._factory = LazyToolFactory()

    @property
    def tools(self) -> list[BaseTool]:
        """Get tools, loading them lazily on first access."""
        if self._tools is None:
            self._tools = self._factory.create_tools(self._tool_specs)
        return self._tools

    def preload(self) -> dict[str, bool]:
        """Preload all tools and return success status."""
        if self._tools is None:
            self._tools = self._factory.create_tools(self._tool_specs)
        results = {}
        for i, spec in enumerate(self._tool_specs):
            tool_name = spec.get('name', f'tool_{i}')
            results[tool_name] = self._tools[i] is not None
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get loading statistics."""
        return self._factory.get_loader_stats()

def create_lazy_tool_wrapper(tool_specs: list[dict[str, Any]]) -> LazyToolWrapper:
    """Create a lazy tool wrapper for a list of tool specifications."""
    return LazyToolWrapper(tool_specs)