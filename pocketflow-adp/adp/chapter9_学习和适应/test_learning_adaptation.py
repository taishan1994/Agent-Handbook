"""
学习和适应模式 - 实验脚本

本脚本用于测试和演示Chapter 9中实现的学习和适应模式
"""

import sys
import os
import asyncio

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from learning_adaptation import (
    LearningFlow, 
    EvolutionFlow,
    AdaptiveAgentFlow,
    run_reinforcement_learning_example,
    run_supervised_learning_example,
    run_self_evolution_example,
    run_adaptive_agent_example
)


def test_reinforcement_learning():
    """测试强化学习"""
    print("=" * 50)
    print("测试强化学习模式")
    print("=" * 50)
    
    # 创建强化学习流程
    rl_flow = LearningFlow(learning_type="reinforcement")
    
    # 共享状态
    shared_state = {}
    
    # 运行多轮学习
    for episode in range(5):  # 运行5轮
        print(f"\n--- Episode {episode+1} ---")
        shared_state["episode_count"] = episode + 1
        
        # 运行环境节点
        env_result = rl_flow.environment.run(shared_state)
        print(f"环境状态: {env_result}")
        
        # 运行智能体节点
        agent_result = rl_flow.agent.run(shared_state)
        print(f"智能体动作: {agent_result}")
        
        # 检查是否结束
        env_state = shared_state.get("environment_state", {})
        if env_state.get("done", False):
            print("环境结束")
            break
    
    # 显示Q表
    agent_state = shared_state.get("agent_state", {})
    q_table = agent_state.get("q_table", {})
    print("\n最终Q表:")
    for state, actions in list(q_table.items())[:3]:  # 只显示前3个状态
        print(f"{state}: {actions}")
    
    print("\n强化学习测试完成\n")


def test_supervised_learning():
    """测试监督学习"""
    print("=" * 50)
    print("测试监督学习模式")
    print("=" * 50)
    
    # 创建监督学习流程
    sl_flow = LearningFlow(learning_type="supervised")
    
    # 准备训练数据
    training_data = [
        {"features": [1.0, 2.0], "label": 3.0},
        {"features": [2.0, 3.0], "label": 5.0},
        {"features": [3.0, 4.0], "label": 7.0},
        {"features": [4.0, 5.0], "label": 9.0},
        {"features": [5.0, 6.0], "label": 11.0}
    ]
    
    # 共享状态
    shared_state = {"training_examples": training_data}
    
    # 运行流程
    result = sl_flow.run(shared_state)
    print(f"结果: {result}")
    
    # 显示模型
    model = shared_state.get("model")
    print(f"模型参数: {model}")
    
    print("\n监督学习测试完成\n")


async def test_self_evolution():
    """测试自我进化模式"""
    print("\n=== 测试自我进化模式 ===")
    
    # 初始化进化流程
    evolution_flow = EvolutionFlow()
    
    # 设置共享状态
    shared_state = {
        "initial_program": "def hello_world(): print('Hello, World!')",
        "population_size": 20,
        "mutation_rate": 0.1,
        "crossover_rate": 0.7,
        "generations": 10
    }
    
    # 运行进化流程
    result = await evolution_flow.run_async(shared_state)
    print(f"进化结果: {result}")
    
    # 显示最佳程序
    best_program = shared_state.get("evolved_program")
    fitness = shared_state.get("fitness", 0)
    generation = shared_state.get("generation", 0)
    
    print(f"最佳程序适应度: {fitness:.2f}")
    print(f"进化代数: {generation}")
    print(f"最佳程序: {best_program}")


async def test_adaptive_agent():
    """测试自适应智能体"""
    print("=" * 50)
    print("测试自适应智能体模式")
    print("=" * 50)
    
    # 创建自适应智能体流程
    adaptive_flow = AdaptiveAgentFlow()
    
    # 共享状态
    shared_state = {
        "query": "强化学习在机器人控制中的最新应用"
    }
    
    # 运行流程
    result = await adaptive_flow.run_async(shared_state)
    print(f"结果: {result}")
    
    # 显示分析结果
    analysis = shared_state.get("analysis", "")
    learning_result = shared_state.get("learning_result", "")
    adaptation_result = shared_state.get("adaptation_result", "")
    
    print(f"\n分析结果: {analysis[:200]}...")  # 只显示前200个字符
    print(f"\n学习结果: {learning_result[:200]}...")  # 只显示前200个字符
    print(f"\n适应结果: {adaptation_result[:200]}...")  # 只显示前200个字符
    
    print("\n自适应智能体测试完成\n")


async def main():
    """主函数，运行所有测试"""
    print("开始测试Chapter 9 - 学习和适应模式\n")
    
    # 测试强化学习
    test_reinforcement_learning()
    
    # 测试监督学习
    test_supervised_learning()
    
    # 测试自我进化
    await test_self_evolution()
    
    # 测试自适应智能体
    await test_adaptive_agent()
    
    print("所有测试完成!")


if __name__ == "__main__":
    asyncio.run(main())