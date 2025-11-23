import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# 添加PocketFlow目录到Python路径，确保使用项目中的版本
pocketflow_path = os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow')
if pocketflow_path not in sys.path:
    sys.path.insert(0, pocketflow_path)

from pocketflow import AsyncNode, AsyncParallelBatchNode, AsyncFlow
from utils.utils import call_llm_async
import asyncio

class SynthesisNode(AsyncNode):
    """
    综合节点：合并并行任务的结果
    """
    async def prep_async(self, shared):
        """准备综合处理的提示"""
        summary = shared.get("summary", "无总结")
        questions = shared.get("questions", "无问题")
        terms = shared.get("key_terms", "无术语")
        
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
        
        return prompt
    
    async def exec_async(self, prompt):
        """执行综合分析"""
        # 使用异步版本的call_llm_async
        return await call_llm_async(prompt)
    
    async def post_async(self, shared, prep_res, exec_res):
        """保存综合分析结果"""
        shared["final_result"] = exec_res
        return exec_res

class ParallelProcessingNode(AsyncParallelBatchNode):
    """并行处理节点，同时执行总结、问题生成和术语提取"""
    
    def __init__(self):
        super().__init__()
        self.max_retries = 3
    
    async def prep_async(self, shared):
        """准备并行处理的任务列表"""
        topic = shared.get("topic", "")
        
        # 创建任务列表（每个任务是一个元组，包含提示词和键）
        tasks = [
            (f"请总结关于'{topic}'的核心内容，控制在200字以内。", "summary"),
            (f"基于'{topic}'这个主题，生成5个有深度的问题。", "questions"),
            (f"从'{topic}'中提取并解释10个关键术语。", "terms")
        ]
        
        return tasks  # 返回任务列表
    
    async def exec_async(self, task):
        """执行单个任务"""
        prompt, key = task  # 解包任务元组
        
        try:
            # 使用异步版本的call_llm_async
            result = await call_llm_async(prompt)
            return {key: result}
        except Exception as e:
            print(f"执行任务 {key} 时出错: {e}")
            return {key: f"处理失败: {str(e)}"}
    
    async def post_async(self, shared, prep_res, exec_res):
        """合并并行处理的结果"""
        # 将结果合并到共享状态
        for result in exec_res:
            if result:  # 确保result不为None
                if "summary" in result:
                    shared["summary"] = result["summary"]
                if "questions" in result:
                    shared["questions"] = result["questions"]
                if "terms" in result:
                    shared["key_terms"] = result["terms"]
        
        print("并行处理完成!")
        # 返回None以确保继续执行下一个节点
        return None

# 创建节点实例
parallel_node = ParallelProcessingNode()
synthesis_node = SynthesisNode()

# 构建流程链：并行处理 → 综合
parallel_node.next(synthesis_node)

# 创建异步流程，以parallel_node为起点
parallel_flow = AsyncFlow(start=parallel_node)