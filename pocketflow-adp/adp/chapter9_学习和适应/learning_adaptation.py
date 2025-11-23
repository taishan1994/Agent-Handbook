"""
学习和适应模式 - 使用PocketFlow实现

本模块实现了Chapter 9中描述的学习和适应模式，包括:
1. 强化学习
2. 监督学习
3. 无监督学习
4. 自我进化
"""

import sys
import os
import json
import random
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

# 添加PocketFlow路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../PocketFlow'))

# 添加utils路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))

from pocketflow import Flow, Node, AsyncNode, AsyncFlow
from utils import call_llm, call_llm_async
from exa_search_main import search_web_exa


class EnvironmentNode(Node):
    """环境节点，模拟智能体与环境的交互"""
    
    def __init__(self, environment_type="simple"):
        super().__init__()
        self.environment_type = environment_type
        self.state = None
        self.step_count = 0
        
    def prep(self, shared):
        """准备环境状态"""
        if self.environment_type == "simple":
            # 简单环境：随机生成状态和奖励
            self.state = {
                "current_state": f"state_{random.randint(1, 10)}",
                "available_actions": ["action_1", "action_2", "action_3"],
                "step": self.step_count
            }
            self.step_count += 1
        elif self.environment_type == "web_search":
            # 网络搜索环境
            query = shared.get("query", "默认查询")
            self.state = {
                "query": query,
                "search_results": None,
                "step": self.step_count
            }
            self.step_count += 1
        return self.state
    
    def exec(self, prep_res):
        """执行环境交互"""
        if self.environment_type == "simple":
            # 简单环境：随机生成奖励
            action = prep_res.get("selected_action", "action_1")
            reward = random.uniform(-1, 1)
            next_state = f"state_{random.randint(1, 10)}"
            done = random.random() < 0.1  # 10%概率结束
            
            return {
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "done": done,
                "current_state": next_state,
                "available_actions": ["action_1", "action_2", "action_3"]
            }
        elif self.environment_type == "web_search":
            # 网络搜索环境
            query = prep_res.get("query", "默认查询")
            try:
                search_results = search_web_exa(query)
                return {
                    "query": query,
                    "search_results": search_results,
                    "success": True
                }
            except Exception as e:
                return {
                    "query": query,
                    "search_results": None,
                    "error": str(e),
                    "success": False
                }
    
    def post(self, shared, prep_res, exec_res):
        """后处理，更新共享状态"""
        shared["environment_state"] = exec_res
        return "default"


