"""
Tests for API integration tools (APIClientTool, CodeAnalysisTool).
"""

import pytest

from ai.frameworks.tools.implementations import APIClientTool, CodeAnalysisTool


class TestAPIClientTool:
    """Test suite for APIClientTool."""

    @pytest.fixture
    def api_client(self):
        """Create APIClientTool instance."""
        return APIClientTool()

    def test_tool_properties(self, api_client):
        """Test tool has correct metadata."""
        assert api_client.name == "api-client"
        assert "HTTP" in api_client.description
        assert "method" in api_client.parameters
        assert "url" in api_client.parameters
        assert api_client.metadata.category == "api"
        assert "http" in api_client.metadata.tags

    def test_parameter_validation(self, api_client):
        """Test parameter validation works correctly."""
        # Valid parameters
        valid, error = api_client.validate_parameters(method="GET", url="https://api.example.com/users")
        assert valid is True
        assert error is None

        # Missing required parameter
        valid, error = api_client.validate_parameters(method="GET")
        assert valid is False
        assert "url" in error.lower()

        # Unknown parameter
        valid, error = api_client.validate_parameters(method="GET", url="https://api.example.com", invalid_param="test")
        assert valid is False
        assert "unknown" in error.lower()

    @pytest.mark.asyncio
    async def test_get_request(self, api_client):
        """Test GET request execution."""
        result = await api_client.run(method="GET", url="https://api.example.com/users/123")

        assert result["success"] is True
        assert result["status_code"] == 200
        assert "headers" in result
        assert "body" in result
        assert "GET" in result["body"]

    @pytest.mark.asyncio
    async def test_post_request_with_body(self, api_client):
        """Test POST request with body."""
        result = await api_client.run(
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            body='{"name": "John", "email": "john@example.com"}',
        )

        assert result["success"] is True
        assert result["status_code"] == 201
        assert "POST" in result["body"]

    @pytest.mark.asyncio
    async def test_custom_headers(self, api_client):
        """Test custom headers are accepted."""
        result = await api_client.run(
            method="GET",
            url="https://api.example.com/protected",
            headers={"Authorization": "Bearer token123", "X-Custom-Header": "value"},
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_timeout_validation(self, api_client):
        """Test timeout parameter validation."""
        # Valid timeout
        result = await api_client.run(method="GET", url="https://api.example.com/slow", timeout=60)
        assert result["success"] is True

        # Invalid timeout (too low)
        with pytest.raises(ValueError, match="Timeout must be between"):
            await api_client.run(method="GET", url="https://api.example.com", timeout=0)

        # Invalid timeout (too high)
        with pytest.raises(ValueError, match="Timeout must be between"):
            await api_client.run(method="GET", url="https://api.example.com", timeout=500)

    @pytest.mark.asyncio
    async def test_different_http_methods(self, api_client):
        """Test all supported HTTP methods."""
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for method in methods:
            result = await api_client.run(method=method, url="https://api.example.com/resource")
            assert result["success"] is True
            assert method in result["body"]

    @pytest.mark.asyncio
    async def test_autogen_function_schema(self, api_client):
        """Test AutoGen function schema generation."""
        schema = api_client.to_autogen_function()

        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == "api-client"
        assert "parameters" in schema["function"]
        assert "method" in schema["function"]["parameters"]["properties"]
        assert "url" in schema["function"]["parameters"]["properties"]
        assert "required" in schema["function"]["parameters"]
        assert "method" in schema["function"]["parameters"]["required"]
        assert "url" in schema["function"]["parameters"]["required"]


class TestCodeAnalysisTool:
    """Test suite for CodeAnalysisTool."""

    @pytest.fixture
    def analyzer(self):
        """Create CodeAnalysisTool instance."""
        return CodeAnalysisTool()

    def test_tool_properties(self, analyzer):
        """Test tool has correct metadata."""
        assert analyzer.name == "code-analysis"
        assert "static" in analyzer.description.lower() or "analyze" in analyzer.description.lower()
        assert "code" in analyzer.parameters
        assert "language" in analyzer.parameters
        assert analyzer.metadata.category == "development"
        assert "analysis" in analyzer.metadata.tags

    def test_parameter_validation(self, analyzer):
        """Test parameter validation."""
        # Valid parameters
        valid, error = analyzer.validate_parameters(code="print('hello')", language="python")
        assert valid is True
        assert error is None

        # Missing required parameter
        valid, error = analyzer.validate_parameters(code="print('hello')")
        assert valid is False
        assert "language" in error.lower()

    @pytest.mark.asyncio
    async def test_syntax_check_valid_python(self, analyzer):
        """Test syntax check with valid Python code."""
        code = """
def greet(name):
    return f"Hello, {name}!"

result = greet("World")
print(result)
"""
        result = await analyzer.run(code=code, language="python", checks=["syntax"])

        assert "issues" in result
        assert "summary" in result
        # Valid code should have no syntax errors
        syntax_errors = [i for i in result["issues"] if i["severity"] == "error"]
        assert len(syntax_errors) == 0

    @pytest.mark.asyncio
    async def test_syntax_check_invalid_python(self, analyzer):
        """Test syntax check with invalid Python code."""
        code = """
def broken_function(
    print("Missing closing paren")
"""
        result = await analyzer.run(code=code, language="python", checks=["syntax"])

        # Should detect syntax error
        syntax_errors = [i for i in result["issues"] if i["rule"] == "syntax-error"]
        assert len(syntax_errors) > 0
        assert result["summary"]["errors"] > 0

    @pytest.mark.asyncio
    async def test_style_check_line_length(self, analyzer):
        """Test style check detects long lines."""
        code = "x = 'This is a very long line that exceeds the maximum allowed line length and should trigger a style warning from the analyzer'\n"

        result = await analyzer.run(code=code, language="python", checks=["style"], max_line_length=80)

        # Should detect line too long
        line_length_issues = [i for i in result["issues"] if i["rule"] == "line-too-long"]
        assert len(line_length_issues) > 0

    @pytest.mark.asyncio
    async def test_style_check_trailing_whitespace(self, analyzer):
        """Test style check detects trailing whitespace."""
        code = "x = 1  \ny = 2\n"  # First line has trailing spaces

        result = await analyzer.run(code=code, language="python", checks=["style"])

        # Should detect trailing whitespace
        whitespace_issues = [i for i in result["issues"] if i["rule"] == "trailing-whitespace"]
        assert len(whitespace_issues) > 0

    @pytest.mark.asyncio
    async def test_security_check_python_eval(self, analyzer):
        """Test security check detects dangerous eval()."""
        code = """
user_input = input("Enter code: ")
result = eval(user_input)  # Dangerous!
"""
        result = await analyzer.run(code=code, language="python", checks=["security"])

        # Should detect eval security issue
        security_issues = [i for i in result["issues"] if i["rule"] == "security-vulnerability"]
        assert len(security_issues) > 0
        eval_issues = [i for i in security_issues if "eval" in i["message"].lower()]
        assert len(eval_issues) > 0
        assert eval_issues[0]["severity"] == "error"

    @pytest.mark.asyncio
    async def test_security_check_javascript_eval(self, analyzer):
        """Test security check for JavaScript."""
        code = """
const userCode = getUserInput();
eval(userCode);  // Dangerous!
"""
        result = await analyzer.run(code=code, language="javascript", checks=["security"])

        # Should detect eval in JavaScript
        security_issues = [i for i in result["issues"] if i["rule"] == "security-vulnerability"]
        assert len(security_issues) > 0

    @pytest.mark.asyncio
    async def test_complexity_check(self, analyzer):
        """Test complexity check detects high complexity."""
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                for i in range(x):
                    while i > 0:
                        if i % 2 == 0:
                            return i
                        i -= 1
    return 0
"""
        result = await analyzer.run(code=code, language="python", checks=["complexity"])

        # Should detect high complexity
        complexity_issues = [i for i in result["issues"] if i["rule"] == "high-complexity"]
        assert len(complexity_issues) > 0

    @pytest.mark.asyncio
    async def test_all_checks_combined(self, analyzer):
        """Test running all checks together."""
        code = """
def process_data(data):
    result = eval(data)  # Security issue
    if result > 0:
        if result > 10:
            if result > 20:
                print("High complexity here with a very long line that exceeds normal limits")  
    return result
"""
        result = await analyzer.run(code=code, language="python", checks=["syntax", "style", "complexity", "security"])

        assert "issues" in result
        assert "summary" in result
        assert "metrics" in result

        # Should have multiple types of issues
        assert result["summary"]["total_issues"] > 0

        # Check metrics
        assert result["metrics"]["total_lines"] > 0
        assert result["metrics"]["code_lines"] > 0

    @pytest.mark.asyncio
    async def test_severity_filter(self, analyzer):
        """Test severity filtering."""
        code = """
x=1  
eval(user_input)
"""
        # Get all issues
        result_all = await analyzer.run(code=code, language="python", severity_filter="info")

        # Get only errors
        result_errors = await analyzer.run(code=code, language="python", severity_filter="error")

        # Should have fewer issues with error filter
        assert result_errors["summary"]["total_issues"] <= result_all["summary"]["total_issues"]

        # All returned issues should be errors
        for issue in result_errors["issues"]:
            assert issue["severity"] == "error"

    @pytest.mark.asyncio
    async def test_metrics_calculation(self, analyzer):
        """Test code metrics are calculated correctly."""
        code = """# This is a comment
def foo():
    pass

# Another comment
x = 1
"""
        result = await analyzer.run(code=code, language="python")

        metrics = result["metrics"]
        assert metrics["total_lines"] == 7  # 7 lines total (6 + trailing newline split)
        assert metrics["comment_lines"] == 2
        assert metrics["blank_lines"] >= 1
        assert metrics["code_lines"] >= 2

    @pytest.mark.asyncio
    async def test_langchain_conversion(self, analyzer):
        """Test LangChain tool conversion."""
        try:
            from langchain_core.tools import StructuredTool

            lc_tool = analyzer.to_langchain_tool()
            assert isinstance(lc_tool, StructuredTool)
            assert lc_tool.name == "code-analysis"
        except ImportError:
            pytest.skip("LangChain not installed")
