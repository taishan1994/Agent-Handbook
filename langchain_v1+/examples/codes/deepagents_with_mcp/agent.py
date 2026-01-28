import asyncio
import json
from langchain.agents import create_agent
from langchain.agents.middleware.todo import TodoListMiddleware
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from text_tool_calls_middleware import TextToolCallsMiddleware

system_prompt = """
你是一位研究专家，根据用户要求进行研究并撰写报告。

## 工作流程
1. 理解核心需求，识别关键要素
2. **必须使用 write_todos 工具制定任务规划**，明确待办事项
3. 逐步研究，记录发现，验证结论
4. 整体结果和审查，必要时重新制定解决链路
5. 输出详细研究报告
6. **重要：在输出最终答案前，必须调用 write_todos 将所有任务标记为 completed**

## 工具使用
- web_search: 网络搜索工具
- extract: 网页内容提取工具
- write_todos: **任务规划工具（必须使用）**

## 重要提示
- **开始任何任务前，必须先使用 write_todos 工具制定任务计划**
- **完成所有任务后，必须调用 write_todos 将所有任务标记为 completed**
- 对于复杂任务，使用 write_todos 工具来规划和跟踪进度
- 需要搜索信息时使用 web_search
- 需要提取网页内容时使用 extract
- 直接调用工具，不要在文本中描述

## 工具调用格式
使用以下格式调用工具：
[{{"name": "web_search", "arguments": {{"query": "搜索关键词", "max_results": 5}}}}]
"""


async def main():
    llm = init_chat_model(
        model="openai:/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507",
        base_url="http://192.168.16.44:11384/v1",
        api_key="none",
        temperature=0,
    )

    client = MultiServerMCPClient(
        connections={
            "web-search": {"url": "http://localhost:6030/sse", "transport": "sse"}
        }
    )
    
    print("正在连接 MCP 服务器...")
    tools = await client.get_tools()
    print(f"成功获取 {len(tools)} 个工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    print(f"\n创建 agent，模型类型: {type(llm)}")
    print(f"工具数量: {len(tools)}")
    
    text_tool_calls_middleware = TextToolCallsMiddleware()
    todo_list_middleware = TodoListMiddleware()
    
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[
            text_tool_calls_middleware,
            todo_list_middleware,
        ],
        debug=False
    )
    
    print("\n开始执行任务...\n")
    print("=" * 80)
    
    # 用于跟踪已执行的工具调用，避免重复显示
    executed_tool_calls = []
    
    # 用于检测工具调用的状态
    skip_tool_call = False
    tool_call_buffer = ""
    current_tool_call = ""
    
    try:
        async for event in agent.astream_events(
            input={
                "messages": [
                    {"role": "user", "content": "埃菲尔铁塔与最高建筑相比有多高？"}
                ]
            },
            version="v2",
            config={"recursion_limit": 50},  # 增加递归限制
        ):
            event_type = event["event"]
            
            if event_type == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # 检测工具调用的开始标记
                    if content == "<tool_call>":
                        skip_tool_call = True
                        current_tool_call = ""
                        continue
                    
                    # 如果在工具调用的状态，流式打印工具调用内容
                    if skip_tool_call:
                        current_tool_call += content
                        # 检测工具调用的结束标记
                        if content == "</tool_call>":
                            skip_tool_call = False
                            # 打印完整的工具调用
                            print(f"\n{'='*80}")
                            print(f"[工具调用]")
                            print(f"{'='*80}")
                            print(current_tool_call)
                            print(f"{'='*80}\n")
                            current_tool_call = ""
                        continue
                    
                    # 正常的LLM输出，流式打印
                    print(content, end="", flush=True)
            
            elif event_type == "on_chat_model_end":
                if "output" in event["data"]:
                    output = event["data"]["output"]
                    # 由于 LLM 输出已经在 on_chat_model_stream 中流式打印，这里不再重复打印
                    # 只保留工具调用的处理（但工具调用也在流式输出中处理了）
                    
                    # 由于工具调用已经在流式输出中打印，这里不再重复打印
                    # if hasattr(output, "tool_calls") and output.tool_calls:
                    #     ...
            
            elif event_type == "on_tool_start":
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                
                # 检查是否是 write_todos 工具
                if tool_name == "write_todos" and "todos" in tool_input:
                    todos = tool_input["todos"]
                    print(f"\n{'='*80}")
                    print(f"[Todo List 更新]")
                    print(f"{'='*80}")
                    for i, todo in enumerate(todos, 1):
                        status = todo.get("status", "pending")
                        content = todo.get("content", "")
                        
                        status_display = {
                            "pending": "⏳ pending",
                            "in_progress": "🔄 in_progress",
                            "completed": "✅ completed"
                        }.get(status, f"❓ {status}")
                        
                        print(f"  {i}. {content}")
                        print(f"     状态: {status_display}")
                        print()
                else:
                    # 检查是否已经执行过这个工具调用
                    tool_key = f"{tool_name}_{str(tool_input)}"
                    if tool_key not in executed_tool_calls:
                        executed_tool_calls.append(tool_key)
                        print(f"\n{'='*80}")
                        print(f"[工具执行: {tool_name}]")
                        print(f"{'='*80}")
            
            elif event_type == "on_tool_end":
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                
                # 只显示非 write_todos 工具的完成信息，并且只显示一次
                if tool_name != "write_todos":
                    tool_key = f"{tool_name}_{str(tool_input)}"
                    if tool_key in executed_tool_calls:
                        print(f"\n{'='*80}")
                        print(f"[工具执行完成: {tool_name}]")
                        print(f"{'='*80}")
                        print(f"  ✅ 工具已成功执行")
                        # 从列表中移除，避免重复显示完成信息
                        if tool_key in executed_tool_calls:
                            executed_tool_calls.remove(tool_key)
        
        print("\n" + "=" * 80)
        print("\n任务完成！")
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
