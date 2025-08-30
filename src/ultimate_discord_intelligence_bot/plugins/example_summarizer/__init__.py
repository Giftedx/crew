from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class _LLMLike(Protocol):  # minimal protocol for the adapter used
    def generate(self, text: str) -> str: ...


def run(adapters: dict[str, Any], text: str) -> str:
    """Example summarizer plugin that echoes a fixed summary.

    Parameters
    ----------
    adapters:
        Mapping of service adapters. Only ``svc_llm`` is used here.
    text:
        Text to summarise.
    """

    llm = adapters["svc_llm"]
    # Provide a defensive cast-like runtime check without importing typing.cast
    if not isinstance(llm, _LLMLike):
        # Fallback: best effort string conversion
        return str(getattr(llm, "generate", lambda _: llm)(text))
    return llm.generate(text)


def self_test() -> bool:
    """Simple self-test used by the plugin testkit.

    Returns
    -------
    bool
        ``True`` if the smoke test passes.
    """

    return True
