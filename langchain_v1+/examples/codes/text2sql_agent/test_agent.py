"""测试Text2SQL Agent的基本功能。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../deepagents_with_mcp"))

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain.chat_models import init_chat_model
from text_tool_calls_middleware import TextToolCallsMiddleware


def test_basic_queries():
    """测试基本的数据库查询功能。"""
    print("=" * 80)
    print("测试Text2SQL Agent - 基本查询功能")
    print("=" * 80)
    print()

    # 初始化模型
    print("正在初始化模型...")
    model = init_chat_model(
        model="openai:/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507",
        base_url="http://192.168.16.2:11384/v1",
        api_key="none",
        temperature=0,
    )
    print(f"模型初始化完成: {type(model)}")
    print()

    # 导入数据库工具
    print("正在加载数据库工具...")
    from db_tools import execute_sql, get_table_schema, list_tables, get_sample_data
    tools = [execute_sql, get_table_schema, list_tables, get_sample_data]
    print(f"数据库工具加载完成: {len(tools)} 个工具")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    print()

    # 创建agent
    print("正在创建Agent...")
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt="""你是一个专业的数据库查询助手，专门帮助用户查询和分析Chinook数据库。

## 你的职责
1. 理解用户的自然语言查询需求
2. 使用SQL技能生成正确的SQL查询语句
3. 执行查询并获取结果
4. 以清晰易懂的方式解释查询结果

## 工作流程
1. 理解用户需求，识别需要查询的表和字段
2. 如果不确定表结构，使用 get_table_schema 或 list_tables 工具查看
3. 使用 execute_sql 工具执行SQL查询
4. 分析查询结果，用自然语言向用户解释

## 重要提示
- 始终使用SQL技能中的最佳实践
- 对于复杂查询，先查看相关表的结构
- 使用LIMIT限制结果数量，避免返回过多数据
- 在解释结果时，提供数据洞察和分析
- 如果查询结果为空，说明可能的原因

## 可用工具
- execute_sql: 执行SQL查询
- get_table_schema: 获取表结构
- list_tables: 列出所有表
- get_sample_data: 获取表的样本数据
""",
        skills=["/skills/query-writing/", "/skills/schema-exploration/"],
        backend=FilesystemBackend(
            root_dir=os.path.join(os.path.dirname(__file__)),
            virtual_mode=False
        ),
        middleware=[TextToolCallsMiddleware()],
        debug=False,
    )
    print("Agent创建完成!")
    print()

    # 测试查询
    test_queries = [
        "列出所有的艺术家",
        "查询有多少个专辑",
        "查询最贵的5首歌曲",
        "查询每个客户的消费总额，按消费金额降序排列，只显示前10名",
    ]

    for i, query in enumerate(test_queries, 1):
        print("=" * 80)
        print(f"测试查询 {i}: {query}")
        print("=" * 80)
        
        try:
            result = agent.invoke({
                "messages": [
                    {"role": "user", "content": query}
                ]
            })
            
            print("\n执行过程:")
            print("=" * 80)
            
            messages = result.get("messages", [])
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                
                if msg_type == "HumanMessage":
                    print(f"\n👤 用户输入:")
                    print(f"   {msg.content}")
                
                elif msg_type == "AIMessage":
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        print(f"\n🤖 AI 调用工具:")
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get("name", "unknown")
                            tool_args = tool_call.get("args", {})
                            print(f"   工具: {tool_name}")
                            print(f"   参数: {tool_args}")
                    elif msg.content:
                        print(f"\n🤖 AI 回复:")
                        print(f"   {msg.content}")
                
                elif msg_type == "ToolMessage":
                    tool_name = msg.name if hasattr(msg, 'name') else "unknown"
                    print(f"\n🔧 工具执行结果 [{tool_name}]:")
                    content = msg.content
                    if isinstance(content, str) and len(content) > 500:
                        print(f"   {content[:500]}...")
                    else:
                        print(f"   {content}")
            
            print("\n" + "=" * 80)
            print()
            
        except Exception as e:
            print(f"错误: {str(e)}")
            print()
    
    print("=" * 80)
    print("测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    test_basic_queries()
