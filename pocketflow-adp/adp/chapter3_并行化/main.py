#!/usr/bin/env python3
"""
Chapter 3: Parallelization with PocketFlow
演示如何使用PocketFlow实现并行化模式
"""

import sys
import os
import time
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from flow import parallel_flow

async def run_parallelization_example():
    """
    运行并行化示例
    """
    print("=== Chapter 3: Parallelization with PocketFlow ===\n")
    
    # 示例主题
    topic = "太空探索的历史"
    
    print(f"输入主题: {topic}\n")
    
    # 初始化共享状态
    shared_state = {"topic": topic}
    
    # 执行异步流程并测量时间
    print("执行并行化流程...")
    start_time = time.time()
    await parallel_flow._run_async(shared_state)
    end_time = time.time()
    parallel_time = end_time - start_time
    
    # 显示中间结果
    print("\n=== 并行处理结果 ===")
    print("1. 主题总结:")
    print(f"   {shared_state['summary']}\n")
    
    print("2. 相关问题:")
    print(f"   {shared_state['questions']}\n")
    
    print("3. 关键术语:")
    print(f"   {shared_state['key_terms']}\n")
    
    # 显示最终综合结果
    print("=== 最终综合结果 ===")
    print(shared_state['final_result'])
    
    return parallel_time

async def run_sequential_comparison_example():
    """
    运行顺序处理示例作为对比
    """
    print("\n\n=== 顺序处理对比示例 ===\n")
    
    # 示例主题
    topic = "太空探索的历史"
    
    print(f"输入主题: {topic}\n")
    
    # 初始化共享状态
    shared_state = {"topic": topic}
    
    # 顺序执行各任务（模拟非并行处理）并测量时间
    print("执行顺序处理流程...")
    start_time = time.time()
    
    # 导入LLM调用函数
    from utils.utils import call_llm_async
    
    # 顺序执行各个任务，使用与并行处理相同的提示词
    # 1. 总结
    prompt = f"请总结关于'{topic}'的核心内容，控制在200字以内。"
    shared_state["summary"] = await call_llm_async(prompt)
    
    # 2. 生成问题
    prompt = f"基于'{topic}'这个主题，生成5个有深度的问题。"
    shared_state["questions"] = await call_llm_async(prompt)
    
    # 3. 提取关键术语
    prompt = f"从'{topic}'中提取并解释10个关键术语。"
    shared_state["key_terms"] = await call_llm_async(prompt)
    
    # 4. 综合（使用与并行处理相同的提示词）
    summary = shared_state.get("summary", "无总结")
    questions = shared_state.get("questions", "无问题")
    terms = shared_state.get("key_terms", "无术语")
    
    prompt = f"""
    基于以下信息，提供一个全面的综合分析：
    
    主题总结：
    {summary}
    
    相关问题：
    {questions}
    
    关键术语：
    {terms}
    
    请提供一个结构化的综合分析，包括：
    1. 主题概述
    2. 关键见解
    3. 实际应用
    4. 未来展望
    """
    
    shared_state["final_result"] = await call_llm_async(prompt)
    
    end_time = time.time()
    sequential_time = end_time - start_time
    
    # 显示结果
    print("\n=== 顺序处理结果 ===")
    print("1. 主题总结:")
    print(f"   {shared_state['summary']}\n")
    
    print("2. 相关问题:")
    print(f"   {shared_state['questions']}\n")
    
    print("3. 关键术语:")
    print(f"   {shared_state['key_terms']}\n")
    
    # 显示最终综合结果
    print("=== 最终综合结果 ===")
    print(shared_state['final_result'])
    
    return sequential_time

async def main():
    """
    主函数：运行并行化和顺序处理示例
    """
    # 运行并行化示例
    parallel_time = await run_parallelization_example()
    
    # 运行顺序处理对比示例
    sequential_time = await run_sequential_comparison_example()
    
    print("\n=== 性能对比 ===")
    print(f"并行处理时间: {parallel_time:.2f} 秒")
    print(f"顺序处理时间: {sequential_time:.2f} 秒")
    
    if sequential_time > 0:
        speedup = sequential_time / parallel_time
        print(f"加速比: {speedup:.2f}x")
        print(f"效率提升: {((speedup - 1) * 100):.1f}%")
    
    print("\n=== 总结 ===")
    print("并行化模式允许同时执行多个独立任务，从而显著提高处理效率。")
    print("在涉及多个LLM调用的场景中，并行化可以减少总体等待时间，")
    print("特别是在处理需要等待外部API响应的任务时效果更加明显。")

if __name__ == "__main__":
    asyncio.run(main())