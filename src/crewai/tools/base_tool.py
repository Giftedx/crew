"""Base tool module for crewai.tools compatibility."""

import sys


# Temporarily remove local crewai package from sys.path to import system BaseTool
_original_path = sys.path[:]
try:
    # Remove the local src directory containing our crewai package
    local_src = None
    for path in sys.path:
        if path.endswith("/src") and "/home/crew" in path:
            local_src = path
            break

    if local_src and local_src in sys.path:
        sys.path.remove(local_src)

    # Now import from system crewai.tools
    from crewai.tools.base_tool import BaseTool

finally:
    # Restore original sys.path
    sys.path[:] = _original_path

__all__ = ["BaseTool"]
