#!/usr/bin/env python3
"""
目标设定和监控模式 - 主程序入口
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from goal_monitoring_flow import run_goal_monitoring_flow

def main():
    """
    主函数 - 运行目标设定和监控流程
    """
    print("=" * 60)
    print("目标设定和监控模式 - 代码生成与改进")
    print("=" * 60)
    
    # 示例用例和目标
    use_case = "创建一个Python函数，用于计算两个数字的最大公约数(GCD)"
    goals = [
        "函数应该命名为gcd",
        "函数应该接受两个整数作为参数",
        "函数应该返回这两个数的最大公约数",
        "函数应该处理负数输入",
        "函数应该处理零输入的情况",
        "代码应该包含适当的错误处理"
    ]
    
    # 设置最大迭代次数
    max_iterations = 5
    
    print(f"\n用例: {use_case}")
    print("\n目标:")
    for i, goal in enumerate(goals, 1):
        print(f"{i}. {goal}")
    print(f"\n最大迭代次数: {max_iterations}")
    print("\n开始生成和改进代码...\n")
    
    # 运行目标设定和监控流程
    result = run_goal_monitoring_flow(use_case, goals, max_iterations)
    
    print("\n" + "=" * 60)
    print("流程完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()