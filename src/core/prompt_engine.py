"""Minimal prompt builder with context injection and tool manifests.

This module constructs deterministic prompts with a safety preamble and
optional memory/context and tool descriptions. It intentionally avoids any
clever templating to keep behaviour predictable for reinforcement learning.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from platform.security.privacy import privacy_filter
if TYPE_CHECKING:
    from collections.abc import Sequence
SAFETY_PREAMBLE = 'You are a helpful assistant.'

def build_prompt(template: str, *, context: str | None=None, tools: Sequence[str] | None=None) -> str:
    """Render a prompt from ``template`` with optional context and tools.

    Parameters
    ----------
    template:
        Base template with placeholders already resolved.
    context:
        Additional memory or conversation context to inject.
    tools:
        Human readable tool manifest entries.
    """
    pieces = [SAFETY_PREAMBLE, template]
    if context:
        pieces.append(f'Context:\n{context}')
    if tools:
        pieces.append('Available tools:\n' + ', '.join(tools))
    prompt = '\n\n'.join(pieces)
    clean, _ = privacy_filter.filter_text(prompt, {})
    return clean
__all__ = ['SAFETY_PREAMBLE', 'build_prompt']