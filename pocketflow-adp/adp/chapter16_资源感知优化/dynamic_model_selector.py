"""
模型选择器 - 基于成本和性能需求的动态模型选择

该模块实现了一个智能模型选择器，可以根据任务复杂度、成本约束和性能要求
动态选择最适合的模型，实现资源感知的优化。
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# 添加utils目录到路径
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils import call_llm
from pocketflow import Node, Flow, AsyncNode, AsyncFlow


class ModelTier(Enum):
    """模型层级枚举"""
    BASIC = "basic"        # 基础模型，成本最低
    STANDARD = "standard"  # 标准模型，成本中等
    PREMIUM = "premium"    # 高级模型，成本最高


class ModelConfig:
    """模型配置类"""
    
    def __init__(self, name: str, tier: ModelTier, cost_per_1k_tokens: float, 
                 avg_response_time: float, capabilities: List[str]):
        self.name = name
        self.tier = tier
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.avg_response_time = avg_response_time
        self.capabilities = capabilities
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "tier": self.tier.value,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "avg_response_time": self.avg_response_time,
            "capabilities": self.capabilities
        }


class ModelSelector:
    """模型选择器类"""
    
    def __init__(self):
        # 初始化模型配置
        self.models = {
            "gpt-4o-mini": ModelConfig(
                name="gpt-4o-mini",
                tier=ModelTier.BASIC,
                cost_per_1k_tokens=0.00015,
                avg_response_time=0.8,
                capabilities=["text_generation", "basic_reasoning"]
            ),
            "gpt-4o": ModelConfig(
                name="gpt-4o",
                tier=ModelTier.STANDARD,
                cost_per_1k_tokens=0.0025,
                avg_response_time=1.2,
                capabilities=["text_generation", "reasoning", "function_calling"]
            ),
            "gpt-4-turbo": ModelConfig(
                name="gpt-4-turbo",
                tier=ModelTier.PREMIUM,
                cost_per_1k_tokens=0.01,
                avg_response_time=1.5,
                capabilities=["text_generation", "advanced_reasoning", "function_calling", "code_generation"]
            ),
            "claude-3-haiku": ModelConfig(
                name="claude-3-haiku",
                tier=ModelTier.BASIC,
                cost_per_1k_tokens=0.00025,
                avg_response_time=0.7,
                capabilities=["text_generation", "basic_reasoning"]
            ),
            "claude-3-sonnet": ModelConfig(
                name="claude-3-sonnet",
                tier=ModelTier.STANDARD,
                cost_per_1k_tokens=0.003,
                avg_response_time=1.0,
                capabilities=["text_generation", "reasoning", "analysis"]
            ),
            "claude-3-opus": ModelConfig(
                name="claude-3-opus",
                tier=ModelTier.PREMIUM,
                cost_per_1k_tokens=0.015,
                avg_response_time=1.8,
                capabilities=["text_generation", "advanced_reasoning", "analysis", "code_generation"]
            )
        }
        
        # 任务复杂度与所需能力的映射
        self.task_complexity_requirements = {
            "simple": ["text_generation"],
            "reasoning": ["text_generation", "reasoning"],
            "complex_reasoning": ["text_generation", "advanced_reasoning"],
            "code": ["text_generation", "code_generation"],
            "analysis": ["text_generation", "analysis"],
            "function_calling": ["text_generation", "function_calling"]
        }
    
    def get_model_by_name(self, model_name: str) -> Optional[ModelConfig]:
        """根据名称获取模型配置"""
        return self.models.get(model_name)
    
    def get_models_by_tier(self, tier: ModelTier) -> List[ModelConfig]:
        """根据层级获取模型列表"""
        return [model for model in self.models.values() if model.tier == tier]
    
    def select_model_by_tier(self, tier: ModelTier) -> ModelConfig:
        """根据层级选择最佳模型"""
        models = self.get_models_by_tier(tier)
        if not models:
            # 如果指定层级没有模型，选择标准层级的模型
            models = self.get_models_by_tier(ModelTier.STANDARD)
        
        # 选择成本最低的模型
        return min(models, key=lambda m: m.cost_per_1k_tokens)
    
    def select_model_by_task(self, task_complexity: str, max_tier: ModelTier = ModelTier.PREMIUM) -> ModelConfig:
        """根据任务复杂度选择模型"""
        # 获取任务所需能力
        required_capabilities = self.task_complexity_requirements.get(task_complexity, ["text_generation"])
        
        # 筛选满足能力要求的模型
        suitable_models = []
        for model in self.models.values():
            # 检查模型层级是否在允许范围内
            if model.tier.value > max_tier.value:
                continue
                
            # 检查模型是否具备所需能力
            if all(cap in model.capabilities for cap in required_capabilities):
                suitable_models.append(model)
        
        if not suitable_models:
            # 如果没有合适的模型，选择标准层级的模型
            return self.select_model_by_tier(ModelTier.STANDARD)
        
        # 在合适的模型中选择成本最低的
        return min(suitable_models, key=lambda m: m.cost_per_1k_tokens)
    
    def select_model_by_cost_constraint(self, max_cost_per_1k: float, task_complexity: str = "simple") -> ModelConfig:
        """根据成本约束选择模型"""
        # 获取任务所需能力
        required_capabilities = self.task_complexity_requirements.get(task_complexity, ["text_generation"])
        
        # 筛选满足成本约束和能力要求的模型
        suitable_models = []
        for model in self.models.values():
            if model.cost_per_1k_tokens <= max_cost_per_1k and all(cap in model.capabilities for cap in required_capabilities):
                suitable_models.append(model)
        
        if not suitable_models:
            # 如果没有合适的模型，选择成本最低的模型
            return min(self.models.values(), key=lambda m: m.cost_per_1k_tokens)
        
        # 在合适的模型中选择性能最好的（响应时间最短）
        return min(suitable_models, key=lambda m: m.avg_response_time)
    
    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """估算模型调用成本"""
        model = self.get_model_by_name(model_name)
        if not model:
            return 0.0
        
        # 假设输入和输出的成本相同
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * model.cost_per_1k_tokens
    
    def get_all_models(self) -> List[ModelConfig]:
        """获取所有模型配置"""
        return list(self.models.values())


class TaskComplexityClassifier(AsyncNode):
    """任务复杂度分类节点"""
    
    def __init__(self, model_selector: ModelSelector):
        super().__init__()
        self.model_selector = model_selector
        self.system_prompt = """
        你是一个任务复杂度分类器，分析用户查询并返回以下复杂度级别之一：
        
        - simple: 简单事实性问题，不需要复杂推理
        - reasoning: 需要逻辑推理、数学计算或多步骤推理
        - complex_reasoning: 需要深度分析、多角度思考或复杂推理链
        - code: 编程相关任务，需要代码生成或解释
        - analysis: 需要分析、比较或评估的任务
        - function_calling: 需要调用工具或API的任务
        
        只返回JSON格式，例如: {"complexity": "simple"}
        """
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取用户查询"""
        return {"query": shared.get("query", "")}
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用LLM对任务复杂度进行分类"""
        query = prep_res["query"]
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            response = await call_llm_async(messages)
            result = json.loads(response)
            complexity = result.get("complexity", "simple")
            return {"complexity": complexity, "query": query}
        except Exception as e:
            # 如果分类失败，默认为simple
            return {"complexity": "simple", "query": query, "error": str(e)}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将分类结果添加到共享状态"""
        shared["complexity"] = exec_res.get("complexity", "simple")
        shared["query"] = exec_res.get("query", "")
        return exec_res.get("complexity", "simple")


