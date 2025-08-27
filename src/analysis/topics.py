from __future__ import annotations

"""Minimal topic/keyword extraction utilities."""

from dataclasses import dataclass
from typing import List
import re


@dataclass
class TopicResult:
    topics: List[str]
    entities: List[str]
    hashtags: List[str]


def extract(text: str) -> TopicResult:
    """Extract rough topics and hashtags from *text*.

    This very lightweight implementation is intended for unit tests and
    placeholder behaviour.  It simply tokenises words and hashtags and
    returns unique lowercase values.
    """

    tokens = re.findall(r"[#@]?[A-Za-z0-9_]+", text)
    hashtags = sorted({t.lower() for t in tokens if t.startswith("#")})
    topics = sorted({t.lower() for t in tokens if not t.startswith(("#", "@"))})
    return TopicResult(topics=topics, entities=[], hashtags=hashtags)
