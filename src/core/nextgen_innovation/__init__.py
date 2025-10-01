"""Next-Generation Innovation Platform (modularized).

Exports the public API that used to live in core.nextgen_innovation_platform.
Prefer importing from this package for new code; the original module path
continues to work via a compatibility shim.
"""

from .adaptive import AdaptiveLearningArchitecture
from .consciousness import ConsciousnessLevelDecisionMaking
from .enums import AIOrchestrationMode, ConsciousnessLevel, InnovationLevel
from .knowledge import CrossDomainKnowledgeSynthesis
from .multimodel import MultiModelIntelligence
from .orchestration import demonstrate_revolutionary_capabilities, run_phase6_innovation_cycle
from .quantum import QuantumInspiredComputing
from .types import BreakthroughCandidate, InnovationMetrics, KnowledgeDomain

__all__ = [
    # Enums/Types
    "AIOrchestrationMode",
    "ConsciousnessLevel",
    "InnovationLevel",
    "BreakthroughCandidate",
    "InnovationMetrics",
    "KnowledgeDomain",
    # Subsystems
    "MultiModelIntelligence",
    "CrossDomainKnowledgeSynthesis",
    "AdaptiveLearningArchitecture",
    "QuantumInspiredComputing",
    "ConsciousnessLevelDecisionMaking",
    # Orchestration
    "run_phase6_innovation_cycle",
    "demonstrate_revolutionary_capabilities",
]
