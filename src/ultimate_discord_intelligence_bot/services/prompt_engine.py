"""Utilities for building prompts and counting tokens.

The :class:`PromptEngine` centralises prompt construction and token counting so
any agent, tool or workflow can consistently prepare requests for large
language models. Token counting is provider aware: ``tiktoken`` powers OpenAI
model estimates, ``transformers`` tokenizers cover other providers and a simple
whitespace split acts as a final fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .memory_service import MemoryService

try:  # pragma: no cover - optional dependency
    import tiktoken
except Exception:  # pragma: no cover
    tiktoken = None

try:  # pragma: no cover - optional dependency
    from transformers import AutoTokenizer  # type: ignore
except Exception:  # pragma: no cover
    AutoTokenizer = None


@dataclass
class PromptEngine:
    """Generate prompts and estimate token usage."""

    memory: Optional[MemoryService] = None
    _tokenizers: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def generate(self, template: str, variables: Dict[str, Any]) -> str:
        """Fill ``template`` with ``variables`` using ``str.format``."""
        return template.format(**variables)

    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Return an estimated token count for ``text``.

        Parameters
        ----------
        text:
            The prompt text to analyse.
        model:
            Optional model name. When supplied the engine attempts to use a
            provider-specific tokenizer: ``tiktoken`` for OpenAI models and
            ``transformers`` for others. If no specialised tokenizer is
            available a simple whitespace split provides a conservative
            fallback.
        """
        if model:
            if tiktoken:
                try:
                    enc = tiktoken.encoding_for_model(model)
                    return len(enc.encode(text))
                except Exception:
                    pass
            if AutoTokenizer:
                try:
                    tokenizer = self._tokenizers.get(model)
                    if tokenizer is None:
                        tokenizer = AutoTokenizer.from_pretrained(model)
                        self._tokenizers[model] = tokenizer
                    return len(tokenizer.encode(text))
                except Exception:
                    pass
            if tiktoken:
                enc = tiktoken.get_encoding("cl100k_base")
                return len(enc.encode(text))
        return len(text.split())

    def optimise(self, prompt: str) -> str:
        """Return a lightly normalised variant of ``prompt``.

        This basic implementation simply strips surrounding whitespace; it can
        be extended with more advanced optimisation strategies.
        """
        return prompt.strip()

    def build_with_context(
        self,
        instruction: str,
        query: str,
        k: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a prompt that includes top-``k`` context snippets.

        ``metadata`` may be provided to scope memory lookups to a specific
        creator or source. Returned prompts list sources for traceability.
        """

        context_blocks = []
        sources = []
        if self.memory:
            hits = self.memory.retrieve(query, limit=k, metadata=metadata)
            for idx, hit in enumerate(hits, 1):
                context_blocks.append(f"[{idx}] {hit['text']}")
                meta = hit.get("metadata", {})
                src = meta.get("source")
                ts = meta.get("ts")
                if src:
                    if ts is not None:
                        sources.append(f"[{idx}] {src}#{ts}")
                    else:
                        sources.append(f"[{idx}] {src}")
        context_text = "\n".join(context_blocks) or "(no context)"
        sources_text = "\n".join(sources)
        return f"{instruction}\n\nContext:\n{context_text}\n\nSources:\n{sources_text}\n\nQuery: {query}" 
