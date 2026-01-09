import asyncio
import json
import tempfile
from pathlib import Path
from Mini_Agents import Tool, ToolResult, LLMClient, Message
from Mini_Agents.tools.mcp_loader import load_mcp_tools_async, cleanup_mcp_connections, set_mcp_timeout_config
from Mini_Agents.tools.mcp_loader import get_mcp_timeout_config

def extract_tool_calls_from_content(content: str):
    """
    Extract tool calls from content string.
    This handles cases where the API doesn't support structured tool calls
    and returns tool calls as JSON in the content.
    """
    tool_calls = []
    
    # Try to find JSON objects in the content
    import re
    
    # Pattern to match JSON objects that look like tool calls
    pattern = r'\{[^{}]*"name"\s*:\s*"[^"]+"[^{}]*"arguments"\s*:\s*\{[^{}]*\}[^{}]*\}'
    
    matches = re.findall(pattern, content)
    
    for i, match in enumerate(matches):
        try:
            tool_call = json.loads(match)
            if "name" in tool_call and "arguments" in tool_call:
                tool_calls.append({
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tool_call["name"],
                        "arguments": tool_call["arguments"]
                    }
                })
        except json.JSONDecodeError:
            continue
    
    return tool_calls

async def main():
    print("=" * 60)
    print("Testing LLMClient with MCP Tools")
    print("=" * 60)

    workspace = Path(tempfile.mkdtemp())
    print(f"\n✓ Workspace created: {workspace}")

    print("\n" + "-" * 60)
    print("Test 1: Load MCP tools")
    print("-" * 60)

    config_path = Path(__file__).parent.parent / "Mini_Agents" / "config" / "mcp.json"
    print(f"\nLoading MCP tools from config: {config_path}")
    
    mcp_tools = await load_mcp_tools_async(str(config_path))

    client = LLMClient(
        api_key="test-key",
        api_base="http://192.168.16.14:18000/v1",
        provider="openai",
        model="/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507",
    )


    set_mcp_timeout_config(
        connect_timeout=15.0,
        execute_timeout=90.0,
        sse_read_timeout=150.0
    )

    config = get_mcp_timeout_config()

    messages = [Message(role="user", content="目前中国最好的大语言模型是哪一个？")]
    response = await client.generate(messages, tools=mcp_tools)

    print(f"\nLLM Response:")
    print(f"  Content: {response.content}")
    print(f"  Tool Calls: {response.tool_calls}")
    print(f"  Finish Reason: {response.finish_reason}")

    tool_calls = response.tool_calls if response.tool_calls else extract_tool_calls_from_content(response.content)

    if tool_calls:
        print(f"\nLLM decided to use {len(tool_calls)} tool(s):")
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]
            else:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
            print(f"  - {tool_name}: {tool_args}")

        messages.append(Message(role="assistant", content=response.content, tool_calls=tool_calls))

        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]
                tool_call_id = tool_call["id"]
            else:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                tool_call_id = tool_call.id

            tool = next((t for t in mcp_tools if t.name == tool_name), None)
            if tool:
                try:
                    result = await tool.execute(**tool_args)
                    print(f"\nTool '{tool_name}' result:")
                    print(f"  Success: {result.success}")
                    print(f"  Content: {result.content[:500]}..." if len(result.content) > 500 else f"  Content: {result.content}")
                    if result.error:
                        print(f"  Error: {result.error}")
                    messages.append(Message(role="tool", content=result.content, tool_call_id=tool_call_id))
                except Exception as e:
                    print(f"\nError executing tool '{tool_name}': {e}")
                    import traceback
                    traceback.print_exc()
                    error_content = f"Tool execution failed: {str(e)}"
                    messages.append(Message(role="tool", content=error_content, tool_call_id=tool_call_id))
            else:
                print(f"\nWarning: Tool '{tool_name}' not found in loaded tools")
                messages.append(Message(role="tool", content=f"Tool '{tool_name}' not found", tool_call_id=tool_call_id))

        final_response = await client.generate(messages, tools=mcp_tools)
        print(f"\nFinal response: {final_response.content}")

    await cleanup_mcp_connections()
 


if __name__ == "__main__":
    asyncio.run(main())
