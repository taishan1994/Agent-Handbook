import asyncio
from Mini_Agents import LLMClient, Message
from Mini_Agents.tools import BashTool, BashOutputTool, BashKillTool


async def main():
    print("=" * 60)
    print("Testing LLMClient with BashTool")
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

    print(f"\n✓ Response generated")
    print(f"Content:\n{response1.content}")

    print("\n" + "-" * 60)
    print("Test 2: LLM lists current directory")
    print("-" * 60)

    messages2 = [
        Message(role="user", content="请使用bash工具列出当前目录的所有文件")
    ]

    print(f"\nUser message: {messages2[0].content}")
    response2 = await client.generate(messages2, tools=[bash_tool])

    print(f"\n✓ Response generated")
    print(f"Content:\n{response2.content}")

    print("\n" + "-" * 60)
    print("Test 3: LLM starts a background process")
    print("-" * 60)

    messages3 = [
        Message(role="user", content="请使用bash工具在后台启动一个命令，每隔1秒打印一次计数，共5次。使用run_in_background=true参数。")
    ]

    print(f"\nUser message: {messages3[0].content}")
    response3 = await client.generate(messages3, tools=[bash_tool])

    print(f"\n✓ Response generated")
    print(f"Content:\n{response3.content}")

    bash_id = None
    if response3.content and "bash_id" in response3.content.lower():
        import re
        match = re.search(r"['\"]([a-f0-9]{8})['\"]", response3.content)
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

    print(f"\n✓ Response generated")
    print(f"Content:\n{response6.content}")

    print("\n" + "-" * 60)
    print("Test 7: LLM checks system information")
    print("-" * 60)

    messages7 = [
        Message(role="user", content="请使用bash工具检查系统信息，包括：当前用户、操作系统类型、CPU核心数、内存使用情况")
    ]

    print(f"\nUser message: {messages7[0].content}")
    response7 = await client.generate(messages7, tools=[bash_tool])

    print(f"\n✓ Response generated")
    print(f"Content:\n{response7.content}")

    print("\n" + "=" * 60)
    print("✅ All LLMClient with BashTool tests completed!")
    print("=" * 60)

    print("\nNote: These tests demonstrate LLM's ability to:")
    print("  - Execute bash commands through tools")
    print("  - Interpret command outputs")
    print("  - Perform multi-step operations")
    print("  - Manage background processes")


if __name__ == "__main__":
    asyncio.run(main())
