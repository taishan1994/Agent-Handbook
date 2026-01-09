import asyncio
import json
import tempfile
from pathlib import Path
from Mini_Agents import LLMClient, Message
from Mini_Agents.tools import ReadTool, WriteTool, EditTool


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


async def execute_tool_calls(tool_calls, read_tool, write_tool, edit_tool):
    """Execute parsed tool calls and return results."""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call['name']
        args = tool_call['arguments']
        
        if tool_name == 'read_file':
            result = await read_tool.execute(**args)
            results.append(f"Read: {args.get('path')}\n{result.content}")
        elif tool_name == 'write_file':
            result = await write_tool.execute(**args)
            results.append(f"Write: {args.get('path')}\n{result.content}")
        elif tool_name == 'edit_file':
            result = await edit_tool.execute(**args)
            results.append(f"Edit: {args.get('path')}\n{result.content}")
    
    return results


async def main():
    print("=" * 60)
    print("Testing LLMClient with FileTools (Full Tool Execution)")
    print("=" * 60)

    workspace = Path(tempfile.mkdtemp())
    print(f"\n✓ Workspace created: {workspace}")

    read_tool = ReadTool(workspace_dir=str(workspace))
    write_tool = WriteTool(workspace_dir=str(workspace))
    edit_tool = EditTool(workspace_dir=str(workspace))

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

    print(f"\n✓ FileTools initialized")
    print(f"  ReadTool: {read_tool.name}")
    print(f"  WriteTool: {write_tool.name}")
    print(f"  EditTool: {edit_tool.name}")

    print("\n" + "-" * 60)
    print("Test 1: LLM creates a new file")
    print("-" * 60)

    messages1 = [
        Message(role="user", content="请使用write_file工具创建一个名为hello.txt的文件，内容为'Hello, World!'")
    ]

    print(f"\nUser message: {messages1[0].content}")
    response1 = await client.generate(messages1, tools=[write_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response1.content)

    tool_calls1 = parse_tool_calls(response1.content)
    print(f"\n✓ Parsed {len(tool_calls1)} tool call(s)")

    if tool_calls1:
        results1 = await execute_tool_calls(tool_calls1, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for result in results1:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 2: LLM reads the file")
    print("-" * 60)

    messages2 = [
        Message(role="user", content="请使用read_file工具读取hello.txt文件的内容")
    ]

    print(f"\nUser message: {messages2[0].content}")
    response2 = await client.generate(messages2, tools=[read_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response2.content)

    tool_calls2 = parse_tool_calls(response2.content)
    print(f"\n✓ Parsed {len(tool_calls2)} tool call(s)")

    if tool_calls2:
        results2 = await execute_tool_calls(tool_calls2, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for result in results2:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 3: LLM edits the file")
    print("-" * 60)

    messages3 = [
        Message(role="user", content="请使用edit_file工具将hello.txt文件中的'Hello, World!'替换为'Hello, Mini_Agents!'")
    ]

    print(f"\nUser message: {messages3[0].content}")
    response3 = await client.generate(messages3, tools=[edit_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response3.content)

    tool_calls3 = parse_tool_calls(response3.content)
    print(f"\n✓ Parsed {len(tool_calls3)} tool call(s)")

    if tool_calls3:
        results3 = await execute_tool_calls(tool_calls3, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for result in results3:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 4: LLM reads the edited file")
    print("-" * 60)

    messages4 = [
        Message(role="user", content="请使用read_file工具再次读取hello.txt文件，确认修改已生效")
    ]

    print(f"\nUser message: {messages4[0].content}")
    response4 = await client.generate(messages4, tools=[read_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response4.content)

    tool_calls4 = parse_tool_calls(response4.content)
    print(f"\n✓ Parsed {len(tool_calls4)} tool call(s)")

    if tool_calls4:
        results4 = await execute_tool_calls(tool_calls4, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for result in results4:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 5: LLM creates a multi-line file")
    print("-" * 60)

    messages5 = [
        Message(role="user", content="请使用write_file工具创建一个名为notes.txt的文件，包含以下内容：\nLine 1: Introduction\nLine 2: This is a test\nLine 3: File tools work great!")
    ]

    print(f"\nUser message: {messages5[0].content}")
    response5 = await client.generate(messages5, tools=[write_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response5.content)

    tool_calls5 = parse_tool_calls(response5.content)
    print(f"\n✓ Parsed {len(tool_calls5)} tool call(s)")

    if tool_calls5:
        results5 = await execute_tool_calls(tool_calls5, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for result in results5:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 6: LLM reads file with offset and limit")
    print("-" * 60)

    messages6 = [
        Message(role="user", content="请使用read_file工具读取notes.txt文件的第2行到第3行（使用offset=2, limit=2）")
    ]

    print(f"\nUser message: {messages6[0].content}")
    response6 = await client.generate(messages6, tools=[read_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response6.content)

    tool_calls6 = parse_tool_calls(response6.content)
    print(f"\n✓ Parsed {len(tool_calls6)} tool call(s)")

    if tool_calls6:
        results6 = await execute_tool_calls(tool_calls6, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for result in results6:
            print(f"\n{result}")

    print("\n" + "-" * 60)
    print("Test 7: LLM performs multi-step file operations")
    print("-" * 60)

    messages7 = [
        Message(role="user", content="请执行以下操作：1) 使用write_file创建一个名为todo.txt的文件，内容为'Task 1: Learn Mini_Agents\nTask 2: Test file tools' 2) 使用read_file读取文件 3) 使用edit_file将'Task 2: Test file tools'替换为'Task 2: Complete file tool testing'")
    ]

    print(f"\nUser message: {messages7[0].content}")
    response7 = await client.generate(messages7, tools=[write_tool, read_tool, edit_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response7.content)

    tool_calls7 = parse_tool_calls(response7.content)
    print(f"\n✓ Parsed {len(tool_calls7)} tool call(s)")

    if tool_calls7:
        results7 = await execute_tool_calls(tool_calls7, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for i, result in enumerate(results7, 1):
            print(f"\nStep {i}:")
            print(result)

    print("\n" + "-" * 60)
    print("Test 8: LLM creates file in subdirectory")
    print("-" * 60)

    messages8 = [
        Message(role="user", content="请使用write_file工具在subdir目录下创建一个名为nested.txt的文件，内容为'This is a nested file'")
    ]

    print(f"\nUser message: {messages8[0].content}")
    response8 = await client.generate(messages8, tools=[write_tool])

    print(f"\n✓ LLM Response (raw):")
    print(response8.content)

    tool_calls8 = parse_tool_calls(response8.content)
    print(f"\n✓ Parsed {len(tool_calls8)} tool call(s)")

    if tool_calls8:
        results8 = await execute_tool_calls(tool_calls8, read_tool, write_tool, edit_tool)
        print(f"\n✓ Tool execution results:")
        for result in results8:
            print(f"\n{result}")

    print("\n" + "=" * 60)
    print("✅ All LLMClient with FileTools tests completed!")
    print("=" * 60)

    print("\nWorkspace location:", workspace)
    print("\nFiles created in workspace:")
    for file in sorted(workspace.rglob("*")):
        if file.is_file():
            rel_path = file.relative_to(workspace)
            print(f"  - {rel_path}")

    print("\nNote: This test demonstrates LLM's ability to:")
    print("  - Create, read, and edit files through tools")
    print("  - Perform multi-step file operations")
    print("  - Work with relative and absolute paths")
    print("  - Handle files in subdirectories")


if __name__ == "__main__":
    asyncio.run(main())
