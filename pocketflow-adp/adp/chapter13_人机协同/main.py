"""
人机协同模式基本示例

本模块提供了人机协同模式的基本使用示例，适合快速了解和入门。
"""

import sys
import os

# 添加当前目录路径
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

from flow import run_human_in_the_loop_example


def main():
    """主函数，演示人机协同模式的基本用法"""
    print("=" * 60)
    print("人机协同模式基本示例")
    print("=" * 60)
    
    # 示例1: 简单任务（自动处理）
    print("\n示例1: 简单任务（自动处理）")
    print("-" * 40)
    simple_task = "查询明天北京的天气"
    result1 = run_human_in_the_loop_example(
        task=simple_task,
        complexity_threshold=0.7,
        simulate_human=True
    )
    
    # 示例2: 复杂任务（人工干预）
    print("\n示例2: 复杂任务（人工干预）")
    print("-" * 40)
    complex_task = "制定一个涉及多部门协作的复杂项目计划，需要考虑预算、时间和人力资源限制"
    result2 = run_human_in_the_loop_example(
        task=complex_task,
        complexity_threshold=0.5,
        simulate_human=True
    )
    
    # 总结
    print("\n" + "=" * 60)
    print("示例总结")
    print("=" * 60)
    print(f"示例1 - 任务: {simple_task}")
    print(f"  需要人工干预: {result1.get('requires_human_intervention', False)}")
    print(f"  响应类型: {result1.get('response_type', 'unknown')}")
    print(f"  任务复杂度: {result1.get('task_complexity', 0):.2f}")
    if result1.get('requires_human_intervention'):
        print(f"  升级原因: {result1.get('escalation_reason', 'N/A')}")
        print(f"  人类输入: {result1.get('human_input', 'N/A')}")
    
    print(f"\n示例2 - 任务: {complex_task}")
    print(f"  需要人工干预: {result2.get('requires_human_intervention', False)}")
    print(f"  响应类型: {result2.get('response_type', 'unknown')}")
    print(f"  任务复杂度: {result2.get('task_complexity', 0):.2f}")
    if result2.get('requires_human_intervention'):
        print(f"  升级原因: {result2.get('escalation_reason', 'N/A')}")
        print(f"  人类输入: {result2.get('human_input', 'N/A')}")
    
    print("\n✅ 基本示例演示完成!")


if __name__ == "__main__":
    main()