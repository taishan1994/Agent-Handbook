"""
Chapter 12: Exception Handling and Recovery - Demo Script
演示异常处理和恢复功能的脚本
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from flow import create_exception_handling_flow
from nodes import PrimaryHandler, FallbackHandler, ResponseAgent
from pocketflow import Flow


def demo_exception_handling():
    """演示异常处理和恢复功能"""
    print("=" * 60)
    print("Chapter 12: 异常处理和恢复模式演示")
    print("=" * 60)
    
    # 创建高失败率的流程以演示异常处理
    primary = PrimaryHandler(failure_rate=0.8)  # 80%失败率
    fallback = FallbackHandler(max_retries=3)
    response = ResponseAgent()
    
    # 连接节点
    primary - "fallback" >> fallback
    fallback - "retry" >> primary
    primary - "response" >> response
    fallback - "response" >> response
    
    # 创建流程
    flow = Flow(start=primary)
    
    # 准备数据
    shared_data = {
        "question": "刘翔获得了多少次世界冠军？",
        "context": "用户是一位体育爱好者，希望了解中国田径运动员的详细信息",
        "retry_count": 0
    }
    
    # 运行流程
    print("\n🚀 开始执行高失败率流程 (80%失败率)")
    print(f"问题: {shared_data['question']}")
    print("=" * 50)
    
    flow.run(shared_data)
    
    print("=" * 50)
    print("🏁 流程执行完成")
    print(f"处理成功: {'是' if shared_data.get('processing_success', False) else '否'}")
    print(f"重试次数: {shared_data.get('retry_count', 0)}")
    
    # 打印最终响应
    final_response = shared_data.get("final_response", "")
    print("\n📋 最终响应:")
    print(final_response)
    
    # 分析处理过程
    print("\n📊 处理过程分析:")
    if shared_data.get("retry_count", 0) > 0:
        print(f"- 经过了 {shared_data.get('retry_count', 0)} 次重试")
        if "last_recovery" in shared_data:
            print(f"- 最后使用的恢复策略: {shared_data['last_recovery']}")
    else:
        print("- 未经重试，一次成功")
    
    if "last_error" in shared_data:
        error = shared_data["last_error"]
        print(f"- 最后遇到的错误: {error.get('error_type', 'unknown')}")
        print(f"- 错误信息: {error.get('error_message', 'no message')}")
    
    return shared_data


def demo_multiple_scenarios():
    """演示多种场景下的异常处理和恢复"""
    print("\n" + "=" * 60)
    print("多种场景演示")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "低失败率场景",
            "failure_rate": 0.2,
            "question": "刘翔获得了多少次世界冠军？"
        },
        {
            "name": "高失败率场景",
            "failure_rate": 0.8,
            "question": "刘翔的运动生涯有哪些重要时刻？"
        },
        {
            "name": "极高失败率场景",
            "failure_rate": 0.95,
            "question": "刘翔对中国田径运动有什么影响？"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔸 {scenario['name']} (失败率: {scenario['failure_rate'] * 100}%)")
        print("-" * 40)
        
        # 创建流程
        primary = PrimaryHandler(failure_rate=scenario["failure_rate"])
        fallback = FallbackHandler(max_retries=3)
        response = ResponseAgent()
        
        # 连接节点
        primary - "fallback" >> fallback
        fallback - "retry" >> primary
        primary - "response" >> response
        fallback - "response" >> response
        
        # 创建流程
        flow = Flow(start=primary)
        
        # 准备数据
        shared_data = {
            "question": scenario["question"],
            "context": "",
            "retry_count": 0
        }
        
        # 运行流程
        flow.run(shared_data)
        
        # 打印结果摘要
        success = shared_data.get("processing_success", False)
        retry_count = shared_data.get("retry_count", 0)
        
        print(f"结果: {'成功' if success else '失败'}")
        print(f"重试次数: {retry_count}")
        
        if not success and "final_error" in shared_data:
            print(f"失败原因: {shared_data['final_error']}")


def main():
    """主函数"""
    print("Chapter 12: 异常处理和恢复模式 - PocketFlow实现演示")
    
    # 演示基本异常处理和恢复
    demo_exception_handling()
    
    # 演示多种场景
    demo_multiple_scenarios()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()