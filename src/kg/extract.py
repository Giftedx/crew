from __future__ import annotations
"""Naive entity and claim extractor used during ingestion."""

from dataclasses import dataclass
from typing import List, Tuple
import re


ENTITY_RE = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b")
CLAIM_RE = re.compile(r"([^.!?]+?(?:is|are|was|were)[^.!?]+)")


@dataclass
class ExtractedItem:
    text: str
    start: int
    end: int


def extract(text: str) -> Tuple[List[ExtractedItem], List[ExtractedItem]]:
    """Return lists of naive entity and claim spans."""
    entities = [ExtractedItem(m.group(1), m.start(1), m.end(1)) for m in ENTITY_RE.finditer(text)]
    claims = [ExtractedItem(m.group(1), m.start(1), m.end(1)) for m in CLAIM_RE.finditer(text)]
    return entities, claims
