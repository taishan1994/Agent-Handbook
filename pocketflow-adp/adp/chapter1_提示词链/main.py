#!/usr/bin/env python3
"""
Chapter 1: Prompt Chaining with PocketFlow
演示如何使用PocketFlow实现提示词链模式
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from flow import spec_flow

def run_prompt_chaining_example():
    """
    运行提示词链示例
    """
    print("=== Chapter 1: Prompt Chaining with PocketFlow ===\n")
    
    # 示例输入文本
    input_text = "新款笔记本电脑型号配备 3.5 GHz 八核处理器、16GB 内存和 1TB NVMe 固态硬盘。"
    
    print("输入文本:")
    print(f"  {input_text}\n")
    
    # 初始化共享状态
    shared_state = {"input_text": input_text}
    
    # 执行流程
    print("执行提示词链流程...")
    spec_flow.run(shared_state)
    
    # 显示中间结果
    print("\n=== 中间结果 ===")
    print("1. 提取的技术规格:")
    print(f"   {shared_state['extracted_specs']}\n")
    
    print("2. 转换的JSON格式:")
    print(f"   {shared_state['json_output']}\n")
    
    print("3. 验证后的最终结果:")
    print(f"   {shared_state['final_result']}\n")
    
    # 尝试解析JSON
    try:
        final_json = json.loads(shared_state['final_result'])
        print("=== 解析后的JSON对象 ===")
        print(json.dumps(final_json, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("最终结果不是有效的JSON格式")

if __name__ == "__main__":
    run_prompt_chaining_example()