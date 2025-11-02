"""Domain layer - business logic organized by capability.

This package provides domain-specific functionality for the Discord Intelligence Bot:
- Intelligence: Content analysis, verification, reasoning engines
- Ingestion: Multi-platform content acquisition (YouTube, TikTok, Twitter, etc.)
- Memory: Vector storage, knowledge graphs, retrieval systems
- Orchestration: CrewAI agents, tasks, and crew management

Architecture: Domains contain all business logic and depend on Platform for infrastructure.
"""

__all__ = [
    # Domains are organized but not re-exported at package level
    # Import from specific domain modules instead:
    # from domains.intelligence.analysis import TextAnalysisTool
    # from domains.memory.vector_store import VectorStore
    # from domains.orchestration.crew import UltimateDiscordIntelligenceBotCrew
]
