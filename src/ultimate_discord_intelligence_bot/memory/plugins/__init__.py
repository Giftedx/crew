"""Memory plugins for specialty backends.

Plugins provide integration with specialized memory systems:
- Mem0Plugin: Long-term episodic memory with user preferences
- HippoRAGPlugin: Continual learning with hippocampal memory patterns
- GraphPlugin: Knowledge graph memory with relationship traversal
"""

from .graph_plugin import GraphPlugin
from .hipporag_plugin import HippoRAGPlugin
from .mem0_plugin import Mem0Plugin


__all__ = ["GraphPlugin", "HippoRAGPlugin", "Mem0Plugin"]
