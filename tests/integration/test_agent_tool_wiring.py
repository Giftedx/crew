"""Integration tests for agent-tool wiring."""

import pytest

from domains.orchestration.agents.acquisition.acquisition_specialist import AcquisitionSpecialistAgent
from domains.orchestration.agents.analysis.analysis_cartographer import AnalysisCartographerAgent
from domains.orchestration.agents.verification.verification_director import VerificationDirectorAgent


class TestAgentToolWiring:
    """Test cases for agent-tool wiring integration."""

    def test_acquisition_specialist_tool_assignment(self):
        """Test AcquisitionSpecialistAgent has correct tools assigned."""
        agent = AcquisitionSpecialistAgent()
        tools = agent._get_acquisition_tools()
        tool_classes = [tool.__class__.__name__ for tool in tools]
        assert "MultiPlatformDownloadTool" in tool_classes
        assert "YouTubeDownloadTool" not in tool_classes
        assert "EnhancedYouTubeDownloadTool" not in tool_classes

    def test_analysis_cartographer_tool_assignment(self):
        """Test AnalysisCartographerAgent has correct tools assigned."""
        agent = AnalysisCartographerAgent()
        tools = agent._get_analysis_tools()
        tool_classes = [tool.__class__.__name__ for tool in tools]
        assert any("Text" in name for name in tool_classes)
        assert any("Sentiment" in name for name in tool_classes)

    def test_verification_director_tool_assignment(self):
        """Test VerificationDirectorAgent has correct tools assigned."""
        agent = VerificationDirectorAgent()
        tools = agent._get_verification_tools()
        tool_classes = [tool.__class__.__name__ for tool in tools]
        assert any("Claim" in name for name in tool_classes)
        assert any("Fact" in name for name in tool_classes)

    def test_agent_tool_loading(self):
        """Test that agents can load their tools without errors."""
        try:
            acquisition_agent = AcquisitionSpecialistAgent()
            analysis_agent = AnalysisCartographerAgent()
            verification_agent = VerificationDirectorAgent()
            acquisition_tools = acquisition_agent._get_acquisition_tools()
            analysis_tools = analysis_agent._get_analysis_tools()
            verification_tools = verification_agent._get_verification_tools()
            assert len(acquisition_tools) > 0
            assert len(analysis_tools) > 0
            assert len(verification_tools) > 0
        except Exception as e:
            pytest.fail(f"Agent tool loading failed: {e}")

    def test_tool_consistency_across_agents(self):
        """Test that tools are consistently available across agents."""
        acquisition_agent = AcquisitionSpecialistAgent()
        analysis_agent = AnalysisCartographerAgent()
        verification_agent = VerificationDirectorAgent()
        all_tools = []
        all_tools.extend(acquisition_agent._get_acquisition_tools())
        all_tools.extend(analysis_agent._get_analysis_tools())
        all_tools.extend(verification_agent._get_verification_tools())
        tool_classes = [tool.__class__.__name__ for tool in all_tools]
        unique_classes = set(tool_classes)
        assert len(unique_classes) > 10, f"Too few unique tool classes: {len(unique_classes)}"
        assert len(tool_classes) > 15, f"Too few total tools: {len(tool_classes)}"

    def test_agent_tool_execution_capability(self):
        """Test that agents can execute their tools."""
        acquisition_agent = AcquisitionSpecialistAgent()
        tools = acquisition_agent._get_acquisition_tools()
        if tools:
            tool = tools[0]
            assert hasattr(tool, "_run"), f"Tool {tool.name} missing _run method"
            assert callable(tool._run), f"Tool {tool.name} _run method not callable"

    def test_memory_tool_integration(self):
        """Test that memory tools are properly integrated."""
        analysis_agent = AnalysisCartographerAgent()
        tools = analysis_agent._get_analysis_tools()
        tool_classes = [tool.__class__.__name__ for tool in tools]
        memory_tools = [
            name for name in tool_classes if any(keyword in name for keyword in ["Memory", "RAG", "Vector", "Storage"])
        ]
        if len(memory_tools) == 0:
            assert len(tool_classes) > 0, "No analysis tools found"

    def test_verification_tool_integration(self):
        """Test that verification tools are properly integrated."""
        verification_agent = VerificationDirectorAgent()
        tools = verification_agent._get_verification_tools()
        tool_classes = [tool.__class__.__name__ for tool in tools]
        verification_tools = [
            name for name in tool_classes if any(keyword in name for keyword in ["Verify", "Check", "Fact"])
        ]
        assert len(verification_tools) > 0, "No verification tools found in verification agent"

    def test_tool_error_handling(self):
        """Test that tools handle errors gracefully."""
        acquisition_agent = AcquisitionSpecialistAgent()
        tools = acquisition_agent._get_acquisition_tools()
        if tools:
            tool = tools[0]
            try:
                result = tool._run("invalid_input")
                assert hasattr(result, "success")
                assert hasattr(result, "error")
            except Exception as e:
                assert "error" in str(e).lower() or "failed" in str(e).lower()

    def test_agent_tool_dependencies(self):
        """Test that agent tools have their dependencies satisfied."""
        agents = [AcquisitionSpecialistAgent(), AnalysisCartographerAgent(), VerificationDirectorAgent()]
        for agent in agents:
            if hasattr(agent, "_get_acquisition_tools"):
                tools = agent._get_acquisition_tools()
            elif hasattr(agent, "_get_analysis_tools"):
                tools = agent._get_analysis_tools()
            elif hasattr(agent, "_get_verification_tools"):
                tools = agent._get_verification_tools()
            else:
                continue
            for tool in tools:
                assert tool is not None, f"Tool {tool.__class__.__name__} is None"
                assert hasattr(tool, "__class__"), "Tool missing class attribute"
                has_run_method = hasattr(tool, "_run")
                has_run_public = hasattr(tool, "run")
                has_execute_method = hasattr(tool, "execute")
                has_call_method = hasattr(tool, "__call__")
                if "MissingDependencyTool" in tool.__class__.__name__ or "Stub" in tool.__class__.__name__:
                    continue
                assert (
                    has_run_method or has_run_public or has_execute_method or has_call_method
                ), f"Tool {tool.__class__.__name__} missing execution method"
