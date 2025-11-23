"""
多智能体协作流程 - 实现多种多智能体协作模式
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Flow, AsyncFlow
from researcher_node import ResearcherNode, WebResearcherNode
from writer_node import WriterNode, ReviewerNode, FinalizerNode
from coordinator_node import CoordinatorNode, TaskAssignerNode, ResultIntegratorNode


class SequentialMultiAgentFlow(Flow):
    """
    顺序多智能体协作流程 - 智能体按顺序执行任务
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化节点
        self.researcher = ResearcherNode()
        self.writer = WriterNode()
        self.reviewer = ReviewerNode()
        self.finalizer = FinalizerNode()
        
        # 定义流程转换规则 - 顺序执行
        self.researcher.next(self.writer)
        self.writer.next(self.reviewer)
        self.reviewer.next(self.finalizer)
        
        # 设置起始节点
        self.start(self.researcher)
    
    def run(self, research_topic, target_audience="一般读者", content_type="博客文章", word_count="500"):
        """运行顺序多智能体协作流程"""
        # 初始化共享状态
        shared_state = {
            "research_topic": research_topic,
            "target_audience": target_audience,
            "content_type": content_type,
            "word_count": word_count,
            "research_completed": False,
            "writing_completed": False,
            "review_completed": False,
            "finalization_completed": False
        }
        
        # 执行流程
        super().run(shared_state)
        return shared_state.get("final_content", "未能生成最终内容")


class ParallelMultiAgentFlow(AsyncFlow):
    """
    并行多智能体协作流程 - 多个智能体同时执行任务
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化节点
        self.researcher = ResearcherNode()
        self.web_researcher = WebResearcherNode()
        self.integrator = ResultIntegratorNode()
        
        # 设置起始节点
        self.start(self.integrator)
    
    async def run(self, research_topic, target_audience="一般读者", content_type="博客文章"):
        """运行并行多智能体协作流程"""
        # 初始化共享状态
        shared_state = {
            "research_topic": research_topic,
            "target_audience": target_audience,
            "content_type": content_type,
            "research_completed": False,
            "web_research_completed": False,
            "integration_completed": False
        }
        
        # 并行执行研究任务
        import asyncio
        
        # 创建任务
        research_task = asyncio.create_task(self._run_node_async(self.researcher, shared_state))
        web_research_task = asyncio.create_task(self._run_node_async(self.web_researcher, shared_state))
        
        # 等待所有研究任务完成
        await asyncio.gather(research_task, web_research_task)
        
        # 执行整合任务
        await super().run_async(shared_state)
        return shared_state.get("integrated_result", "未能整合研究结果")
    
    async def _run_node_async(self, node, shared_state):
        """异步运行单个节点"""
        import asyncio
        
        # 节点的预处理
        prep_result = node.prep(shared_state)
        
        # 节点的执行
        if asyncio.iscoroutinefunction(node.exec):
            exec_result = await node.exec(prep_result)
        else:
            exec_result = node.exec(prep_result)
        
        # 节点的后处理
        node.post(shared_state, prep_result, exec_result)


class HierarchicalMultiAgentFlow(Flow):
    """
    层级多智能体协作流程 - 主智能体协调和管理多个子智能体
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化节点
        self.coordinator = CoordinatorNode()
        self.task_assigner = TaskAssignerNode()
        self.researcher = ResearcherNode()
        self.writer = WriterNode()
        self.reviewer = ReviewerNode()
        self.result_integrator = ResultIntegratorNode()
        
        # 定义流程转换规则 - 层级结构
        self.coordinator.next(self.task_assigner)
        self.task_assigner.next(self.researcher)  # 根据任务分配结果选择执行路径
        self.researcher.next(self.writer)
        self.writer.next(self.reviewer)
        self.reviewer.next(self.result_integrator)
        
        # 设置起始节点
        self.start(self.coordinator)
    
    def run(self, user_request):
        """运行层级多智能体协作流程"""
        # 初始化共享状态
        shared_state = {
            "user_request": user_request,
            "decomposition_completed": False,
            "assignment_completed": False,
            "research_completed": False,
            "writing_completed": False,
            "review_completed": False,
            "integration_completed": False
        }
        
        # 执行流程
        super().run(shared_state)
        return shared_state.get("integrated_result", "未能生成整合结果")


class CollaborativeDecisionFlow(Flow):
    """
    协作决策流程 - 多个智能体共同参与决策过程
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化节点
        self.researcher1 = ResearcherNode()  # 第一个研究智能体
        self.researcher2 = WebResearcherNode()  # 第二个研究智能体
        self.writer = WriterNode()
        self.reviewer1 = ReviewerNode()  # 第一个审阅智能体
        self.reviewer2 = ReviewerNode()  # 第二个审阅智能体
        self.finalizer = FinalizerNode()
        
        # 定义流程转换规则 - 协作决策
        self.researcher1.next(self.researcher2)
        self.researcher2.next(self.writer)
        self.writer.next(self.reviewer1)
        self.reviewer1.next(self.reviewer2)
        self.reviewer2.next(self.finalizer)
        
        # 设置起始节点
        self.start(self.researcher1)
    
    def run(self, research_topic, target_audience="专家读者", content_type="研究报告"):
        """运行协作决策流程"""
        # 初始化共享状态
        shared_state = {
            "research_topic": research_topic,
            "target_audience": target_audience,
            "content_type": content_type,
            "word_count": "1000",  # 研究报告通常较长
            "research_completed": False,
            "web_research_completed": False,
            "writing_completed": False,
            "review1_completed": False,
            "review2_completed": False,
            "finalization_completed": False
        }
        
        # 执行流程
        super().run(shared_state)
        return shared_state.get("final_content", "未能生成最终内容")