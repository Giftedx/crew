"""Minimal ID generator stubs for OpenTelemetry compatibility."""

from __future__ import annotations

import random


class IdGenerator:
    """Base ID generator stub."""

    def generate_trace_id(self) -> int:
        return random.getrandbits(128)

    def generate_span_id(self) -> int:
        return random.getrandbits(64)


class RandomIdGenerator(IdGenerator):
    """Concrete random ID generator stub."""


__all__ = ["IdGenerator", "RandomIdGenerator"]
