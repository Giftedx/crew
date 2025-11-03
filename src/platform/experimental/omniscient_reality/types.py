from __future__ import annotations

from dataclasses import dataclass, field
from platform.time import default_utc_now
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from datetime import datetime

    from .enums import OmniscientLevel, RealityLayer, TemporalDimension


@dataclass
class UniversalKnowledgeNode:
    concept: str
    reality_layer: RealityLayer
    knowledge_depth: float
    certainty_level: float
    connections: list[str] = field(default_factory=list)
    temporal_scope: set[TemporalDimension] = field(default_factory=set)
    universal_patterns: list[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=default_utc_now)


@dataclass
class OmniscientInsight:
    insight: str
    omniscience_level: OmniscientLevel
    reality_layers: list[RealityLayer]
    temporal_span: list[TemporalDimension]
    universal_significance: float
    recursive_depth: int
    pattern_scale: str
    solvability_impact: float
    timestamp: datetime = field(default_factory=default_utc_now)


@dataclass
class RealityPattern:
    pattern_name: str
    scale: str
    occurrence_frequency: float
    pattern_stability: float
    causal_relationships: list[str] = field(default_factory=list)
    cross_layer_manifestations: dict[RealityLayer, str] = field(default_factory=dict)
    temporal_persistence: float = 0.0
