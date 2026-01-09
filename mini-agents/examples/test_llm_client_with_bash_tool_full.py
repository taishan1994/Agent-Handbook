import asyncio
import json
from Mini_Agents import LLMClient, Message
from Mini_Agents.tools import BashTool, BashOutputTool, BashKillTool


def parse_tool_calls(content: str):
    """Parse tool calls from LLM response content."""
    tool_calls = []
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                tool_call = json.loads(line)
                if 'name' in tool_call and 'arguments' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
    return tool_calls


async def execute_tool_calls(tool_calls, bash_tool, bash_output_tool, bash_kill_tool):
    """Execute parsed tool calls and return results."""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call['name']
        args = tool_call['arguments']
        
        if tool_name == 'bash':
            result = await bash_tool.execute(**args)
            results.append(f"Command: {args.get('command')}\nOutput: {result.content}")
        elif tool_name == 'bash_output':
            result = await bash_output_tool.execute(**args)
            results.append(f"Bash ID: {args.get('bash_id')}\nOutput: {result.content}")
        elif tool_name == 'bash_kill':
            result = await bash_kill_tool.execute(**args)
            results.append(f"Killed Bash ID: {args.get('bash_id')}\nResult: {result.content}")
    
    return results


async def main():
    print("=" * 60)
    print("Testing LLMClient with BashTool (Full Tool Execution)")
    print("=" * 60)

    bash_tool = BashTool()
    bash_output_tool = BashOutputTool()
    bash_kill_tool = BashKillTool()

    client = LLMClient(
        api_key="test-key",
        api_base="http://192.168.16.14:18000/v1",
        provider="openai",
        model="/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507"
    )

    print(f"\n✓ LLMClient initialized")
    print(f"  Provider: {client.provider}")
    print(f"  API Base: {client.api_base}")
    print(f"  Model: {client.model}")

    print(f"\n✓ BashTool initialized")
    print(f"  Name: {bash_tool.name}")
    print(f"  Shell: {'PowerShell' if bash_tool.is_windows else 'bash'}")

    print("\n" + "-" * 60)
    print("Test 1: LLM executes simple bash command")
    print("-" * 60)

    messages1 = [
        Message(role="user", content="请使用bash工具执行命令：echo 'Hello from LLM with BashTool!'")
    ]

    print(f"\nUser message: {messages1[0].content}")
    response1 = await client.generate(messages1, tools=[bash_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response1.content)

    tool_calls1 = parse_tool_calls(response1.content)
    print(f"\n✓ Parsed {len(tool_calls1)} tool call(s)")

    if tool_calls1:
        results1 = await execute_tool_calls(tool_calls1, bash_tool, bash_output_tool, bash_kill_tool)
        print(f"\n✓ Tool execution results:")
        for result in results1:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 2: LLM lists current directory")
    print("-" * 60)

    messages2 = [
        Message(role="user", content="请使用bash工具列出当前目录的所有文件")
    ]

    print(f"\nUser message: {messages2[0].content}")
    response2 = await client.generate(messages2, tools=[bash_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response2.content)

    tool_calls2 = parse_tool_calls(response2.content)
    print(f"\n✓ Parsed {len(tool_calls2)} tool call(s)")

    if tool_calls2:
        results2 = await execute_tool_calls(tool_calls2, bash_tool, bash_output_tool, bash_kill_tool)
        print(f"\n✓ Tool execution results:")
        for result in results2:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 3: LLM starts a background process")
    print("-" * 60)

    messages3 = [
        Message(role="user", content="请使用bash工具在后台启动一个命令，每隔1秒打印一次计数，共5次。使用run_in_background=true参数。")
    ]

    print(f"\nUser message: {messages3[0].content}")
    response3 = await client.generate(messages3, tools=[bash_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response3.content)

    tool_calls3 = parse_tool_calls(response3.content)
    print(f"\n✓ Parsed {len(tool_calls3)} tool call(s)")

    bash_id = None
    if tool_calls3:
        results3 = await execute_tool_calls(tool_calls3, bash_tool, bash_output_tool, bash_kill_tool)
        print(f"\n✓ Tool execution results:")
        for result in results3:
            print(f"\n{result}")
            if "bash_id" in result.lower():
                import re
                match = re.search(r"ID:\s*([a-f0-9]{8})", result)
                if match:
                    bash_id = match.group(1)
                    print(f"\nExtracted bash_id: {bash_id}")

    if bash_id:
        print("\n" + "-" * 60)
        print("Test 4: Monitor background process output")
        print("-" * 60)

        print(f"\nMonitoring bash_id: {bash_id}")
        for i in range(3):
            await asyncio.sleep(1.5)
            output_result = await bash_output_tool.execute(bash_id)
            print(f"\nCheck {i+1}:")
            print(f"  New output:\n{output_result.stdout or '(no new output)'}")

        print("\n" + "-" * 60)
        print("Test 5: Terminate background process")
        print("-" * 60)

        print(f"\nTerminating bash_id: {bash_id}")
        kill_result = await bash_kill_tool.execute(bash_id)
        print(f"Success: {kill_result.success}")
        print(f"Exit code: {kill_result.exit_code}")

    print("\n" + "-" * 60)
    print("Test 6: LLM with multiple bash operations")
    print("-" * 60)

    messages6 = [
        Message(role="user", content="请使用bash工具执行以下操作：1) 创建一个测试文件test.txt 2) 向文件写入内容'Hello World' 3) 读取文件内容 4) 删除文件")
    ]

    print(f"\nUser message: {messages6[0].content}")
    response6 = await client.generate(messages6, tools=[bash_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response6.content)

    tool_calls6 = parse_tool_calls(response6.content)
    print(f"\n✓ Parsed {len(tool_calls6)} tool call(s)")

    if tool_calls6:
        results6 = await execute_tool_calls(tool_calls6, bash_tool, bash_output_tool, bash_kill_tool)
        print(f"\n✓ Tool execution results:")
        for i, result in enumerate(results6, 1):
            print(f"\nStep {i}:")
            print(result)

    print("\n" + "-" * 60)
    print("Test 7: LLM checks system information")
    print("-" * 60)

    messages7 = [
        Message(role="user", content="请使用bash工具检查系统信息，包括：当前用户、操作系统类型、CPU核心数、内存使用情况")
    ]

    print(f"\nUser message: {messages7[0].content}")
    response7 = await client.generate(messages7, tools=[bash_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response7.content)

    tool_calls7 = parse_tool_calls(response7.content)
    print(f"\n✓ Parsed {len(tool_calls7)} tool call(s)")

    if tool_calls7:
        results7 = await execute_tool_calls(tool_calls7, bash_tool, bash_output_tool, bash_kill_tool)
        print(f"\n✓ Tool execution results:")
        for result in results7:
            print(f"\n{result}")

    print("\n" + "=" * 60)
    print("✅ All LLMClient with BashTool tests completed!")
    print("=" * 60)

    print("\nNote: This test demonstrates the full tool calling workflow:")
    print("  1. LLM generates tool calls in JSON format")
    print("  2. Parse tool calls from LLM response")
    print("  3. Execute tools with parsed arguments")
    print("  4. Return tool execution results")
    print("\nFor automatic tool execution, configure your vLLM server with:")
    print("  --tool-call-parser qwen  (for Qwen models)")
    print("  --tool-call-parser hermes  (for general use)")


if __name__ == "__main__":
    asyncio.run(main())
