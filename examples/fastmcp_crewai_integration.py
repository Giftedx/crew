"""FastMCP 2.0 + CrewAI Integration Examples.

This module demonstrates how to use the enhanced FastMCP-CrewAI integration,
showcasing bidirectional workflows between MCP servers and CrewAI crews.
"""

import asyncio
import json
import os


# Example 1: Using FastMCP Client from CrewAI Agent
def example_crewai_agent_calls_mcp_server():
    """Example: CrewAI agent calling external MCP server using FastMCP client."""

    from ultimate_discord_intelligence_bot.tools import FastMCPClientTool

    # Initialize the FastMCP client tool
    mcp_client = FastMCPClientTool()

    # Example 1: Call documentation search on FastMCP docs server
    result = mcp_client.run(
        server_url="https://gofastmcp.com/mcp",
        tool_name="SearchFastMcp",
        arguments={"query": "CrewAI integration patterns"},
    )

    print("MCP Server Call Result:")
    print(json.dumps(result.to_dict(), indent=2))

    # Example 2: Call local MCP server
    local_result = mcp_client.run(
        server_url="stdio://crew_mcp",  # Local server
        tool_name="health_check",
        arguments={},
    )

    print("\nLocal MCP Server Health:")
    print(json.dumps(local_result.to_dict(), indent=2))


# Example 2: External MCP Client calling CrewAI via MCP
async def example_external_client_calls_crewai():
    """Example: External MCP client controlling CrewAI crews."""

    try:
        from fastmcp import Client

        # Connect to our CrewAI MCP server
        async with Client("stdio://crew_mcp") as client:
            # 1. List available crews
            crews_result = await client.call_tool(
                name="crewai_list_available_crews", arguments={}
            )
            print("Available CrewAI Crews:")
            print(json.dumps(crews_result, indent=2))

            # 2. Get crew status
            status_result = await client.call_tool(
                name="crewai_get_crew_status", arguments={}
            )
            print("\nCrewAI Status:")
            print(json.dumps(status_result, indent=2))

            # 3. Execute a crew (if enabled)
            execution_result = await client.call_tool(
                name="crewai_execute_crew",
                arguments={
                    "inputs": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                    "crew_type": "default",
                },
            )
            print("\nCrew Execution Result:")
            print(json.dumps(execution_result, indent=2))

            # 4. Read crew resources
            agents_resource = await client.read_resource("crewai://agents")
            print("\nCrewAI Agents Resource:")
            print(agents_resource)

    except ImportError:
        print("FastMCP client not available. Install with: pip install fastmcp")
    except Exception as e:
        print(f"Example failed: {e}")


# Example 3: Hybrid MCP-CrewAI Workflow
def example_hybrid_workflow():
    """Example: Complex workflow combining MCP servers and CrewAI crews."""

    from ultimate_discord_intelligence_bot.tools import FastMCPClientTool, MCPCallTool

    # Initialize tools
    external_mcp = FastMCPClientTool()
    internal_mcp = MCPCallTool()

    print("=== Hybrid MCP-CrewAI Workflow Example ===\n")

    # Step 1: Use MCP server for initial data gathering
    print("Step 1: Gathering data via MCP HTTP server...")
    http_result = internal_mcp.run(
        namespace="http",
        name="http_json_get",
        params={"url": "https://api.github.com/repos/fastmcp/fastmcp/releases/latest"},
    )

    if http_result.ok:
        print("✅ Successfully gathered data from GitHub API")
        release_data = http_result.data.get("result", {})
        print(f"Latest FastMCP release: {release_data.get('name', 'Unknown')}")
    else:
        print("❌ Failed to gather data via MCP HTTP server")
        release_data = {}

    # Step 2: Process data through CrewAI crew
    print("\nStep 2: Processing via CrewAI crew...")
    try:
        # This would typically be a real crew execution
        # For demo, we'll simulate the crew analysis
        crew_inputs = {
            "url": "https://github.com/fastmcp/fastmcp",
            "context": f"Analyzing FastMCP release: {release_data.get('name', 'Unknown')}",
        }

        print("✅ CrewAI crew would process the GitHub data here")
        print(f"Crew inputs: {json.dumps(crew_inputs, indent=2)}")

    except Exception as e:
        print(f"❌ CrewAI processing failed: {e}")

    # Step 3: Store results via MCP memory server
    print("\nStep 3: Storing results via MCP memory server...")
    memory_result = internal_mcp.run(
        namespace="memory",
        name="vs_search",
        params={
            "tenant": "demo",
            "workspace": "fastmcp_analysis",
            "name": "releases",
            "query": "FastMCP integration patterns",
            "k": 5,
        },
    )

    if memory_result.ok:
        print("✅ Successfully queried memory store")
        results = memory_result.data.get("result", {})
        print(f"Found {len(results.get('results', []))} relevant memories")
    else:
        print("❌ Memory query failed - this is expected without data")

    # Step 4: Generate summary via external MCP server
    print("\nStep 4: Generating summary via external MCP...")
    try:
        summary_result = external_mcp.run(
            server_url="https://gofastmcp.com/mcp",
            tool_name="SearchFastMcp",
            arguments={"query": "FastMCP CrewAI integration best practices"},
        )

        if summary_result.ok:
            print("✅ Successfully gathered external documentation")
        else:
            print("❌ External MCP call failed")

    except Exception as e:
        print(f"External MCP call error: {e}")

    print("\n=== Workflow Complete ===")
    print("This example demonstrates:")
    print("1. 🔄 MCP servers for data input/output")
    print("2. 🤖 CrewAI crews for intelligent processing")
    print("3. 💾 Memory integration for persistence")
    print("4. 🌐 External MCP servers for additional capabilities")


