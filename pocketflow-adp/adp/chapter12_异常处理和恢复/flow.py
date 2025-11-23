"""
Chapter 12: Exception Handling and Recovery - Flow Implementation
使用PocketFlow实现的异常处理和恢复模式流程
"""

import sys
import os

# 添加PocketFlow路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

from pocketflow import Flow
from nodes import PrimaryHandler, FallbackHandler, ResponseAgent


def create_exception_handling_flow():
    """
    创建异常处理和恢复流程
    
    这个流程实现了Chapter 12中描述的异常处理和恢复模式：
    1. PrimaryHandler - 执行主要处理逻辑，可能失败
    2. FallbackHandler - 处理异常并尝试恢复
    3. ResponseAgent - 生成最终响应
    
    流程图:
    PrimaryHandler --[失败]--> FallbackHandler --[恢复成功]--> PrimaryHandler
                     |                                  |
                     |                                  |
                     +------[成功]----------------------> ResponseAgent
                                                        |
                                                        +----[结束]----> End
    """
    
    # 创建节点实例
    primary_handler = PrimaryHandler(failure_rate=0.3)  # 30%失败率
    fallback_handler = FallbackHandler(max_retries=3)  # 最大重试3次
    response_agent = ResponseAgent()
    
    # 连接节点形成流程
    # PrimaryHandler失败时转到FallbackHandler
    primary_handler - "fallback" >> fallback_handler
    
    # FallbackHandler恢复成功时重试PrimaryHandler
    fallback_handler - "retry" >> primary_handler
    
    # PrimaryHandler成功时转到ResponseAgent
    primary_handler - "response" >> response_agent
    
    # FallbackHandler无法恢复时也转到ResponseAgent
    fallback_handler - "response" >> response_agent
    
    # 创建并返回流程，从PrimaryHandler开始
    return Flow(start=primary_handler)


def run_exception_handling_example(question, context=""):
    """
    运行异常处理和恢复示例
    
    Args:
        question: 用户问题
        context: 上下文信息
        
    Returns:
        dict: 包含处理结果和响应的字典
    """
    # 创建流程
    flow = create_exception_handling_flow()
    
    # 准备共享数据
    shared_data = {
        "question": question,
        "context": context,
        "retry_count": 0
    }
    
    # 执行流程
    print("🚀 开始执行异常处理和恢复流程")
    print(f"问题: {question}")
    print("=" * 50)
    
    # 执行流程并获取共享数据
    flow.run(shared_data)
    
    print("=" * 50)
    print("🏁 流程执行完成")
    print(f"处理成功: {'是' if shared_data.get('processing_success', False) else '否'}")
    print(f"重试次数: {shared_data.get('retry_count', 0)}")
    
    # 打印最终响应
    final_response = shared_data.get("final_response", "")
    print("\n📋 最终响应:")
    print(final_response)
    
    return shared_data


if __name__ == "__main__":
    # 示例问题
    example_question = "刘翔获得了多少次世界冠军？"
    
    # 运行示例
    run_exception_handling_example(example_question)