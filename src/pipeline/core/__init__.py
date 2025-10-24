"""Minimal pipeline core interfaces (Step, Middleware, Executor).

Safe scaffolding only; no behavior changes to existing pipelines.
"""

from .executor import Executor
from .middleware import Middleware
from .step import Step


__all__ = ["Executor", "Middleware", "Step"]
