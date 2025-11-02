"""Modular building blocks for the content pipeline."""

from .types import PipelineRunResult


__all__ = ["ContentPipeline", "PipelineRunResult"]


def __getattr__(name: str):  # pragma: no cover - exercised implicitly
    if name == "ContentPipeline":
        from .orchestrator import ContentPipeline

        return ContentPipeline
    raise AttributeError(name)
