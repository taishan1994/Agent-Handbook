#!/usr/bin/env python3
"""
目标设定和监控模式 - 测试脚本
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from goal_monitoring_flow import run_goal_monitoring_flow

def test_simple_case():
    """
    测试简单用例
    """
    print("=" * 60)
    print("测试用例：计算两个数字的最大公约数")
    print("=" * 60)
    
    use_case = "创建一个Python函数，用于计算两个数字的最大公约数(GCD)"
    goals = [
        "函数应该命名为gcd",
        "函数应该接受两个整数作为参数",
        "函数应该返回这两个数的最大公约数",
        "函数应该处理负数输入",
        "函数应该处理零输入的情况"
    ]
    
    max_iterations = 3  # 减少迭代次数以便快速测试
    
    print(f"\n用例: {use_case}")
    print("\n目标:")
    for i, goal in enumerate(goals, 1):
        print(f"{i}. {goal}")
    print(f"\n最大迭代次数: {max_iterations}")
    print("\n开始生成和改进代码...\n")
    
    # 运行目标设定和监控流程
    result = run_goal_monitoring_flow(use_case, goals, max_iterations)
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_simple_case()