from __future__ import annotations
from typing import Any, Dict


def run(adapters: Dict[str, Any], text: str) -> str:
    """Example summarizer plugin that echoes a fixed summary.

    Parameters
    ----------
    adapters:
        Mapping of service adapters. Only ``svc_llm`` is used here.
    text:
        Text to summarise.
    """

    llm = adapters["svc_llm"]
    return llm.generate(text)


def self_test() -> bool:
    """Simple self-test used by the plugin testkit.

    Returns
    -------
    bool
        ``True`` if the smoke test passes.
    """

    return True
