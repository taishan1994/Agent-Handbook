"""
辩论链(Chain of Debate, CoD)推理技术实现

辩论链是一种通过多轮辩论来提高推理质量的推理技术。
它模拟人类辩论过程，让多个角色从不同角度讨论一个问题，
通过辩论和反驳来发现问题的多个方面，最终得出更全面、更准确的结论。
"""

import sys
import os
import asyncio
import json
import random
from typing import Dict, List, Any, Optional, Tuple

# 添加utils路径以便导入
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from utils import call_llm, call_llm_async

from pocketflow import AsyncNode, AsyncFlow


class DebateAgent:
    """
    辩论代理
    
    表示参与辩论的一个角色，有特定的观点和立场。
    """
    
    def __init__(self, name: str, role: str, stance: str, description: str):
        """
        初始化辩论代理
        
        Args:
            name: 代理名称
            role: 代理角色
            stance: 代理立场
            description: 代理描述
        """
        self.name = name
        self.role = role
        self.stance = stance
        self.description = description
    
    def get_prompt(self, question: str, debate_history: List[Dict[str, str]], is_first: bool = False) -> str:
        """
        获取代理的提示词
        
        Args:
            question: 问题
            debate_history: 辩论历史
            is_first: 是否是第一个发言
            
        Returns:
            提示词
        """
        # 格式化辩论历史
        history_text = ""
        if not is_first and debate_history:
            history_parts = []
            for entry in debate_history:
                history_parts.append(f"{entry['agent_name']} ({entry['agent_role']}): {entry['argument']}")
            history_text = "\n".join(history_parts)
        
        prompt = f"""
你是{self.name}，一个{self.role}。你的立场是：{self.stance}。

描述：{self.description}

问题：{question}

{"之前的辩论：" if not is_first and debate_history else ""}
{history_text if not is_first and debate_history else ""}

请基于你的角色和立场，对上述问题提出你的观点。{"请回应之前的辩论，并提出你的反驳或支持观点。" if not is_first and debate_history else "请开始辩论，提出你的初始观点。"}

你的观点：
"""
        return prompt


