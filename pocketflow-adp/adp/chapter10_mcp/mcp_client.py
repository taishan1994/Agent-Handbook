#!/usr/bin/env python3
"""
使用PocketFlow实现的MCP客户端
基于Chapter 10的示例，展示如何使用MCP进行文件系统交互和Web搜索
"""

import sys
import os
import yaml
import asyncio
from typing import List, Dict, Any, Optional

# 添加PocketFlow路径
sys.path.append('/nfs/FM/gongoubo/new_project/Agent-Handbook/pocketflow-adp/PocketFlow')
sys.path.append('/nfs/FM/gongoubo/new_project/Agent-Handbook/pocketflow-adp/utils')

from pocketflow import Node, Flow
from utils import call_llm
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPUtils:
    """MCP工具类，用于与MCP服务器交互"""
    
    @staticmethod
    async def get_tools(server_script_path: str) -> List[Any]:
        """获取MCP服务器提供的工具"""
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                return tools_response.tools
    
    @staticmethod
    async def call_tool(server_script_path: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用MCP服务器上的工具"""
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text
    
    @classmethod
    def sync_get_tools(cls, server_script_path: str) -> List[Any]:
        """同步获取工具"""
        return asyncio.run(cls.get_tools(server_script_path))
    
    @classmethod
    def sync_call_tool(cls, server_script_path: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """同步调用工具"""
        return asyncio.run(cls.call_tool(server_script_path, tool_name, arguments))


class GetToolsNode(Node):
    """获取可用工具节点"""
    
    def prep(self, shared):
        """准备参数"""
        return shared.get("server_path", "mcp_server.py")
    
    def exec(self, server_path):
        """执行获取工具"""
        print("🔍 获取可用工具...")
        tools = MCPUtils.sync_get_tools(server_path)
        return tools
    
    def post(self, shared, prep_res, exec_res):
        """后处理，存储工具信息"""
        tools = exec_res
        shared["tools"] = tools
        
        # 格式化工具信息
        tool_info = []
        for i, tool in enumerate(tools, 1):
            properties = tool.inputSchema.get('properties', {})
            required = tool.inputSchema.get('required', [])
            
            params = []
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'unknown')
                req_status = "(必需)" if param_name in required else "(可选)"
                params.append(f"    - {param_name} ({param_type}): {req_status}")
            
            tool_info.append(f"[{i}] {tool.name}\n  描述: {tool.description}\n  参数:\n" + "\n".join(params))
        
        shared["tool_info"] = "\n".join(tool_info)
        print("✅ 工具获取完成")
        return "decide"


class DecideToolNode(Node):
    """决策节点，决定使用哪个工具"""
    
    def prep(self, shared):
        """准备提示"""
        tool_info = shared["tool_info"]
        question = shared.get("question", "")
        
        prompt = f"""
### 上下文
你是一个可以通过模型上下文协议(MCP)使用工具的助手。

### 可用工具
{tool_info}

### 任务
分析用户的问题并选择合适的工具来回答: "{question}"

## 工具选择指南

当用户输入时，请按照以下规则选择工具：

1. **read_file** - 用户输入数字"1"或明确表示要读取文件内容
   - 用户输入数字"1"时，如果没有指定文件路径，请使用默认值"README.md"
   - 示例: "1", "读取文件", "查看文件内容"

2. **write_file** - 用户输入数字"2"或明确表示要写入文件
   - 用户输入数字"2"时，如果没有指定文件路径和内容，请使用默认值file_path="test.txt", content="这是测试内容"
   - 示例: "2", "写入文件", "创建文件"

3. **list_directory** - 用户输入数字"3"或明确表示要列出目录内容
   - 用户输入数字"3"时，如果没有指定目录路径，请使用默认值"."
   - 示例: "3", "列出目录", "查看文件夹"

4. **web_search** - 用户输入数字"4"或明确表示要进行网络搜索
   - 用户输入数字"4"时，如果没有指定搜索内容，请使用默认值"人工智能"
   - 示例: "4", "搜索", "网络搜索"

5. **analyze_file_content** - 用户输入数字"5"或明确表示要分析文件内容
   - 用户输入数字"5"时，如果没有指定文件路径和分析类型，请使用默认值file_path="README.md", analysis_type="summary"
   - 示例: "5", "分析文件", "文件分析"

## 重要提示
- 如果用户输入不明确，优先选择最可能匹配的工具
- 如果用户输入"1"但没有提供文件路径，使用默认值"README.md"
- 如果用户输入"2"但没有提供文件路径和内容，使用默认值file_path="test.txt", content="这是测试内容"
- 如果用户输入"3"但没有提供目录路径，使用默认值"."
- 如果用户输入"4"但没有提供搜索内容，使用默认值"人工智能"
- 如果用户输入"5"但没有提供文件路径和分析类型，使用默认值file_path="README.md", analysis_type="summary"

## 下一步行动
分析问题，提取任何参数，并决定使用哪个工具。
请按以下格式返回响应：

```yaml
thinking: |
    <你关于问题要求以及提取哪些数字或参数的逐步推理>
tool: <要使用的工具名称>
reason: <你选择这个工具的原因>
parameters:
    <参数名>: <参数值>
    <参数名>: <参数值>
```

重要提示:
1. 必须从上述可用工具中选择一个工具名称
2. 正确从问题中提取参数
3. 对多行字段使用适当的缩进(4个空格)
4. 对多行文本字段使用|字符
5. 如果用户只输入数字但没有提供文件路径，使用默认值或询问

注意：
- 工具名称必须是以下之一: read_file, write_file, list_directory, web_search, analyze_file_content
- 参数必须包含所选工具所需的所有参数
- 如果用户只输入数字，请使用相应的默认值
"""
        return prompt
    
    def exec(self, prompt):
        """执行LLM调用"""
        print("🤔 分析问题并决定使用哪个工具...")
        print("\n=== 发送给LLM的提示 ===")
        print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
        print("=== 提示结束 ===\n")
        
        response = call_llm(prompt)
        
        print("\n=== LLM的响应 ===")
        print(response[:1000] + "..." if len(response) > 1000 else response)
        print("=== 响应结束 ===\n")
        
        return response
    
    def post(self, shared, prep_res, exec_res):
        """解析决策并存储到共享上下文"""
        print("\n=== LLM原始响应 ===")
        print(exec_res)
        print("=== 响应结束 ===\n")
        
        try:
            # 检查响应中是否包含yaml代码块
            if "```yaml" not in exec_res:
                print(f"❌ LLM响应中未包含YAML代码块")
                print("原始响应:", exec_res)
                
                # 尝试从用户输入中提取工具选择
                question = shared.get("question", "")
                if question.strip() == "1":
                    shared["tool_name"] = "read_file"
                    shared["parameters"] = {"file_path": "README.md"}
                    print("💡 根据输入选择默认工具: read_file")
                elif question.strip() == "2":
                    shared["tool_name"] = "write_file"
                    shared["parameters"] = {"file_path": "test.txt", "content": "这是测试内容"}
                    print("💡 根据输入选择默认工具: write_file")
                elif question.strip() == "3":
                    shared["tool_name"] = "list_directory"
                    shared["parameters"] = {"path": "."}
                    print("💡 根据输入选择默认工具: list_directory")
                elif question.strip() == "4":
                    shared["tool_name"] = "web_search"
                    shared["parameters"] = {"query": "人工智能"}
                    print("💡 根据输入选择默认工具: web_search")
                elif question.strip() == "5":
                    shared["tool_name"] = "analyze_file_content"
                    shared["parameters"] = {"file_path": "README.md", "analysis_type": "summary"}
                    print("💡 根据输入选择默认工具: analyze_file_content")
                else:
                    shared["tool_name"] = None
                    shared["parameters"] = {}
                    return "interactive"  # 返回交互节点重新输入
                
                print(f"🔢 提取的参数: {shared['parameters']}")
                return "execute"
                
            yaml_str = exec_res.split("```yaml")[1].split("```")[0].strip()
            decision = yaml.safe_load(yaml_str)
            
            # 检查决策是否有效
            if not decision or "tool" not in decision or decision["tool"] is None:
                print(f"❌ LLM未选择有效工具")
                print("决策内容:", decision)
                shared["tool_name"] = None
                shared["parameters"] = {}
                return "interactive"  # 返回交互节点重新输入
            
            shared["tool_name"] = decision["tool"]
            shared["parameters"] = decision.get("parameters", {})
            shared["thinking"] = decision.get("thinking", "")
            
            print(f"💡 选择的工具: {decision['tool']}")
            print(f"🔢 提取的参数: {decision.get('parameters', {})}")
            
            return "execute"
        except Exception as e:
            print(f"❌ 解析LLM响应时出错: {e}")
            print("原始响应:", exec_res)
            shared["tool_name"] = None
            shared["parameters"] = {}
            return "interactive"  # 返回交互节点重新输入


class ExecuteToolNode(Node):
    """执行工具节点"""
    
    def prep(self, shared):
        """准备工具执行参数"""
        tool_name = shared.get("tool_name")
        parameters = shared.get("parameters", {})
        
        # 检查工具名称是否有效
        if not tool_name:
            print("❌ 没有选择有效工具，跳过执行")
            return None, None, None
            
        return shared.get("server_path", "mcp_server.py"), tool_name, parameters
    
    def exec(self, inputs):
        """执行工具"""
        server_path, tool_name, parameters = inputs
        
        # 检查输入是否有效
        if not tool_name:
            return "错误: 没有选择有效工具"
            
        # 特殊处理write_file工具，确保file_path不为空
        if tool_name == "write_file":
            if not parameters.get("file_path") or parameters.get("file_path", "").strip() == "":
                parameters["file_path"] = "test.txt"  # 设置默认文件路径
                print(f"⚠️ 检测到空文件路径，使用默认值: {parameters['file_path']}")
            
            if not parameters.get("content"):
                parameters["content"] = "这是测试内容"  # 设置默认内容
                print(f"⚠️ 检测到空内容，使用默认值")
            
        print(f"🔧 使用参数 {parameters} 执行工具 '{tool_name}'")
        try:
            result = MCPUtils.sync_call_tool(server_path, tool_name, parameters)
            return result
        except Exception as e:
            return f"执行工具时出错: {str(e)}"
    
    def post(self, shared, prep_res, exec_res):
        """后处理，存储结果"""
        shared["result"] = exec_res
        print(f"\n✅ 执行结果: {exec_res}")
        return "continue"


class InteractiveNode(Node):
    """交互节点，获取用户输入"""
    
    def prep(self, shared):
        """准备提示"""
        return shared.get("welcome_message", "欢迎使用MCP文件系统和Web搜索助手!")
    
    def exec(self, welcome_message):
        """获取用户输入"""
        print("\n" + "="*50)
        print(welcome_message)
        print("="*50)
        print("可用功能:")
        print("1. 读取文件内容")
        print("2. 写入内容到文件")
        print("3. 列出目录内容")
        print("4. Web搜索")
        print("5. 分析文件内容")
        print("输入'quit'退出程序")
        print("="*50)
        
        question = input("\n请输入您的问题或请求: ")
        return question
    
    def post(self, shared, prep_res, exec_res):
        """处理用户输入"""
        question = exec_res
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 再见!")
            return "end"
        
        shared["question"] = question
        return "get_tools"


class EndNode(Node):
    """结束节点，用于正确结束流程"""
    def prep(self, shared):
        return None
    
    def exec(self, prep_res):
        return None
    
    def post(self, shared, prep_res, exec_res):
        return None

class ContinueNode(Node):
    """继续节点，询问用户是否继续"""
    
    def prep(self, shared):
        """准备参数"""
        return shared.get("result", "")
    
    def exec(self, result):
        """询问用户是否继续"""
        print("\n" + "-"*50)
        choice = input("是否继续? (y/n): ").lower()
        return choice
    
    def post(self, shared, prep_res, exec_res):
        """处理用户选择"""
        choice = exec_res
        
        if choice in ['y', 'yes']:
            return "interactive"
        else:
            print("👋 再见!")
            return "end"


def create_flow():
    """创建MCP工作流"""
    # 创建节点
    interactive_node = InteractiveNode()
    get_tools_node = GetToolsNode()
    decide_node = DecideToolNode()
    execute_node = ExecuteToolNode()
    continue_node = ContinueNode()
    end_node = EndNode()
    
    # 连接节点
    interactive_node - "get_tools" >> get_tools_node
    get_tools_node - "decide" >> decide_node
    decide_node - "execute" >> execute_node
    execute_node - "continue" >> continue_node
    continue_node - "interactive" >> interactive_node
    continue_node - "end" >> end_node
    execute_node - "interactive" >> interactive_node  # 如果执行失败也回到交互节点
    
    # 创建工作流
    return Flow(start=interactive_node)


def main():
    """主函数"""
    print("🚀 启动MCP文件系统和Web搜索助手")
    
    # 创建工作流
    flow = create_flow()
    
    # 初始化共享上下文
    shared = {
        "server_path": "/nfs/FM/gongoubo/new_project/Agent-Handbook/pocketflow-adp/adp/chapter10_mcp/mcp_server.py",
        "welcome_message": "欢迎使用MCP文件系统和Web搜索助手!"
    }
    
    # 运行工作流
    try:
        flow.run(shared)
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断，再见!")
    except Exception as e:
        print(f"\n❌ 运行时出错: {e}")


if __name__ == "__main__":
    main()