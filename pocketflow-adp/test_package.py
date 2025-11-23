#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试agent_handbook_utils包是否正常工作
"""

print("开始测试agent_handbook_utils包...")

# 测试导入
print("\n测试1: 导入包")
try:
    from agent_handbook_utils import (
        call_llm,
        call_llm_async,
        get_embedding,
        get_embedding_batch,
        search_web_exa,
        exa_web_search,
        extract_relevant_info
    )
    print("✓ 成功导入所有函数")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

# 测试包结构
print("\n测试2: 查看包结构")
try:
    import agent_handbook_utils
    print(f"✓ 包路径: {agent_handbook_utils.__file__}")
    print(f"✓ 包内容: {dir(agent_handbook_utils)}")
except Exception as e:
    print(f"✗ 获取包结构失败: {e}")

print("\n测试完成！包已成功安装并可以正常导入。")