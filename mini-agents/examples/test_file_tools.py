import asyncio
import tempfile
from pathlib import Path
from Mini_Agents.tools import ReadTool, WriteTool, EditTool


async def main():
    print("=" * 60)
    print("Testing Mini_Agents FileTools")
    print("=" * 60)

    workspace = Path(tempfile.mkdtemp())
    print(f"\n✓ Workspace created: {workspace}")

    read_tool = ReadTool(workspace_dir=str(workspace))
    write_tool = WriteTool(workspace_dir=str(workspace))
    edit_tool = EditTool(workspace_dir=str(workspace))

    print(f"\n✓ Tools initialized")
    print(f"  ReadTool: {read_tool.name}")
    print(f"  WriteTool: {write_tool.name}")
    print(f"  EditTool: {edit_tool.name}")

    print("\n" + "-" * 60)
    print("Test 1: Write a new file")
    print("-" * 60)

    test_content = """Hello World!
This is a test file.
It has multiple lines.
Line 4
Line 5
"""

    result1 = await write_tool.execute(
        path="test.txt",
        content=test_content
    )
    print(f"\nWrite to: test.txt")
    print(f"Success: {result1.success}")
    print(f"Content: {result1.content}")

    print("\n" + "-" * 60)
    print("Test 2: Read the file")
    print("-" * 60)

    result2 = await read_tool.execute(path="test.txt")
    print(f"\nRead from: test.txt")
    print(f"Success: {result2.success}")
    print(f"Content:\n{result2.content}")

    print("\n" + "-" * 60)
    print("Test 3: Read file with offset and limit")
    print("-" * 60)

    result3 = await read_tool.execute(path="test.txt", offset=2, limit=2)
    print(f"\nRead from: test.txt (offset=2, limit=2)")
    print(f"Success: {result3.success}")
    print(f"Content:\n{result3.content}")

    print("\n" + "-" * 60)
    print("Test 4: Edit file - replace text")
    print("-" * 60)

    result4 = await edit_tool.execute(
        path="test.txt",
        old_str="Line 4",
        new_str="Modified Line 4"
    )
    print(f"\nEdit: test.txt")
    print(f"Replace: 'Line 4' -> 'Modified Line 4'")
    print(f"Success: {result4.success}")
    print(f"Content: {result4.content}")

    print("\n" + "-" * 60)
    print("Test 5: Read edited file")
    print("-" * 60)

    result5 = await read_tool.execute(path="test.txt")
    print(f"\nRead from: test.txt (after edit)")
    print(f"Success: {result5.success}")
    print(f"Content:\n{result5.content}")

    print("\n" + "-" * 60)
    print("Test 6: Write to a new file in subdirectory")
    print("-" * 60)

    result6 = await write_tool.execute(
        path="subdir/nested.txt",
        content="This is a nested file."
    )
    print(f"\nWrite to: subdir/nested.txt")
    print(f"Success: {result6.success}")
    print(f"Content: {result6.content}")

    print("\n" + "-" * 60)
    print("Test 7: Read nested file")
    print("-" * 60)

    result7 = await read_tool.execute(path="subdir/nested.txt")
    print(f"\nRead from: subdir/nested.txt")
    print(f"Success: {result7.success}")
    print(f"Content:\n{result7.content}")

    print("\n" + "-" * 60)
    print("Test 8: Edit file with multi-line replacement")
    print("-" * 60)

    result8 = await edit_tool.execute(
        path="test.txt",
        old_str="This is a test file.\nIt has multiple lines.",
        new_str="This is an edited test file.\nIt now has different content."
    )
    print(f"\nEdit: test.txt")
    print(f"Replace multi-line text")
    print(f"Success: {result8.success}")
    print(f"Content: {result8.content}")

    print("\n" + "-" * 60)
    print("Test 9: Read edited file again")
    print("-" * 60)

    result9 = await read_tool.execute(path="test.txt")
    print(f"\nRead from: test.txt (after multi-line edit)")
    print(f"Success: {result9.success}")
    print(f"Content:\n{result9.content}")

    print("\n" + "-" * 60)
    print("Test 10: Error handling - read non-existent file")
    print("-" * 60)

    result10 = await read_tool.execute(path="nonexistent.txt")
    print(f"\nRead from: nonexistent.txt")
    print(f"Success: {result10.success}")
    print(f"Error: {result10.error}")

    print("\n" + "-" * 60)
    print("Test 11: Error handling - edit non-existent file")
    print("-" * 60)

    result11 = await edit_tool.execute(
        path="nonexistent.txt",
        old_str="some text",
        new_str="new text"
    )
    print(f"\nEdit: nonexistent.txt")
    print(f"Success: {result11.success}")
    print(f"Error: {result11.error}")

    print("\n" + "-" * 60)
    print("Test 12: Error handling - edit with non-existent old_str")
    print("-" * 60)

    result12 = await edit_tool.execute(
        path="test.txt",
        old_str="text that does not exist",
        new_str="new text"
    )
    print(f"\nEdit: test.txt")
    print(f"Success: {result12.success}")
    print(f"Error: {result12.error}")

    print("\n" + "-" * 60)
    print("Test 13: Write with absolute path")
    print("-" * 60)

    abs_path = workspace / "absolute.txt"
    result13 = await write_tool.execute(
        path=str(abs_path),
        content="Written with absolute path"
    )
    print(f"\nWrite to: {abs_path}")
    print(f"Success: {result13.success}")
    print(f"Content: {result13.content}")

    print("\n" + "-" * 60)
    print("Test 14: Read with absolute path")
    print("-" * 60)

    result14 = await read_tool.execute(path=str(abs_path))
    print(f"\nRead from: {abs_path}")
    print(f"Success: {result14.success}")
    print(f"Content:\n{result14.content}")

    print("\n" + "-" * 60)
    print("Test 15: List files in workspace")
    print("-" * 60)

    print(f"\nFiles in workspace {workspace}:")
    for file in sorted(workspace.rglob("*")):
        if file.is_file():
            rel_path = file.relative_to(workspace)
            print(f"  - {rel_path}")

    print("\n" + "=" * 60)
    print("✅ All FileTools tests completed!")
    print("=" * 60)

    print("\nWorkspace location:", workspace)
    print("(Workspace will be cleaned up automatically)")


if __name__ == "__main__":
    asyncio.run(main())