class ModelSelectionNode(AsyncNode):
    """模型选择节点"""
    
    def __init__(self, model_selector: ModelSelector):
        super().__init__()
        self.model_selector = model_selector
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取任务复杂度和约束条件"""
        return {
            "complexity": shared.get("complexity", "simple"),
            "cost_constraint": shared.get("cost_constraint"),
            "tier_constraint": shared.get("tier_constraint")
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：根据约束条件选择模型"""
        complexity = prep_res["complexity"]
        cost_constraint = prep_res["cost_constraint"]
        tier_constraint = prep_res["tier_constraint"]
        
        selected_model = None
        
        if cost_constraint is not None:
            # 有成本约束，根据成本选择
            selected_model = self.model_selector.select_model_by_cost_constraint(
                cost_constraint, complexity
            )
        elif tier_constraint is not None:
            # 有层级约束，根据层级选择
            tier = ModelTier(tier_constraint)
            selected_model = self.model_selector.select_model_by_tier(tier)
        else:
            # 无特殊约束，根据任务复杂度选择
            selected_model = self.model_selector.select_model_by_task(complexity)
        
        return {
            "selected_model": selected_model.to_dict(),
            "complexity": complexity
        }
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将选择的模型添加到共享状态"""
        shared["selected_model"] = exec_res.get("selected_model", {})
        shared["complexity"] = exec_res.get("complexity", "simple")
        return "default"


class QueryProcessingNode(AsyncNode):
    """查询处理节点"""
    
    def __init__(self, model_selector: ModelSelector):
        super().__init__()
        self.model_selector = model_selector
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取查询和选择的模型"""
        return {
            "query": shared.get("query", ""),
            "selected_model": shared.get("selected_model", {})
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用选择的模型处理查询"""
        query = prep_res["query"]
        model_config = prep_res["selected_model"]
        model_name = model_config.get("name", "gpt-4o-mini")
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 调用LLM
            response = await call_llm_async(query)
            
            # 记录结束时间
            end_time = time.time()
            response_time = end_time - start_time
            
            # 估算成本
            estimated_tokens = len(query.split()) + len(response.split())
            estimated_cost = self.model_selector.estimate_cost(model_name, estimated_tokens, estimated_tokens)
            
            return {
                "response": response,
                "model_name": model_name,
                "response_time": response_time,
                "estimated_cost": estimated_cost,
                "model_config": model_config
            }
        except Exception as e:
            return {
                "response": f"处理查询时出错: {str(e)}",
                "model_name": model_name,
                "error": str(e),
                "model_config": model_config
            }
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将结果添加到共享状态"""
        shared["response"] = exec_res.get("response", "")
        shared["model_name"] = exec_res.get("model_name", "")
        shared["response_time"] = exec_res.get("response_time", 0)
        shared["estimated_cost"] = exec_res.get("estimated_cost", 0)
        shared["model_config"] = exec_res.get("model_config", {})
        return "default"


class DynamicModelSelectionFlow(AsyncFlow):
    """动态模型选择流程"""
    
    def __init__(self, model_selector: ModelSelector):
        super().__init__()
        self.model_selector = model_selector
        
        # 创建节点
        self.classifier = TaskComplexityClassifier(model_selector)
        self.model_selector_node = ModelSelectionNode(model_selector)
        self.query_processor = QueryProcessingNode(model_selector)
        
        # 设置流程
        self.start(self.classifier)
        self.classifier.next(self.model_selector_node)
        self.model_selector_node.next(self.query_processor)
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：初始化共享状态"""
        shared["start_time"] = time.time()
        return {}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """后处理阶段：计算总处理时间和资源使用情况"""
        end_time = time.time()
        total_time = end_time - shared.get("start_time", end_time)
        
        return {
            "query": shared.get("query", ""),
            "response": shared.get("response", ""),
            "complexity": shared.get("complexity", ""),
            "model_name": shared.get("model_name", ""),
            "model_config": shared.get("model_config", {}),
            "response_time": shared.get("response_time", 0),
            "estimated_cost": shared.get("estimated_cost", 0),
            "total_time": total_time
        }


# 异步版本的call_llm函数
async def call_llm_async(prompt):
    """异步版本的call_llm函数"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, call_llm, prompt)


# 工厂函数
def create_dynamic_model_selection_flow():
    """创建动态模型选择流程"""
    model_selector = ModelSelector()
    return DynamicModelSelectionFlow(model_selector)


# 示例使用
async def main():
    """主函数：演示动态模型选择流程"""
    # 创建流程
    flow = create_dynamic_model_selection_flow()
    
    # 测试查询
    test_queries = [
        "法国的首都是哪里？",  # simple
        "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？",  # reasoning
        "请分析一下人工智能在医疗领域的应用前景和挑战",  # analysis
        "请写一个Python函数，实现快速排序算法",  # code
    ]
    
    # 处理每个查询
    for query in test_queries:
        print(f"\n处理查询: {query}")
        print("-" * 50)
        
        # 运行流程
        shared_state = {"query": query}
        result = await flow.run_async(shared_state)
        
        # 显示结果
        print(f"复杂度: {result['complexity']}")
        print(f"选择模型: {result['model_name']}")
        print(f"模型层级: {result['model_config'].get('tier', '')}")
        print(f"响应时间: {result['response_time']:.2f}秒")
        print(f"估算成本: ${result['estimated_cost']:.6f}")
        print(f"总处理时间: {result['total_time']:.2f}秒")
        print(f"回答: {result['response']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())