"""自定义中间件：解析文本格式的工具调用并转换为结构化工具调用"""

import json
import re
from typing import Any

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime
from langgraph.types import Overwrite


class TextToolCallsMiddleware(AgentMiddleware):
    """中间件：解析文本格式的工具调用并转换为结构化工具调用"""

    name = "text_tool_calls"

    def after_model(self, state: AgentState, runtime: Runtime[Any]) -> dict[str, Any] | None:  # noqa: ARG002
        """在模型调用后，检查并转换文本格式的工具调用"""
        messages = state["messages"]
        if not messages:
            return None

        last_message = messages[-1]
        
        # 只处理 AIMessage
        if not isinstance(last_message, AIMessage):
            return None
        
        # 如果已经有结构化的 tool_calls，不需要处理
        if last_message.tool_calls:
            return None
        
        # 检查 content 中是否包含工具调用
        content = last_message.content
        if not content:
            return None
        
        # 尝试解析工具调用
        tool_calls = self._parse_tool_calls(content)
        
        if not tool_calls:
            return None
        
        # 去重：检查是否有重复的工具调用（相同的 name 和 arguments）
        unique_tool_calls = []
        seen = set()
        for tool_call in tool_calls:
            # 创建唯一标识符：name + arguments 的字符串表示
            key = (tool_call["name"], json.dumps(tool_call["args"], sort_keys=True))
            if key not in seen:
                seen.add(key)
                unique_tool_calls.append(tool_call)
            else:
                # 打印去重信息（调试用）
                print(f"[去重] 移除重复的工具调用: {tool_call['name']}")
        
        if not unique_tool_calls:
            return None
        
        # 创建新的 AIMessage，包含结构化的 tool_calls
        new_message = AIMessage(
            content=content,
            tool_calls=unique_tool_calls,
            additional_kwargs=last_message.additional_kwargs,
            response_metadata=last_message.response_metadata,
            id=last_message.id,
        )
        
        # 替换最后一条消息
        new_messages = list(messages[:-1]) + [new_message]
        
        return {"messages": Overwrite(new_messages)}
    
    def _parse_tool_calls(self, content: str) -> list[dict[str, Any]]:
        """从文本内容中解析工具调用"""
        tool_calls = []
        
        # 模式1: JSON 数组格式 [{"name": "...", "arguments": {...}}, ...]
        # 查找所有可能的 JSON 数组
        json_start = content.find('[')
        if json_start != -1:
            # 尝试从找到的 [ 开始解析 JSON
            try:
                # 找到匹配的 ]
                bracket_count = 0
                json_end = json_start
                for i in range(json_start, len(content)):
                    if content[i] == '[':
                        bracket_count += 1
                    elif content[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_end = i + 1
                            break
                
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        if isinstance(item, dict) and "name" in item and "arguments" in item:
                            tool_calls.append({
                                "id": f"call_{i}",
                                "name": item["name"],
                                "args": item["arguments"]
                            })
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        
        # 模式2: 单个 JSON 对象格式 {"name": "...", "arguments": {...}}
        if not tool_calls:
            json_start = content.find('{')
            if json_start != -1:
                try:
                    # 找到匹配的 }
                    bracket_count = 0
                    json_end = json_start
                    for i in range(json_start, len(content)):
                        if content[i] == '{':
                            bracket_count += 1
                        elif content[i] == '}':
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_end = i + 1
                                break
                    
                    json_str = content[json_start:json_end]
                    data = json.loads(json_str)
                    
                    if isinstance(data, dict) and "name" in data and "arguments" in data:
                        tool_calls.append({
                            "id": f"call_0",
                            "name": data["name"],
                            "args": data["arguments"]
                        })
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
        
        # 模式3: <tool_call> 标签格式
        if not tool_calls:
            tool_call_pattern = r'<tool_call>\s*\{["\']name["\']\s*:\s*["\']([^"\']+)["\']\s*,\s*["\']arguments["\']\s*:\s*(\{.*?\})\s*\}\s*</tool_call>'
            matches = re.findall(tool_call_pattern, content, re.DOTALL)
            
            for i, (name, args_str) in enumerate(matches):
                try:
                    args = json.loads(args_str)
                    tool_calls.append({
                        "id": f"call_{i}",
                        "name": name,
                        "args": args
                    })
                except json.JSONDecodeError:
                    continue
        
        return tool_calls
