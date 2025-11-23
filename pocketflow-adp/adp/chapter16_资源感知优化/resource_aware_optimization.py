"""
资源感知优化 - 基于PocketFlow的实现

该模块实现了一个资源感知优化系统，能够根据任务复杂性和资源约束
动态选择合适的模型和策略，以在成本、性能和质量之间取得平衡。
"""

import sys
import os
import json
import time
from typing import Dict, List, Any, Optional, Union

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils import call_llm
from pocketflow import Node, Flow, AsyncNode, AsyncFlow


class TaskClassifierNode(AsyncNode):
    """
    任务分类节点：根据查询内容将任务分类为simple、reasoning或internet_search
    """
    
    def __init__(self):
        super().__init__()
        self.system_prompt = """
        你是一个任务分类器，分析用户查询并返回以下三个类别之一：
        
        - simple: 直接事实性问题，不需要复杂推理或当前事件信息
        - reasoning: 需要逻辑推理、数学计算或多步骤推理的问题
        - internet_search: 涉及当前事件、最新数据或超出训练数据范围的问题
        
        规则:
        - 对于可以直接回答的事实性问题使用'simple'
        - 对于逻辑、数学或多步骤推理问题使用'reasoning'
        - 对于涉及当前事件或最新数据的问题使用'internet_search'
        
        只返回JSON格式，例如: {"classification": "simple"}
        """
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取用户查询"""
        return {"query": shared.get("query", "")}
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用LLM对任务进行分类"""
        query = prep_res["query"]
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            response = await call_llm_async(messages)
            result = json.loads(response)
            classification = result.get("classification", "simple")
            return {"classification": classification, "query": query}
        except Exception as e:
            # 如果分类失败，默认为simple
            return {"classification": "simple", "query": query, "error": str(e)}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将分类结果添加到共享状态"""
        shared["classification"] = exec_res.get("classification", "simple")
        shared["query"] = exec_res.get("query", "")
        return exec_res.get("classification", "simple")


class SimpleQueryNode(AsyncNode):
    """
    简单查询节点：使用轻量级模型处理简单查询
    """
    
    def __init__(self, model_name="gpt-4o-mini"):
        super().__init__()
        self.model_name = model_name
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取查询内容"""
        return {"query": shared.get("query", "")}
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用轻量级模型处理查询"""
        query = prep_res["query"]
        
        try:
            response = await call_llm_async(query)
            return {
                "response": response,
                "model": self.model_name,
                "classification": "simple"
            }
        except Exception as e:
            return {
                "response": f"处理简单查询时出错: {str(e)}",
                "model": self.model_name,
                "classification": "simple",
                "error": str(e)
            }
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将结果添加到共享状态"""
        shared["response"] = exec_res.get("response", "")
        shared["model_used"] = exec_res.get("model", self.model_name)
        shared["classification"] = exec_res.get("classification", "simple")
        return "default"


class ReasoningQueryNode(AsyncNode):
    """
    推理查询节点：使用更强大的模型处理复杂推理任务
    """
    
    def __init__(self, model_name="gpt-4o"):
        super().__init__()
        self.model_name = model_name
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取查询内容"""
        return {"query": shared.get("query", "")}
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用强大模型处理推理任务"""
        query = prep_res["query"]
        
        # 添加推理提示
        reasoning_prompt = f"""
        请仔细分析以下问题，并进行逐步推理：
        
        {query}
        
        请提供详细的推理过程和最终答案。
        """
        
        try:
            response = await call_llm_async(reasoning_prompt)
            return {
                "response": response,
                "model": self.model_name,
                "classification": "reasoning"
            }
        except Exception as e:
            return {
                "response": f"处理推理查询时出错: {str(e)}",
                "model": self.model_name,
                "classification": "reasoning",
                "error": str(e)
            }
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将结果添加到共享状态"""
        shared["response"] = exec_res.get("response", "")
        shared["model_used"] = exec_res.get("model", self.model_name)
        shared["classification"] = exec_res.get("classification", "reasoning")
        return "default"


class InternetSearchNode(AsyncNode):
    """
    网络搜索节点：模拟搜索相关信息，然后使用模型生成回答
    """
    
    def __init__(self, model_name="gpt-4o"):
        super().__init__()
        self.model_name = model_name
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取查询内容"""
        return {"query": shared.get("query", "")}
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：模拟搜索，然后生成回答"""
        query = prep_res["query"]
        
        try:
            # 模拟网络搜索结果
            search_results = f"模拟搜索结果：关于'{query}'的相关信息..."
            
            # 构建包含搜索结果的提示
            search_prompt = f"""
            基于以下网络搜索结果，回答用户问题：
            
            搜索结果：
            {search_results}
            
            用户问题：
            {query}
            
            请提供准确、全面的回答，并在适当的地方引用搜索结果。
            """
            
            # 使用模型生成回答
            response = await call_llm_async(search_prompt)
            
            return {
                "response": response,
                "model": self.model_name,
                "classification": "internet_search",
                "search_results": search_results
            }
        except Exception as e:
            return {
                "response": f"处理网络搜索查询时出错: {str(e)}",
                "model": self.model_name,
                "classification": "internet_search",
                "error": str(e)
            }
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将结果添加到共享状态"""
        shared["response"] = exec_res.get("response", "")
        shared["model_used"] = exec_res.get("model", self.model_name)
        shared["classification"] = exec_res.get("classification", "internet_search")
        shared["search_results"] = exec_res.get("search_results", "")
        return "default"


class ResourceAwareOptimizationFlow(AsyncFlow):
    """
    资源感知优化流程：根据任务分类动态选择处理策略
    """
    
    def __init__(self):
        super().__init__()
        
        # 创建节点
        self.classifier = TaskClassifierNode()
        self.simple_handler = SimpleQueryNode()
        self.reasoning_handler = ReasoningQueryNode()
        self.search_handler = InternetSearchNode()
        
        # 设置流程
        self.start(self.classifier)
        self.classifier.next(self.simple_handler, "simple")
        self.classifier.next(self.reasoning_handler, "reasoning")
        self.classifier.next(self.search_handler, "internet_search")
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：初始化共享状态"""
        shared["start_time"] = time.time()
        return {}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """后处理阶段：计算处理时间和资源使用情况"""
        end_time = time.time()
        processing_time = end_time - shared.get("start_time", end_time)
        
        return {
            "query": shared.get("query", ""),
            "response": shared.get("response", ""),
            "classification": shared.get("classification", ""),
            "model_used": shared.get("model_used", ""),
            "processing_time": processing_time,
            "search_results": shared.get("search_results", "")
        }


# 异步版本的call_llm函数
async def call_llm_async(prompt):
    """异步版本的call_llm函数"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, call_llm, prompt)


# 工厂函数
def create_resource_aware_flow():
    """创建资源感知优化流程"""
    return ResourceAwareOptimizationFlow()


# 示例使用
async def main():
    """主函数：演示资源感知优化流程"""
    # 创建流程
    flow = create_resource_aware_flow()
    
    # 测试查询
    test_queries = [
        "法国的首都是哪里？",  # simple
        "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？",  # reasoning
        "2024年诺贝尔物理学奖获得者是谁？"  # internet_search
    ]
    
    # 处理每个查询
    for query in test_queries:
        print(f"\n处理查询: {query}")
        print("-" * 50)
        
        # 运行流程
        shared_state = {"query": query}
        result = await flow.run_async(shared_state)
        
        # 显示结果
        print(f"分类: {result['classification']}")
        print(f"使用模型: {result['model_used']}")
        print(f"处理时间: {result['processing_time']:.2f}秒")
        print(f"回答: {result['response']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())