# Example 4: Configuration and Setup
def example_setup_and_configuration():
    """Example: How to configure FastMCP-CrewAI integration."""

    print("=== FastMCP-CrewAI Configuration Example ===\n")

    # 1. Environment Variables
    print("1. Required Environment Variables:")
    env_vars = {
        "ENABLE_MCP_CREWAI": "1",  # Enable CrewAI MCP server
        "ENABLE_MCP_CREWAI_EXECUTION": "1",  # Enable crew execution via MCP
        "ENABLE_MCP_MEMORY": "1",  # Enable memory server
        "ENABLE_MCP_HTTP": "1",  # Enable HTTP server
        "ENABLE_MCP_ROUTER": "1",  # Enable routing server
        "MCP_HTTP_ALLOWLIST": "api.github.com,gofastmcp.com",  # Allowed hosts
        "CREW_MAX_RPM": "10",  # CrewAI rate limiting
        "CREW_EMBEDDER_PROVIDER": "openai",  # CrewAI embedder
    }

    for var, value in env_vars.items():
        current_value = os.getenv(var, "Not Set")
        status = "✅" if current_value != "Not Set" else "❌"
        print(f"  {status} {var}={value} (current: {current_value})")

    # 2. MCP Client Configuration (Claude Desktop)
    print("\n2. Claude Desktop Configuration (~/.claude/config.json):")
    claude_config = {
        "mcpServers": {
            "crew": {
                "command": "crew_mcp",
                "env": {
                    "ENABLE_MCP_CREWAI": "1",
                    "ENABLE_MCP_CREWAI_EXECUTION": "1",
                    "ENABLE_MCP_MEMORY": "1",
                    "ENABLE_MCP_HTTP": "1",
                    "ENABLE_MCP_ROUTER": "1",
                },
            }
        }
    }
    print(json.dumps(claude_config, indent=2))

    # 3. Running the MCP Server
    print("\n3. Running the Enhanced MCP Server:")
    print("   # Install with MCP support")
    print("   pip install -e '.[mcp]'")
    print()
    print("   # Run with all features enabled")
    print("   ENABLE_MCP_CREWAI=1 ENABLE_MCP_CREWAI_EXECUTION=1 crew_mcp")
    print()
    print("   # Or use the Makefile")
    print("   make run-mcp")

    # 4. Testing the Integration
    print("\n4. Testing the Integration:")
    print("   # Test MCP server health")
    print(
        "   python -c \"from mcp_server.server import mcp; print('MCP Server:', mcp.name)\""
    )
    print()
    print("   # Test CrewAI integration")
    print(
        "   python -c \"from mcp_server.crewai_server import crewai_mcp; print('CrewAI MCP:', crewai_mcp.name)\""
    )
    print()
    print("   # Test tool availability")
    print(
        "   python -c \"from ultimate_discord_intelligence_bot.tools import FastMCPClientTool; print('FastMCP Client available')\""
    )

    print("\n=== Configuration Complete ===")


# Main execution
if __name__ == "__main__":
    print("🚀 FastMCP 2.0 + CrewAI Integration Examples\n")

    # Run examples
    print("Example 1: CrewAI Agent → MCP Server")
    print("-" * 40)
    try:
        example_crewai_agent_calls_mcp_server()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    print("\n\nExample 2: External Client → CrewAI via MCP")
    print("-" * 40)
    try:
        asyncio.run(example_external_client_calls_crewai())
    except Exception as e:
        print(f"Example 2 failed: {e}")

    print("\n\nExample 3: Hybrid MCP-CrewAI Workflow")
    print("-" * 40)
    try:
        example_hybrid_workflow()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    print("\n\nExample 4: Configuration and Setup")
    print("-" * 40)
    try:
        example_setup_and_configuration()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    print("\n\n🎉 Examples completed!")
    print("\nNext steps:")
    print("1. Configure environment variables")
    print("2. Install FastMCP: pip install -e '.[mcp]'")
    print("3. Run MCP server: ENABLE_MCP_CREWAI=1 crew_mcp")
    print("4. Connect with Claude Desktop or other MCP clients")
    print("5. Explore hybrid MCP-CrewAI workflows")
