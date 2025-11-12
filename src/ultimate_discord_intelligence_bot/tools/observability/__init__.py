"""Tools for the observability domain.

This subpackage intentionally avoids importing heavy optional dependencies at import time.
Tool classes are lazily imported via __getattr__ to keep base imports lightweight.
"""

_MAPPING = {
    # File-local tools that are generally lightweight
    "MCPCallTool": ".mcp_call_tool",
    "FastMCPClientTool": ".fastmcp_client_tool",
    # Heavier tools (crewai, etc.) - only imported if explicitly requested
    "DashboardIntegrationTool": ".observability_tool",
    "IntelligentAlertingTool": ".observability_tool",
    "UnifiedMetricsTool": ".observability_tool",
    "UnifiedCacheTool": ".unified_cache_tool",
    "CacheOptimizationTool": ".unified_cache_tool",
    "CacheStatusTool": ".unified_cache_tool",
    "UnifiedOrchestrationTool": ".unified_orchestration_tool",
    "OrchestrationStatusTool": ".unified_orchestration_tool",
    "TaskManagementTool": ".unified_orchestration_tool",
    "UnifiedRouterTool": ".unified_router_tool",
    "RouterStatusTool": ".unified_router_tool",
    "CostTrackingTool": ".unified_router_tool",
    "SystemStatusTool": ".system_status_tool",
    "WorkflowOptimizationTool": ".workflow_optimization_tool",
    "DependencyResolverTool": ".dependency_resolver_tool",
    "EarlyExitConditionsTool": ".early_exit_conditions_tool",
    "AgentBridgeTool": ".agent_bridge_tool",
    "ResourceAllocationTool": ".resource_allocation_tool",
    "PipelineTool": ".pipeline_tool",
    "ContentTypeRoutingTool": ".content_type_routing_tool",
    "CheckpointManagementTool": ".checkpoint_management_tool",
}

__all__ = sorted(_MAPPING.keys())


def __getattr__(name: str):  # PEP 562: lazy attribute loading
    mod = _MAPPING.get(name)
    if mod is None:
        raise AttributeError(name)
    from importlib import import_module

    module_path = f"{__name__}{mod}"
    module = import_module(module_path)
    try:
        return getattr(module, name)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise AttributeError(name) from exc


def __dir__():  # pragma: no cover - cosmetic
    return sorted(list(globals().keys()) + __all__)
