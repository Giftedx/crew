"""Tests for tool contract validation."""

from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from ultimate_discord_intelligence_bot.tools.validation import (
    ToolContractViolation,
    get_tool_metadata,
    validate_tool_contract,
    validate_tool_instance,
)


class ValidTool(BaseTool):
    """A tool that conforms to the contract."""

    name = "valid_tool"
    description = "Test tool for validation"

    def _run(self, input_data: str, tenant: str = "default", workspace: str = "main", **kwargs) -> StepResult:
        """Run the tool."""
        return StepResult.ok(result=f"Processed: {input_data}")


class InvalidToolNoRun(BaseTool):
    """Tool missing _run method."""

    name = "invalid_no_run"
    description = "Missing run method"


class InvalidToolWrongSignature(BaseTool):
    """Tool with wrong _run signature (missing tenant/workspace)."""

    name = "invalid_signature"
    description = "Wrong signature"

    def _run(self, input_data: str) -> StepResult:
        """Missing tenant/workspace params."""
        return StepResult.ok(result=input_data)


class LegacyDictTool(BaseTool):
    """Tool that returns dict (legacy compatibility)."""

    name = "legacy_dict"
    description = "Returns dict"

    def _run(self, data: str, tenant: str = "default", workspace: str = "main", **kwargs) -> dict:
        """Returns dict instead of StepResult."""
        return {"status": "success", "data": data}


class KwargsCaptureTool(BaseTool):
    """Tool that uses **kwargs to capture tenant/workspace."""

    name = "kwargs_tool"
    description = "Uses kwargs"

    def _run(self, input_data: str, **kwargs) -> StepResult:
        """Captures tenant/workspace via kwargs."""
        tenant = kwargs.get("tenant", "default")
        workspace = kwargs.get("workspace", "main")
        return StepResult.ok(input=input_data, tenant=tenant, workspace=workspace)


def test_validate_valid_tool():
    """Test validation passes for conforming tool."""
    result = validate_tool_contract(ValidTool)
    assert result.success
    assert result["tool"] == "ValidTool"
    assert result["validated"] is True


def test_validate_missing_run_method():
    """Test validation fails when _run missing."""
    result = validate_tool_contract(InvalidToolNoRun)
    assert not result.success
    assert "missing required _run method" in result.error.lower()


def test_validate_wrong_signature():
    """Test validation warns about missing tenant/workspace params."""
    result = validate_tool_contract(InvalidToolWrongSignature)
    # Should fail due to missing params
    assert not result.success
    assert "tenant" in result.error.lower() or "workspace" in result.error.lower()


def test_validate_kwargs_capture():
    """Test validation passes for tools using **kwargs."""
    result = validate_tool_contract(KwargsCaptureTool)
    # Should pass because **kwargs captures tenant/workspace
    assert result.success


def test_validate_legacy_dict_return():
    """Test validation allows dict return type for legacy compatibility."""
    result = validate_tool_contract(LegacyDictTool)
    # Should pass - dict is allowed for backward compatibility
    assert result.success


def test_validate_instance_valid():
    """Test instance validation for valid tool."""
    tool = ValidTool()
    result = validate_tool_instance(tool, {"input_data": "test"})
    assert result.success
    assert result["return_type"] == "StepResult"


def test_validate_instance_dict_return():
    """Test instance validation for legacy dict-returning tool."""
    tool = LegacyDictTool()
    result = validate_tool_instance(tool, {"data": "test"})
    assert result.success
    assert result["return_type"] == "dict"


def test_validate_instance_missing_status():
    """Test instance validation fails for dict without status."""

    class BadDictTool(BaseTool):
        name = "bad_dict"
        description = "Returns dict without status"

        def _run(self, **kwargs) -> dict:
            return {"data": "no status key"}

    tool = BadDictTool()
    result = validate_tool_instance(tool)
    assert not result.success
    assert "status" in result.error.lower()


def test_get_tool_metadata():
    """Test metadata extraction."""
    metadata = get_tool_metadata(ValidTool)

    assert metadata["name"] == "ValidTool"
    assert "contract" in metadata["description"].lower()
    assert "input_data" in metadata["required_params"]


def test_metadata_optional_params():
    """Test metadata distinguishes required vs optional params."""

    class ParamTool(BaseTool):
        """Tool with mixed params."""

        name = "param_tool"

        def _run(
            self,
            required_arg: str,
            optional_arg: str = "default",
            tenant: str = "default",
            workspace: str = "main",
            **kwargs,
        ) -> StepResult:
            return StepResult.ok()

    metadata = get_tool_metadata(ParamTool)

    assert "required_arg" in metadata["required_params"]
    assert "optional_arg" in metadata["optional_params"]
    # tenant/workspace should be filtered out
    assert "tenant" not in metadata["required_params"]
    assert "tenant" not in metadata["optional_params"]


@pytest.mark.parametrize(
    "tool_class,should_pass",
    [
        (ValidTool, True),
        (KwargsCaptureTool, True),
        (LegacyDictTool, True),
        (InvalidToolNoRun, False),
        (InvalidToolWrongSignature, False),
    ],
)
def test_validation_matrix(tool_class, should_pass):
    """Test validation across various tool implementations."""
    result = validate_tool_contract(tool_class)
    assert result.success == should_pass
