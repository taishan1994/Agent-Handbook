"""
Complete Demo: LLM with Skill + Code Execution

Demonstrates how LLM can:
1. Load a skill
2. Parse the skill content to understand what code to execute
3. Execute the code using code execution tools
4. Return results to the user
"""

import asyncio
import json
from pathlib import Path
from Mini_Agents import LLMClient, Message
from Mini_Agents.tools.skill_tool import create_skill_tools
from Mini_Agents.tools import create_code_execution_tools


async def main():
    print("=" * 60)
    print("Complete Demo: LLM with Skill + Code Execution")
    print("=" * 60)

    # Step 1: Setup tools
    skills_dir = Path(__file__).parent.parent / "Mini_Agents" / "skills"
    print(f"\n📂 Loading skills from: {skills_dir}")
    
    skill_tools, skill_loader = create_skill_tools(str(skills_dir))
    print(f"✓ Loaded {len(skill_tools)} skill tool(s)")
    
    code_tools = create_code_execution_tools()
    print(f"✓ Created {len(code_tools)} code execution tool(s)")
    
    # Combine all tools
    all_tools = skill_tools + code_tools
    print(f"✓ Total tools available: {len(all_tools)}")
    
    # Step 2: Setup LLM client
    client = LLMClient(
        api_key="test-key",
        api_base="http://192.168.16.24:18000/v1",
        provider="openai",
        model="/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507"
    )
    print("✓ LLMClient created")
    
    # Step 3: Create system prompt
    if skill_loader:
        available_skills = skill_loader.list_skills()
        print(f"\n📚 Available skills ({len(available_skills)}):")
        for skill_name in available_skills:
            skill = skill_loader.get_skill(skill_name)
            print(f"  - {skill_name}: {skill.description}")
        
        skills_metadata = skill_loader.get_skills_metadata_prompt()
        system_prompt = f"""You are a helpful AI assistant with access to specialized skills and code execution capabilities.

{skills_metadata}

Available tools:
- get_skill: Load complete content for a specified skill (includes guidance and code examples)
- execute_code: Execute Python or JavaScript code directly
- execute_script: Execute script files (Python, JavaScript, Bash)

IMPORTANT: When you need to process a file (like PDF):
1. First, use get_skill to load the appropriate skill (e.g., "pdf" for PDF processing)
2. Parse the skill content to understand what code needs to be executed
3. Use execute_code to run the appropriate code with the correct file path
4. Provide the results to the user

The skill content will include:
- Usage instructions
- Code examples (both inline and script files)
- Best practices

When executing code from a skill:
- Replace placeholder paths (like "document.pdf") with the actual file path provided by the user
- Use execute_code for inline code snippets
- Use execute_script for running existing script files

Always execute the code and return the actual results to the user."""
        
        print("\n✓ System prompt created")
    
    # Step 4: User request
    user_message = "帮我解析一下pdf，路径是：/nfs/FM/gongoubo/new_project/Agent-Handbook/mini-agents/examples/test.pdf。"
    
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=user_message)
    ]
    
    print(f"\n📝 User message: {user_message}")
    print("\n" + "=" * 60)
    print("Starting LLM Conversation")
    print("=" * 60)
    
    # Step 5: Execute the conversation
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        # Call LLM
        response = await client.generate(messages=messages, tools=all_tools)
        
        print(f"\n🤖 LLM Response:")
        print(response.content)
        
        if response.thinking:
            print(f"\n💭 Thinking:")
            print(response.thinking)
        
        # Check if LLM made tool calls
        if response.tool_calls:
            print(f"\n🔧 LLM made {len(response.tool_calls)} tool call(s):")
            
            # Execute all tool calls
            for tool_call in response.tool_calls:
                print(f"\n  Tool: {tool_call.function.name}")
                print(f"  Arguments: {json.dumps(tool_call.function.arguments, indent=4, ensure_ascii=False)}")
                
                # Find the appropriate tool
                tool = None
                for t in all_tools:
                    if t.name == tool_call.function.name:
                        tool = t
                        break
                
                if not tool:
                    print(f"  ✗ Tool '{tool_call.function.name}' not found")
                    continue
                
                # Execute the tool
                print(f"\n  ⚙️  Executing tool...")
                tool_result = await tool.execute(**tool_call.function.arguments)
                print(f"  ✓ Tool executed")
                print(f"    Success: {tool_result.success}")
                
                if tool_result.success:
                    # If it's a skill tool, show preview
                    if tool_call.function.name == "get_skill":
                        print(f"\n  📋 Skill Content Preview:")
                        print(f"    {tool_result.content[:300]}...")
                    
                    # Show output
                    print(f"\n  📄 Output:")
                    output = tool_result.content
                    if len(output) > 500:
                        output = output[:500] + "\n... (truncated)"
                    print(f"    {output}")
                    
                    # Add tool result to messages
                    messages.append(Message(
                        role="tool",
                        content=json.dumps({
                            "tool_call_id": tool_call.id,
                            "output": tool_result.content
                        })
                    ))
                else:
                    print(f"\n  ✗ Tool execution failed:")
                    print(f"    Error: {tool_result.error}")
                    
                    # Add error to messages
                    messages.append(Message(
                        role="tool",
                        content=json.dumps({
                            "tool_call_id": tool_call.id,
                            "error": tool_result.error
                        })
                    ))
            
            # Continue conversation with tool results
            print(f"\n🔄 Continuing conversation with tool results...")
            continue
        
        # No more tool calls, conversation is complete
        print(f"\n✓ Conversation completed (no more tool calls)")
        break
        
    
    print("\n" + "=" * 60)
    print("✓ Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
