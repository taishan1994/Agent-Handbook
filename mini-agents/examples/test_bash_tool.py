import asyncio
from Mini_Agents.tools import BashTool, BashOutputTool, BashKillTool


async def main():
    print("=" * 60)
    print("Testing Mini_Agents BashTool")
    print("=" * 60)

    bash_tool = BashTool()
    bash_output_tool = BashOutputTool()
    bash_kill_tool = BashKillTool()

    print(f"\n✓ BashTool initialized")
    print(f"  Name: {bash_tool.name}")
    print(f"  Shell: {'PowerShell' if bash_tool.is_windows else 'bash'}")

    print("\n" + "-" * 60)
    print("Test 1: Foreground command execution")
    print("-" * 60)

    result1 = await bash_tool.execute("echo 'Hello from BashTool!'")
    print(f"\nCommand: echo 'Hello from BashTool!'")
    print(f"Success: {result1.success}")
    print(f"Exit code: {result1.exit_code}")
    print(f"Stdout: {result1.stdout}")
    if result1.stderr:
        print(f"Stderr: {result1.stderr}")

    print("\n" + "-" * 60)
    print("Test 2: List current directory")
    print("-" * 60)

    result2 = await bash_tool.execute("ls -la")
    print(f"\nCommand: ls -la")
    print(f"Success: {result2.success}")
    print(f"Exit code: {result2.exit_code}")
    print(f"Output:\n{result2.stdout}")

    print("\n" + "-" * 60)
    print("Test 3: Background command execution")
    print("-" * 60)

    result3 = await bash_tool.execute(
        "for i in {1..5}; do echo \"Count: $i\"; sleep 1; done",
        run_in_background=True
    )
    print(f"\nCommand: for i in {{1..5}}; do echo \"Count: $i\"; sleep 1; done")
    print(f"Success: {result3.success}")
    print(f"Bash ID: {result3.bash_id}")
    print(f"Content: {result3.content}")

    bash_id = result3.bash_id

    print("\n" + "-" * 60)
    print("Test 4: Monitor background command output")
    print("-" * 60)

    print(f"\nMonitoring bash_id: {bash_id}")
    for i in range(3):
        await asyncio.sleep(1.5)
        output_result = await bash_output_tool.execute(bash_id)
        print(f"\nCheck {i+1}:")
        print(f"  Success: {output_result.success}")
        print(f"  New output:\n{output_result.stdout or '(no new output)'}")

    print("\n" + "-" * 60)
    print("Test 5: Start long-running background command")
    print("-" * 60)

    result5 = await bash_tool.execute(
        "while true; do echo 'Running...'; sleep 2; done",
        run_in_background=True
    )
    print(f"\nCommand: while true; do echo 'Running...'; sleep 2; done")
    print(f"Success: {result5.success}")
    print(f"Bash ID: {result5.bash_id}")

    long_running_bash_id = result5.bash_id

    await asyncio.sleep(2)

    output_result5 = await bash_output_tool.execute(long_running_bash_id)
    print(f"\nFirst output check:")
    print(f"  Success: {output_result5.success}")
    print(f"  Output:\n{output_result5.stdout}")

    print("\n" + "-" * 60)
    print("Test 6: Terminate background command")
    print("-" * 60)

    print(f"\nTerminating bash_id: {long_running_bash_id}")
    kill_result = await bash_kill_tool.execute(long_running_bash_id)
    print(f"Success: {kill_result.success}")
    print(f"Content: {kill_result.content}")
    print(f"Exit code: {kill_result.exit_code}")

    print("\n" + "-" * 60)
    print("Test 7: Test with filter pattern")
    print("-" * 60)

    result7 = await bash_tool.execute(
        "for i in {1..10}; do echo \"Line $i: test\"; sleep 0.3; done",
        run_in_background=True
    )
    print(f"\nCommand: for i in {{1..10}}; do echo \"Line $i: test\"; sleep 0.3; done")
    print(f"Bash ID: {result7.bash_id}")

    filter_bash_id = result7.bash_id
    await asyncio.sleep(3)

    filtered_result = await bash_output_tool.execute(filter_bash_id, filter_str="Line [1-5]:")
    print(f"\nFiltered output (pattern: 'Line [1-5]:'):")
    print(f"  Output:\n{filtered_result.stdout}")

    await bash_kill_tool.execute(filter_bash_id)

    print("\n" + "-" * 60)
    print("Test 8: Error handling - invalid command")
    print("-" * 60)

    result8 = await bash_tool.execute("invalid_command_that_does_not_exist")
    print(f"\nCommand: invalid_command_that_does_not_exist")
    print(f"Success: {result8.success}")
    print(f"Exit code: {result8.exit_code}")
    print(f"Error: {result8.error}")

    print("\n" + "-" * 60)
    print("Test 9: Error handling - invalid bash_id")
    print("-" * 60)

    result9 = await bash_output_tool.execute("invalid_bash_id")
    print(f"\nQuery invalid bash_id: invalid_bash_id")
    print(f"Success: {result9.success}")
    print(f"Error: {result9.error}")

    print("\n" + "=" * 60)
    print("✅ All BashTool tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
