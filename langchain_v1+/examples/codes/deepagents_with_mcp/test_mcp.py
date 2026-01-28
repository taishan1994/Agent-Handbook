import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


async def test_mcp_connection():
    """测试 MCP 服务器连接和工具调用"""
    print("正在连接 MCP 服务器...")
    
    client = MultiServerMCPClient(
        connections={
            "web-search": {"url": "http://localhost:6030/sse", "transport": "sse"}
        }
    )
    
    try:
        # 获取工具
        tools = await client.get_tools()
        print(f"\n成功获取 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # 测试调用 web_search 工具
        print("\n正在测试 web_search 工具...")
        web_search_tool = None
        for tool in tools:
            if tool.name == "web_search":
                web_search_tool = tool
                break
        
        if web_search_tool:
            print(f"工具参数: {web_search_tool.args_schema}")
            result = await web_search_tool.ainvoke(
                {"query": "test", "max_results": 2}
            )
            print(f"\n工具调用结果:")
            print(result)
        else:
            print("错误: 未找到 web_search 工具")
            
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
