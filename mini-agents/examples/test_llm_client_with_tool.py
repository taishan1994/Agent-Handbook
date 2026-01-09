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