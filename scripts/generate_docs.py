#!/usr/bin/env python3
"""Automated documentation generator for API endpoints and configuration.

Generates markdown documentation from code analysis, configuration files,
and inline documentation to keep docs in sync with implementation.
"""

import ast
import json
from pathlib import Path
from typing import Any


class APIDocumentationGenerator:
    """Generator for API endpoint documentation."""

    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.endpoints: list[dict[str, Any]] = []

    def analyze_fastapi_routes(self, app_file: Path) -> list[dict[str, Any]]:
        """Analyze FastAPI routes from the application file."""
        endpoints = []

        try:
            with open(app_file, encoding="utf-8") as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Look for FastAPI route decorators
                    for decorator in node.decorator_list:
                        if self._is_route_decorator(decorator):
                            endpoint = self._extract_endpoint_info(node, decorator)
                            if endpoint:
                                endpoints.append(endpoint)

        except Exception as e:
            print(f"Error analyzing {app_file}: {e}")

        return endpoints

    def _is_route_decorator(self, decorator: ast.AST) -> bool:
        """Check if decorator is a FastAPI route decorator."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in ["get", "post", "put", "delete", "patch"]
        return False

    def _extract_endpoint_info(self, func_node: ast.FunctionDef, decorator: ast.Call) -> dict[str, Any] | None:
        """Extract endpoint information from function and decorator."""
        try:
            # Get HTTP method
            method = decorator.func.attr.upper() if isinstance(decorator.func, ast.Attribute) else "UNKNOWN"

            # Get path from first argument
            path = ""
            if decorator.args:
                if isinstance(decorator.args[0], ast.Constant):
                    path = decorator.args[0].value

            # Get docstring
            docstring = ast.get_docstring(func_node) or "No description available"

            # Extract parameters from function signature
            params = []
            for arg in func_node.args.args:
                if arg.arg != "self":  # Skip self parameter
                    params.append({"name": arg.arg, "type": self._get_type_annotation(arg.annotation)})

            return {
                "method": method,
                "path": path,
                "function_name": func_node.name,
                "description": docstring,
                "parameters": params,
                "summary": docstring.split("\n")[0] if docstring else "No summary",
            }

        except Exception as e:
            print(f"Error extracting endpoint info: {e}")
            return None

    def _get_type_annotation(self, annotation: ast.AST | None) -> str:
        """Extract type annotation as string."""
        if annotation is None:
            return "Any"

        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Attribute):
            return (
                f"{annotation.value.id}.{annotation.attr}" if hasattr(annotation.value, "id") else str(annotation.attr)
            )
        else:
            return "Any"

    def generate_api_docs(self) -> str:
        """Generate markdown documentation for API endpoints."""
        docs = ["# API Documentation\n"]
        docs.append("Auto-generated documentation for API endpoints.\n")
        docs.append("Generated from source analysis.\n\n")

        # Group endpoints by path prefix
        grouped_endpoints = {}
        for endpoint in self.endpoints:
            prefix = endpoint["path"].split("/")[1] if endpoint["path"].startswith("/") else "root"
            if prefix not in grouped_endpoints:
                grouped_endpoints[prefix] = []
            grouped_endpoints[prefix].append(endpoint)

        for group_name, group_endpoints in grouped_endpoints.items():
            docs.append(f"## {group_name.title()} Endpoints\n")

            for endpoint in group_endpoints:
                docs.append(f"### {endpoint['method']} {endpoint['path']}\n")
                docs.append(f"**Function:** `{endpoint['function_name']}`\n\n")
                docs.append(f"**Description:** {endpoint['summary']}\n\n")

                if endpoint["parameters"]:
                    docs.append("**Parameters:**\n")
                    for param in endpoint["parameters"]:
                        docs.append(f"- `{param['name']}` ({param['type']})\n")
                    docs.append("\n")

                if len(endpoint["description"]) > len(endpoint["summary"]):
                    docs.append("**Details:**\n")
                    docs.append(f"{endpoint['description']}\n\n")

                docs.append("---\n\n")

        return "".join(docs)

    def analyze_configuration(self, config_files: list[Path]) -> dict[str, Any]:
        """Analyze configuration files and extract documentation."""
        config_docs = {}

        for config_file in config_files:
            try:
                if config_file.suffix == ".py":
                    config_docs[config_file.name] = self._analyze_python_config(config_file)
                elif config_file.suffix in [".yaml", ".yml"]:
                    config_docs[config_file.name] = self._analyze_yaml_config(config_file)
                elif config_file.suffix == ".toml":
                    config_docs[config_file.name] = self._analyze_toml_config(config_file)

            except Exception as e:
                print(f"Error analyzing config file {config_file}: {e}")

        return config_docs

    def _analyze_python_config(self, config_file: Path) -> dict[str, Any]:
        """Analyze Python configuration file."""
        with open(config_file, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        config_items = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        value = self._get_literal_value(node.value)
                        config_items.append(
                            {
                                "name": target.id,
                                "value": value,
                                "type": type(value).__name__ if value is not None else "Unknown",
                            }
                        )

        return {"type": "python", "items": config_items}

    def _analyze_yaml_config(self, config_file: Path) -> dict[str, Any]:
        """Analyze YAML configuration file."""
        try:
            import yaml

            with open(config_file, encoding="utf-8") as f:
                content = yaml.safe_load(f)
            return {"type": "yaml", "content": content}
        except ImportError:
            return {"type": "yaml", "error": "PyYAML not available"}

    def _analyze_toml_config(self, config_file: Path) -> dict[str, Any]:
        """Analyze TOML configuration file."""
        try:
            import tomllib

            with open(config_file, "rb") as f:
                content = tomllib.load(f)
            return {"type": "toml", "content": content}
        except ImportError:
            return {"type": "toml", "error": "tomllib not available"}

    def _get_literal_value(self, node: ast.AST) -> Any:
        """Extract literal value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._get_literal_value(item) for item in node.elts]
        elif isinstance(node, ast.Dict):
            result = {}
            for key, value in zip(node.keys, node.values):
                key_val = self._get_literal_value(key)
                val_val = self._get_literal_value(value)
                if key_val is not None:
                    result[key_val] = val_val
            return result
        else:
            return None

    def generate_config_docs(self, config_docs: dict[str, Any]) -> str:
        """Generate configuration documentation."""
        docs = ["# Configuration Reference\n"]
        docs.append("Auto-generated documentation for configuration files.\n\n")

        for filename, config_info in config_docs.items():
            docs.append(f"## {filename}\n")
            docs.append(f"**Type:** {config_info['type'].upper()}\n\n")

            if "error" in config_info:
                docs.append(f"**Error:** {config_info['error']}\n\n")
                continue

            if config_info["type"] == "python":
                docs.append("| Setting | Value | Type |\n")
                docs.append("|---------|-------|------|\n")
                for item in config_info["items"]:
                    value_str = str(item["value"])[:50] + "..." if len(str(item["value"])) > 50 else str(item["value"])
                    docs.append(f"| `{item['name']}` | `{value_str}` | {item['type']} |\n")
                docs.append("\n")
            else:
                docs.append("```yaml\n")
                docs.append(json.dumps(config_info["content"], indent=2))
                docs.append("\n```\n\n")

        return "".join(docs)

    def run(self) -> None:
        """Run the documentation generation process."""
        print("🔍 Analyzing API endpoints...")

        # Find FastAPI app files
        app_files = list(self.source_dir.glob("**/app.py"))
        app_files.extend(list(self.source_dir.glob("**/main.py")))

        for app_file in app_files:
            endpoints = self.analyze_fastapi_routes(app_file)
            self.endpoints.extend(endpoints)

        print(f"Found {len(self.endpoints)} API endpoints")

        # Generate API documentation
        api_docs = self.generate_api_docs()
        api_output = self.output_dir / "api_reference.md"
        api_output.parent.mkdir(parents=True, exist_ok=True)

        with open(api_output, "w", encoding="utf-8") as f:
            f.write(api_docs)
        print(f"📝 Generated API docs: {api_output}")

        # Analyze configuration files
        print("🔍 Analyzing configuration files...")
        config_files = list(self.source_dir.parent.glob("*.toml"))
        config_files.extend(list(self.source_dir.parent.glob("config/*.yaml")))
        config_files.extend(list(self.source_dir.glob("**/settings.py")))

        config_docs = self.analyze_configuration(config_files)
        config_doc_content = self.generate_config_docs(config_docs)

        config_output = self.output_dir / "configuration_reference.md"
        with open(config_output, "w", encoding="utf-8") as f:
            f.write(config_doc_content)
        print(f"📝 Generated config docs: {config_output}")


def main():
    """Main entry point for documentation generation."""
    source_dir = Path("src")
    output_dir = Path("docs/generated")

    generator = APIDocumentationGenerator(source_dir, output_dir)
    generator.run()

    print("✅ Documentation generation completed!")


if __name__ == "__main__":
    main()