class ChainOfDebateNode(AsyncNode):
    """
    辩论链节点
    
    实现多轮辩论过程，让多个角色从不同角度讨论一个问题。
    """
    
    def __init__(self, 
                 name: str = "ChainOfDebateNode",
                 max_rounds: int = 3,
                 agents: Optional[List[DebateAgent]] = None,
                 moderator_prompt: Optional[str] = None,
                 summary_prompt: Optional[str] = None,
                 max_retries: int = 1):
        """
        初始化辩论链节点
        
        Args:
            name: 节点名称
            max_rounds: 最大辩论轮数
            agents: 辩论代理列表
            moderator_prompt: 主持人提示模板
            summary_prompt: 总结提示模板
            max_retries: 最大重试次数
        """
        self.name = name
        self.max_rounds = max_rounds
        super().__init__(max_retries=max_retries)
        
        # 默认辩论代理
        if agents is None:
            self.agents = self._create_default_agents()
        else:
            self.agents = agents
        
        # 默认主持人提示模板
        self.moderator_prompt = moderator_prompt or """
你是一个辩论主持人，负责总结辩论过程并提出最终结论。

问题：{question}

辩论过程：
{debate_history}

请基于以上辩论过程，总结各方观点，并提出一个全面、平衡的结论。

总结：
"""
        
        # 默认总结提示模板
        self.summary_prompt = summary_prompt or """
你是一个辩论分析师，负责分析辩论过程并提取关键信息。

问题：{question}

辩论过程：
{debate_history}

请分析以上辩论过程，识别：
1. 各方的主要观点和论据
2. 观点之间的共识和分歧
3. 关键的论点和反驳
4. 可以得出的结论

分析：
"""
    
    def _create_default_agents(self) -> List[DebateAgent]:
        """
        创建默认辩论代理
        
        Returns:
            默认辩论代理列表
        """
        return [
            DebateAgent(
                name="支持者",
                role="积极支持者",
                stance="完全支持问题的正面观点",
                description="你总是从积极的角度看待问题，强调其优点和好处。"
            ),
            DebateAgent(
                name="批评者",
                role="批判性思考者",
                stance="持批判性观点，强调潜在问题和风险",
                description="你总是从批判的角度看待问题，指出其缺点和潜在风险。"
            ),
            DebateAgent(
                name="中立者",
                role="中立分析者",
                stance="保持中立，客观分析问题",
                description="你总是从中立的角度看待问题，客观分析其优缺点。"
            ),
        ]
    
    async def get_agent_argument(self, agent: DebateAgent, question: str, 
                                debate_history: List[Dict[str, str]], 
                                is_first: bool = False) -> str:
        """
        获取代理的论点
        
        Args:
            agent: 辩论代理
            question: 问题
            debate_history: 辩论历史
            is_first: 是否是第一个发言
            
        Returns:
            代理的论点
        """
        prompt = agent.get_prompt(question, debate_history, is_first)
        return await call_llm_async(prompt)
    
    async def moderate_debate(self, question: str, debate_history: List[Dict[str, str]]) -> str:
        """
        主持辩论并总结
        
        Args:
            question: 问题
            debate_history: 辩论历史
            
        Returns:
            辩论总结
        """
        # 格式化辩论历史
        history_parts = []
        for entry in debate_history:
            history_parts.append(f"{entry['agent_name']} ({entry['agent_role']}): {entry['argument']}")
        history_text = "\n".join(history_parts)
        
        prompt = self.moderator_prompt.format(
            question=question,
            debate_history=history_text
        )
        
        return await call_llm_async(prompt)
    
    async def analyze_debate(self, question: str, debate_history: List[Dict[str, str]]) -> str:
        """
        分析辩论过程
        
        Args:
            question: 问题
            debate_history: 辩论历史
            
        Returns:
            辩论分析
        """
        # 格式化辩论历史
        history_parts = []
        for entry in debate_history:
            history_parts.append(f"{entry['agent_name']} ({entry['agent_role']}): {entry['argument']}")
        history_text = "\n".join(history_parts)
        
        prompt = self.summary_prompt.format(
            question=question,
            debate_history=history_text
        )
        
        return await call_llm_async(prompt)
    
    async def prep_async(self, shared):
        """
        预处理方法，符合AsyncNode接口要求
        
        Args:
            shared: 共享状态数据
            
        Returns:
            共享状态数据
        """
        return shared
        
    async def post_async(self, shared, prep_res, exec_res):
        """
        后处理方法，符合AsyncNode接口要求
        
        Args:
            shared: 共享状态数据
            prep_res: 预处理结果
            exec_res: 执行结果
            
        Returns:
            返回字符串"default"以符合AsyncFlow的要求
        """
        print(f"[DEBUG] ChainOfDebateNode.post_async: exec_res type={type(exec_res)}")
        # 将执行结果存储在共享状态中
        if isinstance(exec_res, dict):
            shared['debate_result'] = exec_res
        # 返回字符串以符合AsyncFlow的要求
        return "default"
        
    async def exec_async(self, prep_res):
        """
        处理输入并生成辩论链推理结果
        
        Args:
            prep_res: 预处理结果，应包含'question'字段
            
        Returns:
            包含辩论链推理结果的字典
        """
        question = prep_res.get('question', '')
        if not question:
            return {
                'error': 'No question provided',
                'conclusion': '',
                'analysis': '',
                'debate_history': []
            }
        
        try:
            # 记录辩论历史
            debate_history = []
            
            # 进行多轮辩论
            for round_num in range(self.max_rounds):
                print(f"辩论轮次 {round_num+1}/{self.max_rounds}")
                
                # 每轮中每个代理依次发言
                for agent in self.agents:
                    print(f"  {agent.name} ({agent.role}) 发言...")
                    
                    # 获取代理的论点
                    is_first = (round_num == 0 and agent == self.agents[0])
                    argument = await self.get_agent_argument(
                        agent, question, debate_history, is_first
                    )
                    
                    # 记录论点
                    debate_history.append({
                        'round': round_num + 1,
                        'agent_name': agent.name,
                        'agent_role': agent.role,
                        'agent_stance': agent.stance,
                        'argument': argument
                    })
                    
                    print(f"    论点: {argument[:100]}...")
            
            # 主持辩论并总结
            print("主持辩论并总结...")
            conclusion = await self.moderate_debate(question, debate_history)
            
            # 分析辩论过程
            print("分析辩论过程...")
            analysis = await self.analyze_debate(question, debate_history)
            
            return {
                'question': question,
                'conclusion': conclusion,
                'analysis': analysis,
                'debate_history': debate_history,
                'error': None
            }
            
        except Exception as e:
            return {
                'question': question,
                'conclusion': '',
                'analysis': '',
                'debate_history': debate_history,
                'error': str(e)
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """
        后处理方法，符合AsyncNode接口要求
        
        Args:
            shared: 共享状态数据
            prep_res: prep_async的执行结果
            exec_res: exec_async的执行结果
            
        Returns:
            执行结果
        """
        # 将结果存储到共享数据中
        if 'cod_results' not in shared:
            shared['cod_results'] = []
        shared['cod_results'].append(exec_res)
        
        # 返回一个简单的字符串作为状态转换条件
        return "default"
    
    async def post_async(self, shared, prep_res, exec_res):
        """
        后处理方法，符合AsyncNode接口要求
        
        Args:
            shared: 共享状态数据
            prep_res: prep_async的执行结果
            exec_res: exec_async的执行结果
            
        Returns:
            执行结果
        """
        # 将结果存储到共享数据中
        if 'cod_results' not in shared:
            shared['cod_results'] = []
        shared['cod_results'].append(exec_res)
        
        # 返回一个简单的字符串作为状态转换条件
        return "default"


class GraphOfDebateNode(AsyncNode):
    """
    辩论图节点
    
    扩展辩论链为辩论图，允许代理之间进行更复杂的交互和辩论。
    """
    
    def __init__(self, 
                 name: str = "GraphOfDebateNode",
                 max_rounds: int = 3,
                 agents: Optional[List[DebateAgent]] = None,
                 moderator_prompt: Optional[str] = None,
                 summary_prompt: Optional[str] = None,
                 max_retries: int = 1):
        """
        初始化辩论图节点
        
        Args:
            name: 节点名称
            max_rounds: 最大辩论轮数
            agents: 辩论代理列表
            moderator_prompt: 主持人提示模板
            summary_prompt: 总结提示模板
            max_retries: 最大重试次数
        """
        super().__init__(name=name, max_retries=max_retries)
        self.max_rounds = max_rounds
        
        # 默认辩论代理
        if agents is None:
            self.agents = self._create_default_agents()
        else:
            self.agents = agents
        
        # 默认主持人提示模板
        self.moderator_prompt = moderator_prompt or """
你是一个辩论主持人，负责总结辩论过程并提出最终结论。

问题：{question}

辩论过程：
{debate_history}

请基于以上辩论过程，总结各方观点，并提出一个全面、平衡的结论。

总结：
"""
        
        # 默认总结提示模板
        self.summary_prompt = summary_prompt or """
你是一个辩论分析师，负责分析辩论过程并提取关键信息。

问题：{question}

辩论过程：
{debate_history}

请分析以上辩论过程，识别：
1. 各方的主要观点和论据
2. 观点之间的共识和分歧
3. 关键的论点和反驳
4. 可以得出的结论

分析：
"""
    
    def _create_default_agents(self) -> List[DebateAgent]:
        """
        创建默认辩论代理
        
        Returns:
            默认辩论代理列表
        """
        return [
            DebateAgent(
                name="支持者",
                role="积极支持者",
                stance="完全支持问题的正面观点",
                description="你总是从积极的角度看待问题，强调其优点和好处。"
            ),
            DebateAgent(
                name="批评者",
                role="批判性思考者",
                stance="持批判性观点，强调潜在问题和风险",
                description="你总是从批判的角度看待问题，指出其缺点和潜在风险。"
            ),
            DebateAgent(
                name="中立者",
                role="中立分析者",
                stance="保持中立，客观分析问题",
                description="你总是从中立的角度看待问题，客观分析其优缺点。"
            ),
            DebateAgent(
                name="实用主义者",
                role="实用主义者",
                stance="从实用角度看待问题，关注实际应用和可行性",
                description="你总是从实用的角度看待问题，关注其实际应用和可行性。"
            ),
        ]
    
    async def get_agent_argument(self, agent: DebateAgent, question: str, 
                                debate_history: List[Dict[str, str]], 
                                target_agent: Optional[DebateAgent] = None,
                                is_first: bool = False) -> str:
        """
        获取代理的论点
        
        Args:
            agent: 辩论代理
            question: 问题
            debate_history: 辩论历史
            target_agent: 目标代理（用于直接回应）
            is_first: 是否是第一个发言
            
        Returns:
            代理的论点
        """
        # 格式化辩论历史
        history_text = ""
        if not is_first and debate_history:
            history_parts = []
            for entry in debate_history:
                history_parts.append(f"{entry['agent_name']} ({entry['agent_role']}): {entry['argument']}")
            history_text = "\n".join(history_parts)
        
        target_text = f"\n请特别回应{target_agent.name}的观点。" if target_agent else ""
        
        prompt = f"""
你是{agent.name}，一个{agent.role}。你的立场是：{agent.stance}。

描述：{agent.description}

问题：{question}

{"之前的辩论：" if not is_first and debate_history else ""}
{history_text if not is_first and debate_history else ""}

请基于你的角色和立场，对上述问题提出你的观点。{"请回应之前的辩论，并提出你的反驳或支持观点。" if not is_first and debate_history else "请开始辩论，提出你的初始观点。"}{target_text}

你的观点：
"""
        return await call_llm_async(prompt)
    
    async def moderate_debate(self, question: str, debate_history: List[Dict[str, str]]) -> str:
        """
        主持辩论并总结
        
        Args:
            question: 问题
            debate_history: 辩论历史
            
        Returns:
            辩论总结
        """
        # 格式化辩论历史
        history_parts = []
        for entry in debate_history:
            history_parts.append(f"{entry['agent_name']} ({entry['agent_role']}): {entry['argument']}")
        history_text = "\n".join(history_parts)
        
        prompt = self.moderator_prompt.format(
            question=question,
            debate_history=history_text
        )
        
        return await call_llm_async(prompt)
    
    async def analyze_debate(self, question: str, debate_history: List[Dict[str, str]]) -> str:
        """
        分析辩论过程
        
        Args:
            question: 问题
            debate_history: 辩论历史
            
        Returns:
            辩论分析
        """
        # 格式化辩论历史
        history_parts = []
        for entry in debate_history:
            history_parts.append(f"{entry['agent_name']} ({entry['agent_role']}): {entry['argument']}")
        history_text = "\n".join(history_parts)
        
        prompt = self.summary_prompt.format(
            question=question,
            debate_history=history_text
        )
        
        return await call_llm_async(prompt)
    
    async def prep_async(self, shared):
        """
        预处理方法，符合AsyncNode接口要求
        
        Args:
            shared: 共享状态数据
            
        Returns:
            共享状态数据
        """
        return shared
        
    async def exec_async(self, prep_res):
        """
        处理输入并生成辩论图推理结果
        
        Args:
            prep_res: 预处理结果，应包含'question'字段
            
        Returns:
            包含辩论图推理结果的字典
        """
        question = prep_res.get('question', '')
        if not question:
            return {
                'error': 'No question provided',
                'conclusion': '',
                'analysis': '',
                'debate_history': []
            }
        
        try:
            # 记录辩论历史
            debate_history = []
            
            # 进行多轮辩论
            for round_num in range(self.max_rounds):
                print(f"辩论轮次 {round_num+1}/{self.max_rounds}")
                
                # 第一轮：每个代理依次发言
                if round_num == 0:
                    for agent in self.agents:
                        print(f"  {agent.name} ({agent.role}) 发言...")
                        
                        # 获取代理的论点
                        is_first = (agent == self.agents[0])
                        argument = await self.get_agent_argument(
                            agent, question, debate_history, is_first=is_first
                        )
                        
                        # 记录论点
                        debate_history.append({
                            'round': round_num + 1,
                            'agent_name': agent.name,
                            'agent_role': agent.role,
                            'agent_stance': agent.stance,
                            'argument': argument,
                            'target_agent': None
                        })
                        
                        print(f"    论点: {argument[:100]}...")
                else:
                    # 后续轮次：随机选择代理进行辩论
                    for i, agent in enumerate(self.agents):
                        # 随机选择一个目标代理进行回应
                        other_agents = [a for a in self.agents if a != agent]
                        target_agent = random.choice(other_agents)
                        
                        print(f"  {agent.name} ({agent.role}) 回应 {target_agent.name}...")
                        
                        # 获取代理的论点
                        argument = await self.get_agent_argument(
                            agent, question, debate_history, target_agent=target_agent
                        )
                        
                        # 记录论点
                        debate_history.append({
                            'round': round_num + 1,
                            'agent_name': agent.name,
                            'agent_role': agent.role,
                            'agent_stance': agent.stance,
                            'argument': argument,
                            'target_agent': target_agent.name
                        })
                        
                        print(f"    论点: {argument[:100]}...")
            
            # 主持辩论并总结
            print("主持辩论并总结...")
            conclusion = await self.moderate_debate(question, debate_history)
            
            # 分析辩论过程
            print("分析辩论过程...")
            analysis = await self.analyze_debate(question, debate_history)
            
            return {
                'question': question,
                'conclusion': conclusion,
                'analysis': analysis,
                'debate_history': debate_history,
                'error': None
            }
            
        except Exception as e:
            return {
                'question': question,
                'conclusion': '',
                'analysis': '',
                'debate_history': debate_history,
                'error': str(e)
            }


def create_cod_workflow(debate_type: str = "chain") -> AsyncFlow:
    """
    创建辩论链工作流
    
    Args:
        debate_type: 辩论类型，"chain"或"graph"
        
    Returns:
        配置好的辩论链工作流
    """
    if debate_type == "chain":
        cod_node = ChainOfDebateNode()
    elif debate_type == "graph":
        cod_node = GraphOfDebateNode()
    else:
        raise ValueError(f"Unknown debate type: {debate_type}")
    
    # 创建工作流，以cod_node为起始节点
    workflow = AsyncFlow(cod_node)
    workflow.name = f"ChainOfDebateWorkflow_{debate_type}"
    
    return workflow


# 示例使用
async def demo_cod():
    """
    辩论链推理演示
    """
    # 创建辩论链工作流
    cod_chain_workflow = create_cod_workflow("chain")
    
    # 测试问题
    questions = [
        "人工智能是否会取代人类工作？",
        "远程工作是否比传统办公室工作更有效率？",
        "是否应该全面禁止一次性塑料制品？"
    ]
    
    print("=== 辩论链推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await cod_chain_workflow._run_async({'question': question})
        
        print(f"结论: {result['conclusion']}\n")
        
        # 打印分析
        print("分析:")
        print(f"{result['analysis']}\n")
        
        # 打印辩论历史
        print("辩论历史:")
        for entry in result['debate_history']:
            print(f"  轮次{entry['round']} - {entry['agent_name']} ({entry['agent_role']}): {entry['argument'][:100]}...")
        
        print("-" * 50 + "\n")
    
    # 创建辩论图工作流
    cod_graph_workflow = create_cod_workflow("graph")
    
    print("=== 辩论图推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await cod_graph_workflow._run_async({'question': question})
        
        print(f"结论: {result['conclusion']}\n")
        
        # 打印分析
        print("分析:")
        print(f"{result['analysis']}\n")
        
        # 打印辩论历史
        print("辩论历史:")
        for entry in result['debate_history']:
            target_text = f" (回应 {entry['target_agent']})" if entry.get('target_agent') else ""
            print(f"  轮次{entry['round']} - {entry['agent_name']} ({entry['agent_role']}){target_text}: {entry['argument'][:100]}...")
        
        print("-" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_cod())