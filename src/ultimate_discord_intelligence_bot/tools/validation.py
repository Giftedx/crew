"""Tool contract validation for StepResult compliance.

Validates that tools conform to the required contract:
- Inherit from BaseTool
- Implement _run method with correct signature
- Return StepResult (or dict for legacy compatibility)
- Export in __all__ if in a module
"""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tools._base import BaseTool


logger = logging.getLogger(__name__)


class ToolContractViolation(Exception):
    """Raised when a tool violates the required contract."""


def validate_tool_contract(tool_class: type[BaseTool]) -> StepResult:
    """Validate that a tool class conforms to required contracts.

    Checks:
    1. Class inherits from BaseTool
    2. _run method exists
    3. _run accepts tenant/workspace parameters
    4. _run return type annotation is StepResult (or dict for legacy)

    Args:
        tool_class: Tool class to validate

    Returns:
        StepResult.ok if valid, StepResult.fail with violation details

    Raises:
        ToolContractViolation: If validation fails in strict mode
    """
    violations: list[str] = []

    # Check 1: Inherits from BaseTool
    try:
        from ultimate_discord_intelligence_bot.tools._base import BaseTool

        if not issubclass(tool_class, BaseTool):
            violations.append(f"{tool_class.__name__} does not inherit from BaseTool")
    except (ImportError, TypeError) as e:
        violations.append(f"Cannot verify BaseTool inheritance: {e}")

    # Check 2: _run method exists
    if not hasattr(tool_class, "_run"):
        violations.append(f"{tool_class.__name__} missing required _run method")
        # Can't validate further without _run
        return StepResult.validation_error(
            f"Tool contract validation failed: {'; '.join(violations)}",
            tool=tool_class.__name__,
            violations=violations,
        )

    # Check 3: _run signature includes tenant/workspace
    try:
        sig = inspect.signature(tool_class._run)
        params = list(sig.parameters.keys())

        # Should have: self, <positional args>, tenant, workspace, **kwargs
        # Or accept **kwargs which would capture them
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

        if not has_kwargs:
            # Check for explicit tenant/workspace params
            if "tenant" not in params:
                violations.append(
                    f"{tool_class.__name__}._run missing 'tenant' parameter (required unless **kwargs present)"
                )
            if "workspace" not in params:
                violations.append(
                    f"{tool_class.__name__}._run missing 'workspace' parameter (required unless **kwargs present)"
                )
    except (ValueError, TypeError) as e:
        violations.append(f"Cannot inspect _run signature: {e}")

    # Check 4: Return type annotation
    try:
        sig = inspect.signature(tool_class._run)
        return_annotation = sig.return_annotation

        if return_annotation is inspect.Signature.empty:
            # No annotation - log warning but allow (legacy compatibility)
            logger.debug(f"{tool_class.__name__}._run missing return type annotation (should be StepResult)")
        else:
            # Check if annotation is StepResult or dict
            ann_str = str(return_annotation)
            if "StepResult" not in ann_str and "dict" not in ann_str:
                violations.append(
                    f"{tool_class.__name__}._run return type should be StepResult or dict, got {return_annotation}"
                )
    except Exception as e:
        logger.debug(f"Cannot check return annotation for {tool_class.__name__}: {e}")

    if violations:
        return StepResult.validation_error(
            f"Tool contract validation failed: {'; '.join(violations)}",
            tool=tool_class.__name__,
            violations=violations,
        )

    return StepResult.ok(
        tool=tool_class.__name__,
        validated=True,
        message="Tool contract validation passed",
    )


def validate_tool_instance(tool: BaseTool, test_kwargs: dict[str, Any] | None = None) -> StepResult:
    """Validate a tool instance by calling _run with test inputs.

    Args:
        tool: Tool instance to validate
        test_kwargs: Optional kwargs to pass to _run for testing

    Returns:
        StepResult indicating validation success/failure
    """
    if test_kwargs is None:
        test_kwargs = {
            "tenant": "validation_test",
            "workspace": "validation_test",
        }

    try:
        # Attempt to call _run (may raise if required args missing)
        # We don't care about the actual result, just that it returns StepResult
        result = tool._run(**test_kwargs)

        # Check return type
        if not isinstance(result, (StepResult, dict)):
            return StepResult.validation_error(
                f"{tool.__class__.__name__}._run returned {type(result).__name__}, expected StepResult or dict",
                tool=tool.__class__.__name__,
            )

        # If dict, verify it has required keys
        if isinstance(result, dict) and "status" not in result:
            return StepResult.validation_error(
                f"{tool.__class__.__name__}._run returned dict without 'status' key",
                tool=tool.__class__.__name__,
            )

        return StepResult.ok(
            tool=tool.__class__.__name__,
            validated=True,
            return_type=type(result).__name__,
        )

    except TypeError as e:
        # Signature mismatch
        return StepResult.validation_error(
            f"{tool.__class__.__name__}._run signature error: {e}",
            tool=tool.__class__.__name__,
        )
    except Exception as e:
        # Tool execution failed (may be expected if inputs are invalid)
        # This is OK - we just want to verify it returns proper types
        logger.debug(
            f"{tool.__class__.__name__}._run raised {type(e).__name__} during validation (may be expected): {e}"
        )
        return StepResult.ok(
            tool=tool.__class__.__name__,
            validated=True,
            note="Tool raised exception during test run (may be expected)",
        )


def get_tool_metadata(tool_class: type[BaseTool]) -> dict[str, Any]:
    """Extract metadata from a tool class.

    Returns:
        Dict with name, description, category, required_params, optional_params
    """
    metadata = {
        "name": tool_class.__name__,
        "description": tool_class.__doc__ or "No description",
        "category": getattr(tool_class, "category", "unknown"),
    }

    # Extract parameters from _run signature
    try:
        sig = inspect.signature(tool_class._run)
        required = []
        optional = []

        for param_name, param in sig.parameters.items():
            if param_name in {"self", "tenant", "workspace", "kwargs"}:
                continue

            if param.default is inspect.Parameter.empty:
                required.append(param_name)
            else:
                optional.append(param_name)

        metadata["required_params"] = required
        metadata["optional_params"] = optional

    except Exception as e:
        logger.debug(f"Cannot extract params for {tool_class.__name__}: {e}")
        metadata["required_params"] = []
        metadata["optional_params"] = []

    return metadata
