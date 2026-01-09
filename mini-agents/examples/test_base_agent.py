import asyncio
from Mini_Agents.base_agent import Agent
from Mini_Agents.llm import LLMClient
from Mini_Agents.tools import ReadTool, WriteTool

async def main():
    # 1. 创建LLM客户端
    llm_client = LLMClient(
        api_key="test-key",
        api_base="http://192.168.16.24:18000/v1",
        provider="openai",
        model="/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507"
    )
    
    # 2. 准备工具
    workspace_dir = "./my_workspace"
    tools = [
        ReadTool(workspace_dir=workspace_dir),
        WriteTool(workspace_dir=workspace_dir)
    ]
    
    # 3. 创建Agent实例
    agent = Agent(
        llm_client=llm_client,
        system_prompt="你是一个文件操作助手，可以帮助用户读取和写入文件。",
        tools=tools,
        max_steps=50,
        workspace_dir=workspace_dir,
        token_limit=80000
    )
    
    # 4. 添加用户任务
    agent.add_user_message("请创建一个名为hello.txt的文件，内容是'Hello, World!'")
    
    # 5. 运行Agent
    result = await agent.run()
    print(f"\n最终结果: {result}")
    
    # 6. 查看对话历史
    history = agent.get_history()
    print(history)
    print(f"\n对话共进行了 {len(history)} 轮")

# 运行主程序
asyncio.run(main())