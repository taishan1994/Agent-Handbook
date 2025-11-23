"""
主程序 - 演示规划模式的使用
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from planning_flow import PlanningFlow


async def main():
    """主函数，演示规划模式的使用"""
    
    # 创建规划流程实例
    planning_flow = PlanningFlow()
    
    # 示例任务1: 研究报告
    task1 = "分析人工智能在医疗领域的最新应用和未来趋势"
    context1 = "这是一份为医疗科技公司准备的内部研究报告"
    
    print("=" * 80)
    print("示例任务1: 分析人工智能在医疗领域的最新应用和未来趋势")
    print("=" * 80)
    
    try:
        result1 = await planning_flow.run(task1, context1)
        print("\n最终响应:")
        print(result1)
    except Exception as e:
        print(f"执行任务1时出错: {str(e)}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())