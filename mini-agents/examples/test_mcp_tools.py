import asyncio
import sys
from pathlib import Path
from Mini_Agents.tools.mcp_loader import load_mcp_tools_async, cleanup_mcp_connections, set_mcp_timeout_config


async def main():
    print("=" * 60)
    print("Testing Mini_Agents MCP Tools")
    print("=" * 60)

    print("\n" + "-" * 60)
    print("Test 1: Load MCP tools from config")
    print("-" * 60)

    print("\nLoading MCP tools from mcp.json...")
    config_path = Path(__file__).parent.parent / "Mini_Agents" / "config" / "mcp.json"
    tools = await load_mcp_tools_async(str(config_path))

    print(f"\n✓ Loaded {len(tools)} MCP tools")

    if tools:
        print("\nAvailable MCP tools:")
        for tool in tools:
            print(f"\n  Tool: {tool.name}")
            print(f"  Description: {tool.description}")
            print(f"  Parameters: {tool.parameters}")

    print("\n" + "-" * 60)
    print("Test 2: Test MCP tool execution (if tools available)")
    print("-" * 60)

    if tools:
        print(f"\nTesting first available tool: {tools[0].name}")
        
        try:
            result = await tools[0].execute()
            print(f"\n✓ Tool executed")
            print(f"Success: {result.success}")
            print(f"Content: {result.content}")
            if result.error:
                print(f"Error: {result.error}")
        except Exception as e:
            print(f"\n✗ Tool execution failed: {e}")
    else:
        print("\nNo MCP tools available for testing")

    print("\n" + "-" * 60)
    print("Test 3: Test timeout configuration")
    print("-" * 60)

    print("\nSetting custom timeout configuration...")
    set_mcp_timeout_config(
        connect_timeout=15.0,
        execute_timeout=90.0,
        sse_read_timeout=150.0
    )
    print("✓ Timeout configuration updated")

    from Mini_Agents.tools.mcp_loader import get_mcp_timeout_config
    config = get_mcp_timeout_config()
    print(f"  Connect timeout: {config.connect_timeout}s")
    print(f"  Execute timeout: {config.execute_timeout}s")
    print(f"  SSE read timeout: {config.sse_read_timeout}s")

    print("\n" + "-" * 60)
    print("Test 4: Test MCP tool with parameters")
    print("-" * 60)

    if len(tools) > 0:
        print(f"\nTesting tool with parameters: {tools[0].name}")
        
        try:
            result = await tools[0].execute(query="test search")
            print(f"\n✓ Tool executed with parameters")
            print(f"Success: {result.success}")
            print(f"Content: {result.content}")
            if result.error:
                print(f"Error: {result.error}")
        except Exception as e:
            print(f"\n✗ Tool execution with parameters failed: {e}")

    print("\n" + "-" * 60)
    print("Test 5: Test cleanup")
    print("-" * 60)

    print("\nCleaning up MCP connections...")
    await cleanup_mcp_connections()
    print("✓ MCP connections cleaned up")

    print("\n" + "=" * 60)
    print("✅ All MCP Tools tests completed!")
    print("=" * 60)

    print("\nNote: MCP tools allow you to:")
    print("  - Load tools from remote MCP servers")
    print("  - Execute tools with timeout protection")
    print("  - Configure custom timeouts per server")
    print("  - Support STDIO, SSE, and HTTP connections")


if __name__ == "__main__":
    asyncio.run(main())