class RLAgentNode(Node):
    """强化学习智能体节点"""
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        super().__init__()
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table = {}  # 状态-动作值表
        self.last_state = None
        self.last_action = None
        
    def prep(self, shared):
        """准备智能体状态"""
        environment_state = shared.get("environment_state", {})
        current_state = environment_state.get("current_state", "state_1")
        available_actions = environment_state.get("available_actions", ["action_1"])
        
        return {
            "current_state": current_state,
            "available_actions": available_actions,
            "reward": environment_state.get("reward"),
            "next_state": environment_state.get("next_state"),
            "done": environment_state.get("done", False)
        }
    
    def exec(self, prep_res):
        """执行智能体决策和学习"""
        current_state = prep_res["current_state"]
        available_actions = prep_res["available_actions"]
        reward = prep_res.get("reward")
        next_state = prep_res.get("next_state")
        done = prep_res.get("done", False)
        
        # 初始化Q表
        if current_state not in self.q_table:
            self.q_table[current_state] = {action: 0.0 for action in available_actions}
        
        if next_state and next_state not in self.q_table:
            self.q_table[next_state] = {action: 0.0 for action in available_actions}
        
        # 选择动作 (ε-贪婪策略)
        if random.random() < self.epsilon:
            # 探索：随机选择动作
            action = random.choice(available_actions)
        else:
            # 利用：选择Q值最高的动作
            action = max(available_actions, key=lambda a: self.q_table[current_state][a])
        
        # 更新Q值 (如果有前一个状态和动作)
        if self.last_state is not None and self.last_action is not None and reward is not None:
            old_value = self.q_table[self.last_state][self.last_action]
            next_max = max(self.q_table[next_state].values()) if next_state else 0
            new_value = old_value + self.learning_rate * (reward + self.discount_factor * next_max - old_value)
            self.q_table[self.last_state][self.last_action] = new_value
        
        # 保存当前状态和动作
        self.last_state = current_state
        self.last_action = action
        
        return {
            "selected_action": action,
            "q_table": self.q_table,
            "learning_update": True
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理，更新共享状态"""
        shared["agent_state"] = exec_res
        shared["selected_action"] = exec_res["selected_action"]
        return "default"


class SupervisedLearningNode(Node):
    """监督学习节点"""
    
    def __init__(self, model_type="simple"):
        super().__init__()
        self.model_type = model_type
        self.training_data = []
        self.model = None
        
    def prep(self, shared):
        """准备训练数据"""
        if "training_examples" in shared:
            self.training_data = shared["training_examples"]
        
        return {
            "training_data": self.training_data,
            "model_type": self.model_type
        }
    
    def exec(self, prep_res):
        """执行监督学习"""
        training_data = prep_res["training_data"]
        model_type = prep_res["model_type"]
        
        if not training_data:
            return {"error": "没有训练数据"}
        
        if model_type == "simple":
            # 简单的线性回归模拟
            # 提取特征和标签
            features = [example["features"] for example in training_data]
            labels = [example["label"] for example in training_data]
            
            # 模拟训练过程
            weights = [random.uniform(-1, 1) for _ in range(len(features[0]) if features else 1)]
            bias = random.uniform(-1, 1)
            
            # 模拟训练迭代
            for _ in range(10):
                for i, feature in enumerate(features):
                    prediction = sum(w * f for w, f in zip(weights, feature)) + bias
                    error = labels[i] - prediction
                    # 更新权重
                    weights = [w + 0.01 * error * f for w, f in zip(weights, feature)]
                    bias += 0.01 * error
            
            self.model = {"weights": weights, "bias": bias}
            
            return {
                "model": self.model,
                "training_samples": len(training_data),
                "model_type": model_type
            }
        
        return {"error": "不支持的模型类型"}
    
    def post(self, shared, prep_res, exec_res):
        """后处理，更新共享状态"""
        shared["model"] = exec_res.get("model")
        shared["training_result"] = exec_res
        return "default"


class SelfEvolutionNode(AsyncNode):
    """自我进化节点"""
    
    def __init__(self, evolution_strategy="mutation"):
        super().__init__()
        self.evolution_strategy = evolution_strategy
        self.generation = 0
        self.population = []
        self.fitness_scores = []
        
    async def prep_async(self, shared):
        """准备进化环境"""
        # 初始化种群
        initial_program = shared.get("initial_program", "def hello_world(): print('Hello, World!')")
        
        # 如果初始程序是字符串，转换为字典格式
        if isinstance(initial_program, str):
            initial_program = {"code": initial_program}
        
        self.population = [initial_program.copy()]
        
        # 生成初始变异
        for _ in range(4):  # 创建5个个体的种群
            mutated = await self.mutate_program(initial_program)
            self.population.append(mutated)
        
        return {
            "population": self.population,
            "generation": self.generation,
            "evolution_strategy": self.evolution_strategy
        }
    
    async def exec_async(self, prep_res):
        """执行进化过程"""
        population = prep_res["population"]
        generation = prep_res["generation"]
        evolution_strategy = prep_res["evolution_strategy"]
        
        # 评估适应度
        self.fitness_scores = []
        for i, program in enumerate(population):
            fitness = await self.evaluate_fitness(program)
            self.fitness_scores.append(fitness)
        
        # 选择最佳个体
        best_idx = np.argmax(self.fitness_scores)
        best_program = population[best_idx]
        best_fitness = self.fitness_scores[best_idx]
        
        # 进化下一代
        if generation < 10:  # 限制进化代数
            new_population = [best_program]  # 精英保留
            
            # 生成新个体
            while len(new_population) < len(population):
                if evolution_strategy == "mutation":
                    # 变异
                    parent = random.choice(population[:3])  # 从前3个最佳个体中选择
                    mutated = await self.mutate_program(parent)
                    new_population.append(mutated)
                elif evolution_strategy == "crossover":
                    # 交叉
                    parent1 = random.choice(population[:3])
                    parent2 = random.choice(population[:3])
                    child = await self.crossover_programs(parent1, parent2)
                    new_population.append(child)
            
            self.population = new_population
            self.generation += 1
            
            return {
                "best_program": best_program,
                "best_fitness": best_fitness,
                "generation": generation,
                "evolved": True
            }
        else:
            return {
                "best_program": best_program,
                "best_fitness": best_fitness,
                "generation": generation,
                "evolved": False,
                "converged": True
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理，更新共享状态"""
        shared["evolved_program"] = exec_res.get("best_program")
        shared["fitness"] = exec_res.get("best_fitness")
        shared["generation"] = exec_res.get("generation")
        shared["evolved"] = exec_res.get("evolved", False)
        shared["converged"] = exec_res.get("converged", False)
        return "default"
    
    async def mutate_program(self, program):
        """程序变异"""
        mutated = program.copy()
        
        # 随机选择变异类型
        mutation_type = random.choice(["add_instruction", "modify_instruction", "remove_instruction"])
        
        if mutation_type == "add_instruction" and len(mutated.get("instructions", [])) < 10:
            # 添加指令
            new_instruction = f"指令_{random.randint(1, 100)}"
            if "instructions" not in mutated:
                mutated["instructions"] = []
            mutated["instructions"].append(new_instruction)
        elif mutation_type == "modify_instruction" and mutated.get("instructions"):
            # 修改指令
            idx = random.randint(0, len(mutated["instructions"]) - 1)
            mutated["instructions"][idx] = f"修改后的指令_{random.randint(1, 100)}"
        elif mutation_type == "remove_instruction" and len(mutated.get("instructions", [])) > 1:
            # 删除指令
            idx = random.randint(0, len(mutated["instructions"]) - 1)
            mutated["instructions"].pop(idx)
        
        return mutated
    
    async def crossover_programs(self, program1, program2):
        """程序交叉"""
        child = {"instructions": []}
        
        # 从两个父代中随机选择指令
        instructions1 = program1.get("instructions", [])
        instructions2 = program2.get("instructions", [])
        
        # 随机交叉点
        max_len = min(len(instructions1), len(instructions2))
        if max_len > 0:
            crossover_point = random.randint(1, max_len)
            child["instructions"] = instructions1[:crossover_point] + instructions2[crossover_point:]
        
        return child
    
    async def evaluate_fitness(self, program):
        """评估程序适应度"""
        # 模拟适应度评估
        # 在实际应用中，这里会运行程序并评估其性能
        instructions = program.get("instructions", [])
        
        # 模拟评估：指令数量适中且包含特定指令的程序适应度更高
        fitness = 0.0
        
        # 指令数量评分
        if 3 <= len(instructions) <= 7:
            fitness += 0.5
        
        # 特定指令评分
        for instruction in instructions:
            if "指令_42" in instruction or "指令_73" in instruction:
                fitness += 0.2
        
        # 添加随机性
        fitness += random.uniform(0, 0.3)
        
        return min(fitness, 1.0)  # 限制在[0,1]范围内


class EvolutionFlow(AsyncFlow):
    """进化流程 - 专门用于自我进化"""
    
    def __init__(self):
        super().__init__()
        self.evolution = SelfEvolutionNode()
        self.start(self.evolution)
    
    async def prep_async(self, shared):
        """准备进化流程"""
        return {"initial_program": shared.get("initial_program")}
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理，更新共享状态"""
        program = shared.get("evolved_program")
        fitness = shared.get("fitness", 0)
        generation = shared.get("generation", 0)
        return f"自我进化完成，最佳程序适应度: {fitness:.2f}，进化代数: {generation}"


class LearningFlow(Flow):
    """学习流程"""
    
    def __init__(self, learning_type="reinforcement"):
        super().__init__()
        self.learning_type = learning_type
        
        # 创建节点
        if learning_type == "reinforcement":
            self.environment = EnvironmentNode("simple")
            self.agent = RLAgentNode()
            self.episode_count = 0
            
            # 设置流程
            self.start(self.environment)
            self.environment >> self.agent
            # 不设置循环，由外部控制
            
        elif learning_type == "supervised":
            self.learner = SupervisedLearningNode()
            self.start(self.learner)
    
    def prep(self, shared):
        """准备学习流程"""
        shared["learning_type"] = self.learning_type
        shared["episode_count"] = shared.get("episode_count", 0)
        shared["max_episodes"] = 50  # 最大学习轮数
        
        return {"learning_type": self.learning_type}
    
    def post(self, shared, prep_res, exec_res):
        """后处理，总结学习结果"""
        if self.learning_type == "reinforcement":
            return f"强化学习完成，共进行了 {shared.get('episode_count', 0)} 轮学习"
        elif self.learning_type == "supervised":
            model = shared.get("model")
            return f"监督学习完成，模型参数: {model}"
        
        return "学习完成"


class AdaptiveAgentFlow(AsyncFlow):
    """自适应智能体流程"""
    
    def __init__(self):
        super().__init__()
        
        # 创建节点
        self.search_node = WebSearchNode()
        self.analysis_node = AnalysisNode()
        self.learning_node = LearningNode()
        self.adaptation_node = AdaptationNode()
        
        # 设置流程
        self.start(self.search_node)
        self.search_node >> self.analysis_node
        self.analysis_node - "need_learning" >> self.learning_node
        self.learning_node >> self.adaptation_node
        self.analysis_node - "no_learning" >> self.adaptation_node
    
    async def prep_async(self, shared):
        """准备自适应智能体流程"""
        shared["iteration"] = 0
        shared["max_iterations"] = 5
        return {"initialized": True}
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理，总结自适应过程"""
        iterations = shared.get("iteration", 0)
        performance = shared.get("performance", [])
        return f"自适应智能体完成，共进行了 {iterations} 次迭代，性能变化: {performance}"


class WebSearchNode(AsyncNode):
    """网络搜索节点"""
    
    async def prep_async(self, shared):
        """准备搜索"""
        query = shared.get("query", "人工智能最新进展")
        return {"query": query}
    
    async def exec_async(self, prep_res):
        """执行搜索"""
        query = prep_res["query"]
        try:
            search_results = search_web_exa(query)
            return {
                "query": query,
                "search_results": search_results,
                "success": True
            }
        except Exception as e:
            return {
                "query": query,
                "search_results": None,
                "error": str(e),
                "success": False
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理"""
        shared["search_results"] = exec_res.get("search_results")
        shared["search_success"] = exec_res.get("success", False)
        return "default"


class AnalysisNode(AsyncNode):
    """分析节点"""
    
    async def prep_async(self, shared):
        """准备分析"""
        search_results = shared.get("search_results", "")
        return {"search_results": search_results}
    
    async def exec_async(self, prep_res):
        """执行分析"""
        search_results = prep_res["search_results"]
        
        if not search_results:
            return {"analysis": "无搜索结果", "need_learning": False}
        
        # 使用LLM分析搜索结果
        prompt = f"""
        请分析以下搜索结果，判断是否需要进一步学习：
        
        搜索结果：
        {search_results[:2000]}  # 限制长度
        
        请回答以下问题：
        1. 搜索结果是否提供了足够的信息？
        2. 是否存在知识缺口需要学习？
        3. 如果需要学习，应该学习什么内容？
        
        请以JSON格式回答，包含字段：
        - sufficient_info: true/false
        - knowledge_gaps: [] 列出知识缺口
        - learning_topics: [] 列出学习主题
        """
        
        try:
            analysis_result = await call_llm_async(prompt)
            # 简单解析JSON结果
            if "true" in analysis_result.lower():
                need_learning = False
            else:
                need_learning = True
            
            return {
                "analysis": analysis_result,
                "need_learning": need_learning
            }
        except Exception as e:
            return {
                "analysis": f"分析失败: {str(e)}",
                "need_learning": False
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理"""
        shared["analysis"] = exec_res.get("analysis")
        need_learning = exec_res.get("need_learning", False)
        return "need_learning" if need_learning else "no_learning"


class LearningNode(AsyncNode):
    """学习节点"""
    
    async def prep_async(self, shared):
        """准备学习"""
        analysis = shared.get("analysis", "")
        return {"analysis": analysis}
    
    async def exec_async(self, prep_res):
        """执行学习"""
        analysis = prep_res["analysis"]
        
        # 使用LLM进行学习
        prompt = f"""
        基于以下分析结果，请提供学习建议：
        
        分析结果：
        {analysis}
        
        请提供：
        1. 需要学习的关键概念
        2. 推荐的学习资源
        3. 学习策略建议
        """
        
        try:
            learning_result = await call_llm_async(prompt)
            return {
                "learning_result": learning_result,
                "success": True
            }
        except Exception as e:
            return {
                "learning_result": f"学习失败: {str(e)}",
                "success": False
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理"""
        shared["learning_result"] = exec_res.get("learning_result")
        shared["learning_success"] = exec_res.get("success", False)
        return "default"


class AdaptationNode(AsyncNode):
    """适应节点"""
    
    async def prep_async(self, shared):
        """准备适应"""
        learning_result = shared.get("learning_result", "")
        learning_success = shared.get("learning_success", False)
        return {
            "learning_result": learning_result,
            "learning_success": learning_success
        }
    
    async def exec_async(self, prep_res):
        """执行适应"""
        learning_result = prep_res["learning_result"]
        learning_success = prep_res["learning_success"]
        
        # 使用LLM生成适应策略
        prompt = f"""
        基于以下学习结果，请生成适应策略：
        
        学习结果：
        {learning_result}
        
        学习成功：{learning_success}
        
        请提供：
        1. 如何将新知识应用到当前任务
        2. 需要调整的策略或方法
        3. 适应后的行动计划
        """
        
        try:
            adaptation_result = await call_llm_async(prompt)
            return {
                "adaptation_result": adaptation_result,
                "success": True
            }
        except Exception as e:
            return {
                "adaptation_result": f"适应失败: {str(e)}",
                "success": False
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理"""
        shared["adaptation_result"] = exec_res.get("adaptation_result")
        shared["adaptation_success"] = exec_res.get("success", False)
        
        # 更新迭代计数
        iteration = shared.get("iteration", 0) + 1
        shared["iteration"] = iteration
        
        # 记录性能
        performance = shared.get("performance", [])
        performance.append({
            "iteration": iteration,
            "adaptation_success": exec_res.get("success", False)
        })
        shared["performance"] = performance
        
        # 判断是否继续迭代
        max_iterations = shared.get("max_iterations", 5)
        if iteration < max_iterations:
            return "continue"  # 继续迭代
        else:
            return "done"  # 结束


# 示例使用函数
def run_reinforcement_learning_example():
    """运行强化学习示例"""
    print("=== 强化学习示例 ===")
    
    # 创建强化学习流程
    rl_flow = LearningFlow(learning_type="reinforcement")
    
    # 共享状态
    shared_state = {}
    
    # 运行流程
    for episode in range(10):  # 运行10轮
        print(f"\n--- Episode {episode+1} ---")
        result = rl_flow.run(shared_state)
        print(f"结果: {result}")
        
        # 检查是否结束
        env_state = shared_state.get("environment_state", {})
        if env_state.get("done", False):
            print("环境结束")
            break
    
    # 显示Q表
    agent_state = shared_state.get("agent_state", {})
    q_table = agent_state.get("q_table", {})
    print("\n最终Q表:")
    for state, actions in q_table.items():
        print(f"{state}: {actions}")


def run_supervised_learning_example():
    """运行监督学习示例"""
    print("\n=== 监督学习示例 ===")
    
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


async def run_self_evolution_example():
    """运行自我进化示例"""
    print("\n=== 自我进化示例 ===")
    
    # 创建自我进化流程
    evolution_flow = LearningFlow(learning_type="evolution")
    
    # 初始程序
    initial_program = {
        "instructions": ["指令_1", "指令_2", "指令_3"]
    }
    
    # 共享状态
    shared_state = {"initial_program": initial_program}
    
    # 运行流程
    result = await evolution_flow.run_async(shared_state)
    print(f"结果: {result}")
    
    # 显示进化后的程序
    evolved_program = shared_state.get("evolved_program")
    fitness = shared_state.get("fitness", 0)
    generation = shared_state.get("generation", 0)
    
    print(f"进化代数: {generation}")
    print(f"最佳适应度: {fitness:.2f}")
    print(f"进化后的程序: {evolved_program}")


async def run_adaptive_agent_example():
    """运行自适应智能体示例"""
    print("\n=== 自适应智能体示例 ===")
    
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
    
    print(f"\n分析结果: {analysis}")
    print(f"\n学习结果: {learning_result}")
    print(f"\n适应结果: {adaptation_result}")


if __name__ == "__main__":
    # 运行所有示例
    run_reinforcement_learning_example()
    run_supervised_learning_example()
    
    # 异步示例
    import asyncio
    asyncio.run(run_self_evolution_example())
    asyncio.run(run_adaptive_agent_example())