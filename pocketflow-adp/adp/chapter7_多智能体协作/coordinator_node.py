"""
协调者智能体节点 - 负责协调和管理多个子智能体的工作
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Node
from utils.utils import call_llm


class CoordinatorNode(Node):
    """
    协调者智能体节点，负责任务分解和智能体协调
    """
    
    def prep(self, shared):
        """准备协调任务"""
        # 从共享状态中获取用户请求
        user_request = shared.get("user_request", "")
        
        # 构建任务分解提示
        decomposition_prompt = f"""
        作为项目协调者，请将以下用户请求分解为可执行的子任务：
        
        用户请求：{user_request}
        
        请提供：
        1. 任务分解列表（每个任务应明确、可执行）
        2. 任务执行顺序（如果有依赖关系）
        3. 每个任务所需的智能体类型（研究、写作、审阅等）
        4. 每个任务的预期输出
        
        请以JSON格式返回分解结果。
        """
        
        return decomposition_prompt
    
    def exec(self, decomposition_prompt):
        """执行任务分解"""
        # 使用LLM进行任务分解
        task_decomposition = call_llm(decomposition_prompt)
        return task_decomposition
    
    def post(self, shared, prep_res, exec_res):
        """处理任务分解结果"""
        # 将任务分解结果存储到共享状态
        shared["task_decomposition"] = exec_res
        shared["decomposition_completed"] = True


class TaskAssignerNode(Node):
    """
    任务分配智能体节点，负责将任务分配给合适的智能体
    """
    
    def prep(self, shared):
        """准备任务分配"""
        # 从共享状态中获取任务分解结果
        task_decomposition = shared.get("task_decomposition", "")
        
        # 构建任务分配提示
        assignment_prompt = f"""
        基于以下任务分解结果，请为每个任务分配最合适的智能体：
        
        任务分解：
        {task_decomposition}
        
        可用智能体类型：
        1. ResearcherNode - 负责研究和信息收集
        2. WriterNode - 负责内容生成和写作
        3. ReviewerNode - 负责内容审阅和改进
        4. WebResearcherNode - 负责网络搜索和信息收集
        
        请为每个任务指定：
        1. 最合适的智能体类型
        2. 任务执行的具体参数
        3. 预期输出格式
        4. 与其他任务的依赖关系
        
        请以JSON格式返回分配结果。
        """
        
        return assignment_prompt
    
    def exec(self, assignment_prompt):
        """执行任务分配"""
        # 使用LLM进行任务分配
        task_assignment = call_llm(assignment_prompt)
        return task_assignment
    
    def post(self, shared, prep_res, exec_res):
        """处理任务分配结果"""
        # 将任务分配结果存储到共享状态
        shared["task_assignment"] = exec_res
        shared["assignment_completed"] = True


class ResultIntegratorNode(Node):
    """
    结果整合智能体节点，负责整合多个智能体的输出结果
    """
    
    def prep(self, shared):
        """准备结果整合"""
        # 从共享状态中获取所有智能体的输出结果
        research_results = shared.get("research_results", "")
        web_research_results = shared.get("web_research_results", {})
        generated_content = shared.get("generated_content", "")
        review_result = shared.get("review_result", "")
        final_content = shared.get("final_content", "")
        
        # 构建结果整合提示
        integration_prompt = f"""
        作为项目协调者，请整合以下所有智能体的输出结果，生成一个完整的项目报告：
        
        研究结果：
        {research_results}
        
        网络搜索结果：
        {web_research_results.get('search_summary', '') if web_research_results else ''}
        
        生成内容：
        {generated_content}
        
        审阅结果：
        {review_result}
        
        最终内容：
        {final_content}
        
        请生成一个完整的项目报告，包括：
        1. 项目概述和目标
        2. 研究方法和过程
        3. 主要发现和结果
        4. 结论和建议
        5. 附录（如有必要）
        """
        
        return integration_prompt
    
    def exec(self, integration_prompt):
        """执行结果整合"""
        # 使用LLM进行结果整合
        integrated_result = call_llm(integration_prompt)
        return integrated_result
    
    def post(self, shared, prep_res, exec_res):
        """处理结果整合"""
        # 将整合结果存储到共享状态
        shared["integrated_result"] = exec_res
        shared["integration_completed"] = True