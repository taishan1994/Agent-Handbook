import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
sys.path.append(os.path.dirname(__file__))  # 添加当前目录，以便导入 pocketflow

from flow import tool_use_flow
from crewai_flow import financial_analysis_flow


async def demonstrate_langchain_tool_use():
    """演示基于LangChain示例的工具使用模式"""
    print("\n" + "="*60)
    print("演示基于LangChain示例的工具使用模式")
    print("="*60)
    
    # 创建共享状态
    shared_state = {
        "user_input": "帮我查找苹果公司的最新股价",
        "history": []
    }
    
    print(f"用户输入: {shared_state['user_input']}")
    print("\n开始执行流程...")
    
    # 运行流程
    result = await tool_use_flow.run(shared_state)
    
    # 打印结果
    print("\n" + "-"*60)
    print("最终响应:")
    print(result.get("final_response", "未获取到响应"))
    print("-"*60)
    
    return result


async def demonstrate_crewai_tool_use():
    """演示基于CrewAI示例的工具使用模式"""
    print("\n" + "="*60)
    print("演示基于CrewAI示例的工具使用模式")
    print("="*60)
    
    # 创建共享状态
    shared_state = {
        "task_description": "分析苹果公司(AAPL)的当前股价，并提供投资建议"
    }
    
    print(f"任务描述: {shared_state['task_description']}")
    print("\n开始执行流程...")
    
    # 运行流程
    result = await financial_analysis_flow.run(shared_state)
    
    # 打印结果
    print("\n" + "-"*60)
    print("最终响应:")
    print(result.get("final_response", "未获取到响应"))
    print("-"*60)
    
    return result


async def demonstrate_multiple_tool_calls():
    """演示多个工具调用的场景"""
    print("\n" + "="*60)
    print("演示多个工具调用的场景")
    print("="*60)
    
    # 创建共享状态
    shared_state = {
        "user_input": "帮我查找苹果公司的最新股价，然后搜索关于苹果公司的最新新闻",
        "history": []
    }
    
    print(f"用户输入: {shared_state['user_input']}")
    print("\n开始执行流程...")
    
    # 运行流程
    result = await tool_use_flow.run(shared_state)
    
    # 打印结果
    print("\n" + "-"*60)
    print("最终响应:")
    print(result.get("final_response", "未获取到响应"))
    print("-"*60)
    
    return result


async def demonstrate_error_handling():
    """演示错误处理场景"""
    print("\n" + "="*60)
    print("演示错误处理场景")
    print("="*60)
    
    # 创建共享状态 - 使用不存在的股票代码
    shared_state = {
        "task_description": "分析不存在的公司(NONEXISTENT)的当前股价"
    }
    
    print(f"任务描述: {shared_state['task_description']}")
    print("\n开始执行流程...")
    
    # 运行流程
    result = await financial_analysis_flow.run(shared_state)
    
    # 打印结果
    print("\n" + "-"*60)
    print("最终响应:")
    print(result.get("final_response", "未获取到响应"))
    print("-"*60)
    
    return result


async def main():
    """主函数"""
    print("\n🛠️  PocketFlow工具使用模式演示")
    print("本演示展示了如何使用PocketFlow实现工具调用功能")
    
    try:
        # 演示1: 基于LangChain示例的工具使用
        await demonstrate_langchain_tool_use()
        
        # 演示2: 基于CrewAI示例的工具使用
        await demonstrate_crewai_tool_use()
        
        # 演示3: 多个工具调用场景
        await demonstrate_multiple_tool_calls()
        
        # 演示4: 错误处理场景
        await demonstrate_error_handling()
        
        print("\n" + "="*60)
        print("所有演示完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())