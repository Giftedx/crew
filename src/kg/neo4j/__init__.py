"""Neo4j knowledge graph backend."""

try:
    from src.kg.neo4j.store import Neo4jKGStore
    __all__ = ["Neo4jKGStore"]
except ImportError:
    __all__ = []
