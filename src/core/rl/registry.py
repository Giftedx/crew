"""Policy registry for dependency injection."""

from __future__ import annotations


class PolicyRegistry:
    """A minimal registry for RL policies."""

    def __init__(self) -> None:
        self._policies: dict[str, object] = {}

    def register(self, name: str, policy: object) -> None:
        self._policies[name] = policy

    def get(self, name: str) -> object:
        return self._policies[name]

    def items(self) -> list[tuple[str, object]]:
        """Return a snapshot list of ``(name, policy)`` pairs.

        A list is returned (rather than the live ``dict_items`` view) to provide
        a stable snapshot for callers and simpler typing.
        """
        return list(self._policies.items())

    # Provide containment to support legacy shims performing ``if name not in registry``.
    def __contains__(self, name: str) -> bool:  # pragma: no cover - trivial
        return name in self._policies
