# 部署服务
如果是自己部署服务的话，使用vllm部署大模型，启动指令如下：
```shell
CUDA_VISIBLE_DEVICES=0 vllm serve ${model_path} --host 0.0.0.0 --port ${port} --tensor-parallel-size 1 --gpu-memory-utilization 0.95 --max-model-len 16000 --enable-auto-tool-choice --tool-call-parser pythonic
```
需要注意的是两个参数：
- --enable-auto-tool-choice
- --tool-call-parser
--tool-call-parser 这个参数有多种选择，对于Qwen3-30B-A3B-Instruct-2507模型，我们选择基础的pythonic即可。

# 安装环境
`cd mini-agents && pip install -e .`

# 调用openai格式的接口
基础的代码摘自MiniMax的Mini-Agent。这里我们使用的是异步请求的函数：`from openai import AsyncOpenAI`传入的是部署好的url以及模型名称。

为了能够让该模型使用，我们这样定义工具：
```python
"""Base tool classes."""

from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """Tool execution result."""

    success: bool
    content: str = ""
    error: str | None = None


class Tool:
    """Base class for all tools."""

    @property
    def name(self) -> str:
        """Tool name."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """Tool description."""
        raise NotImplementedError

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema (JSON Schema format)."""
        raise NotImplementedError

    async def execute(self, *args, **kwargs) -> ToolResult:  # type: ignore
        """Execute the tool with arbitrary arguments."""
        raise NotImplementedError

    def to_schema(self) -> dict[str, Any]:
        """Convert tool to Anthropic tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert tool to OpenAI tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
```
需要注意的是openai需要接受的工具的格式是：
```python
{
    "type": "function",
    "function": {
        "name": self.name,
        "description": self.description,
        "parameters": self.parameters,
    },
}
```
最后，在examples/test_llm_client_with_tool.py中：
```python
import asyncio
from Mini_Agents import Tool, ToolResult, LLMClient, Message

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "A custom tool example"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input text"}
            },
            "required": ["input"]
        }
    
    async def execute(self, input: str) -> ToolResult:
        return ToolResult(success=True, content=f"Processed: {input}")

async def main():
    print("Testing Mini_Agents package imports and basic functionality...")
    
    # Test 1: Create a tool
    tool = MyTool()
    print(f"✓ Tool created: {tool.name}")
    print(f"✓ Tool description: {tool.description}")
    print(f"✓ Tool parameters: {tool.parameters}")
    
    # Test 2: Execute tool
    result = await tool.execute("hello world")
    print(f"✓ Tool executed: {result.content}")
    

    client = LLMClient(
        api_key="test-key",
        api_base="http://192.168.16.14:18000/v1",
        provider="openai",  # openai/anthropic
        model="/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507"
    )
    
    # Test 4: Create messages
    messages = [Message(role="user", content="Use my_tool with 'hello world'")]
    response = await client.generate(messages, tools=[tool])

    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
```

我们定义了一个测试的工具，运行之后得到结果如下：
```xml
<tool_call>
{"name": "my_tool", "arguments": {"input": "hello world"}}
</tool_call>
```
我们可以对工具进行解析并执行工具，并将结果进一步返回给大模型进行其他的任务。更多工具的使用样例参考examples中的更多样例。