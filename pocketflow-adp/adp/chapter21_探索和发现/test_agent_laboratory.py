#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证Agent Laboratory框架的基本功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from exploration_discovery import (
    ReviewersAgent,
    ProfessorAgent,
    PostdocAgent,
    MLEngineerAgent,
    SoftwareEngineerAgent,
    AgentLaboratory,
    Message
)


async def test_individual_agents():
    """测试各个独立Agent的基本功能"""
    print("===== 测试独立Agent功能 =====")
    
    # 测试ReviewersAgent
    print("\n测试 ReviewersAgent...")
    reviewer = ReviewersAgent()
    review_response = await reviewer.process(Message(content={
        "research_content": "这是一个关于人工智能在医疗领域应用的研究",
        "evaluation_criteria": ["创新性", "实用性"]
    }))
    print(f"ReviewersAgent 响应状态: {review_response.content.get('status')}")
    
    # 测试ProfessorAgent (使用简单主题)
    print("\n测试 ProfessorAgent...")
    professor = ProfessorAgent()
    professor_response = await professor.process(Message(content={
        "research_topic": "简单测试主题"
    }))
    print(f"ProfessorAgent 响应状态: {professor_response.content.get('status')}")
    
    # 测试MLEngineerAgent
    print("\n测试 MLEngineerAgent...")
    ml_engineer = MLEngineerAgent()
    ml_response = await ml_engineer.process(Message(content={
        "research_needs": "需要准备简单的测试数据集"
    }))
    print(f"MLEngineerAgent 响应状态: {ml_response.content.get('status')}")
    
    return {
        "reviewer_test": "passed" if review_response.content.get('status') else "failed",
        "professor_test": "passed" if professor_response.content.get('status') else "failed",
        "ml_engineer_test": "passed" if ml_response.content.get('status') else "failed"
    }


async def test_agent_laboratory_integration():
    """测试Agent Laboratory框架的集成功能"""
    print("\n===== 测试Agent Laboratory集成功能 =====")
    
    # 创建一个简化版本的流水线测试
    lab = AgentLaboratory()
    
    # 测试Agent注册情况
    print("\n检查已注册的Agent...")
    agent_names = [agent.name for agent in lab.agents]
    print(f"已注册的Agent: {', '.join(agent_names)}")
    
    # 验证所有必需的Agent都已注册
    required_agents = [
        "ReviewersAgent",
        "ProfessorAgent",
        "PostdocAgent",
        "MLEngineerAgent",
        "SoftwareEngineerAgent"
    ]
    
    registration_status = {}
    for agent_name in required_agents:
        registration_status[agent_name] = "registered" if agent_name in agent_names else "missing"
    
    print("\nAgent注册状态:")
    for agent_name, status in registration_status.items():
        print(f"  - {agent_name}: {status}")
    
    return registration_status


async def run_validation():
    """运行完整的验证测试"""
    print("开始验证 Chapter 21: 探索和发现 实现...")
    
    # 测试独立Agent
    individual_test_results = await test_individual_agents()
    
    # 测试集成功能
    integration_test_results = await test_agent_laboratory_integration()
    
    # 生成验证报告
    print("\n===== 验证报告 =====")
    print("独立Agent测试结果:")
    for agent, result in individual_test_results.items():
        print(f"  - {agent.replace('_test', '')}: {result}")
    
    print("\n集成测试结果:")
    all_registered = all(status == "registered" for status in integration_test_results.values())
    print(f"  - 所有必需Agent注册: {'成功' if all_registered else '失败'}")
    
    # 验证目录结构和文件
    print("\n验证目录结构和文件:")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    expected_files = [
        "exploration_discovery.py",
        "README.md",
        "requirements.txt",
        "test_agent_laboratory.py"
    ]
    
    file_status = {}
    for file in expected_files:
        file_path = os.path.join(current_dir, file)
        file_status[file] = "exists" if os.path.exists(file_path) else "missing"
    
    for file, status in file_status.items():
        print(f"  - {file}: {status}")
    
    all_files_exist = all(status == "exists" for status in file_status.values())
    
    # 整体验证结果
    print("\n===== 整体验证结果 =====")
    if all_files_exist and all_registered:
        print("✅ 验证通过: Chapter 21 实现符合要求!")
    else:
        print("❌ 验证失败: 请检查缺失的组件或错误")


if __name__ == "__main__":
    try:
        asyncio.run(run_validation())
    except Exception as e:
        print(f"验证过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()