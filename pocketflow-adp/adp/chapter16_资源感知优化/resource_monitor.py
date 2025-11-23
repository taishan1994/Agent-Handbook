"""
资源监控器 - 跟踪和优化资源使用情况

该模块实现了一个资源监控系统，能够跟踪LLM调用的成本、性能和资源使用情况，
并提供优化建议和策略。
"""

import json
import time
import os
import copy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

# 添加utils目录到路径
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils import call_llm
from pocketflow import Node, Flow, AsyncNode, AsyncFlow


@dataclass
class ResourceUsage:
    """资源使用记录"""
    timestamp: str
    model_name: str
    input_tokens: int
    output_tokens: int
    response_time: float
    cost: float
    query_type: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class ResourceMetrics:
    """资源指标"""
    total_cost: float
    total_tokens: int
    avg_response_time: float
    success_rate: float
    query_count: int
    model_usage: Dict[str, int]  # 模型使用次数
    query_type_distribution: Dict[str, int]  # 查询类型分布


class ResourceMonitor:
    """资源监控器类"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(os.path.dirname(__file__), "resource_usage.json")
        self.usage_history: List[ResourceUsage] = []
        self.model_costs = {
            "gpt-4o-mini": 0.00015,  # per 1k tokens
            "gpt-4o": 0.0025,
            "gpt-4-turbo": 0.01,
            "claude-3-haiku": 0.00025,
            "claude-3-sonnet": 0.003,
            "claude-3-opus": 0.015
        }
        self.load_usage_history()
    
    def load_usage_history(self):
        """加载使用历史"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.usage_history = [ResourceUsage(**item) for item in data]
        except Exception as e:
            print(f"加载使用历史失败: {e}")
            self.usage_history = []
    
    def save_usage_history(self):
        """保存使用历史"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump([asdict(usage) for usage in self.usage_history], f, indent=2)
        except Exception as e:
            print(f"保存使用历史失败: {e}")
    
    def record_usage(self, model_name: str, input_tokens: int, output_tokens: int, 
                    response_time: float, query_type: str, success: bool, 
                    error_message: Optional[str] = None):
        """记录资源使用情况"""
        cost = self.calculate_cost(model_name, input_tokens, output_tokens)
        timestamp = datetime.now().isoformat()
        
        usage = ResourceUsage(
            timestamp=timestamp,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time=response_time,
            cost=cost,
            query_type=query_type,
            success=success,
            error_message=error_message
        )
        
        self.usage_history.append(usage)
        self.save_usage_history()
        
        return usage
    
    def calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """计算调用成本"""
        cost_per_1k = self.model_costs.get(model_name, 0.0025)  # 默认使用gpt-4o的成本
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * cost_per_1k
    
    def calculate_metrics(self, days: int = 7) -> ResourceMetrics:
        """计算资源指标"""
        # 过滤指定天数内的记录
        cutoff_time = datetime.fromisoformat(datetime.now().isoformat()).timestamp() - (days * 24 * 3600)
        recent_usage = [
            usage for usage in self.usage_history 
            if datetime.fromisoformat(usage.timestamp).timestamp() > cutoff_time
        ]
        
        if not recent_usage:
            return ResourceMetrics(
                total_cost=0.0,
                total_tokens=0,
                avg_response_time=0.0,
                success_rate=0.0,
                query_count=0,
                model_usage={},
                query_type_distribution={}
            )
        
        # 计算指标
        total_cost = sum(usage.cost for usage in recent_usage)
        total_tokens = sum(usage.input_tokens + usage.output_tokens for usage in recent_usage)
        avg_response_time = sum(usage.response_time for usage in recent_usage) / len(recent_usage)
        success_count = sum(1 for usage in recent_usage if usage.success)
        success_rate = success_count / len(recent_usage)
        
        # 模型使用统计
        model_usage = defaultdict(int)
        for usage in recent_usage:
            model_usage[usage.model_name] += 1
        
        # 查询类型分布
        query_type_distribution = defaultdict(int)
        for usage in recent_usage:
            query_type_distribution[usage.query_type] += 1
        
        return ResourceMetrics(
            total_cost=total_cost,
            total_tokens=total_tokens,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            query_count=len(recent_usage),
            model_usage=dict(model_usage),
            query_type_distribution=dict(query_type_distribution)
        )
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        metrics = self.calculate_metrics()
        suggestions = []
        
        # 成本优化建议
        if metrics.total_cost > 10.0:  # 如果成本超过10美元
            suggestions.append("您的LLM使用成本较高，考虑使用更经济的模型（如gpt-4o-mini）处理简单任务")
        
        # 模型使用建议
        premium_models = ["gpt-4-turbo", "claude-3-opus"]
        premium_usage = sum(metrics.model_usage.get(model, 0) for model in premium_models)
        if premium_usage > metrics.query_count * 0.5:  # 如果超过50%使用高级模型
            suggestions.append("您频繁使用高级模型，考虑对任务进行分类，简单任务使用基础模型")
        
        # 性能优化建议
        if metrics.avg_response_time > 2.0:  # 如果平均响应时间超过2秒
            suggestions.append("平均响应时间较长，考虑优化查询或使用更快的模型")
        
        # 成功率建议
        if metrics.success_rate < 0.9:  # 如果成功率低于90%
            suggestions.append("查询成功率较低，检查查询格式或模型选择是否合适")
        
        # 查询类型优化建议
        simple_queries = metrics.query_type_distribution.get("simple", 0)
        if simple_queries > 0:
            simple_ratio = simple_queries / metrics.query_count
            if simple_ratio > 0.3 and metrics.model_usage.get("gpt-4o-mini", 0) < simple_queries:
                suggestions.append("您有许多简单查询，但未充分利用经济模型gpt-4o-mini")
        
        return suggestions
    
    def get_usage_report(self, days: int = 7) -> Dict[str, Any]:
        """获取使用报告"""
        metrics = self.calculate_metrics(days)
        suggestions = self.get_optimization_suggestions()
        
        return {
            "period_days": days,
            "metrics": asdict(metrics),
            "optimization_suggestions": suggestions
        }


class ResourceAwareQueryNode(Node):
    """资源感知查询节点"""
    
    def __init__(self, monitor: ResourceMonitor, model_name: str = "gpt-4o"):
        super().__init__()
        self.monitor = monitor
        self.model_name = model_name
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取查询内容"""
        return {
            "query": shared.get("query", ""),
            "query_type": shared.get("query_type", "unknown")
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：处理查询并记录资源使用"""
        query = prep_res["query"]
        query_type = prep_res["query_type"]
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 调用LLM
            response = call_llm(query)
            
            # 记录结束时间
            end_time = time.time()
            response_time = end_time - start_time
            
            # 估算token数量（简单估算：单词数）
            input_tokens = len(query.split())
            output_tokens = len(response.split())
            
            # 记录资源使用
            usage = self.monitor.record_usage(
                model_name=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time=response_time,
                query_type=query_type,
                success=True
            )
            
            print(f"资源使用已记录: 模型={self.model_name}, 输入Token={input_tokens}, 输出Token={output_tokens}, 响应时间={response_time:.2f}秒")
            
            return {
                "response": response,
                "model_name": self.model_name,
                "response_time": response_time,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "success": True
            }
        except Exception as e:
            # 记录结束时间
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录资源使用（失败情况）
            self.monitor.record_usage(
                model_name=self.model_name,
                input_tokens=len(query.split()),
                output_tokens=0,
                response_time=response_time,
                query_type=query_type,
                success=False,
                error_message=str(e)
            )
            
            return {
                "response": f"处理查询时出错: {str(e)}",
                "model_name": self.model_name,
                "response_time": response_time,
                "success": False,
                "error": str(e)
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将结果添加到共享状态"""
        shared["response"] = exec_res.get("response", "")
        shared["model_name"] = exec_res.get("model_name", "")
        shared["response_time"] = exec_res.get("response_time", 0)
        shared["input_tokens"] = exec_res.get("input_tokens", 0)
        shared["output_tokens"] = exec_res.get("output_tokens", 0)
        shared["success"] = exec_res.get("success", False)
        
        # 根据action决定下一步
        action = shared.get("action", "query")
        return action if action == "generate_report" else "default"


class ResourceReportNode(Node):
    """资源报告节点"""
    
    def __init__(self, monitor: ResourceMonitor):
        super().__init__()
        self.monitor = monitor
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取报告参数"""
        return {
            "days": shared.get("report_days", 7)
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：生成资源使用报告"""
        days = prep_res["days"]
        report = self.monitor.get_usage_report(days)
        # 获取指标字典
        metrics = report.get("metrics", {})
        # 重新组织报告结构，使其更易于访问
        organized_report = {
            "total_cost": metrics.get("total_cost", 0),
            "total_tokens": metrics.get("total_tokens", 0),
            "avg_response_time": metrics.get("avg_response_time", 0),
            "success_rate": metrics.get("success_rate", 0) * 100,  # 转换为百分比
            "query_count": metrics.get("query_count", 0),
            "model_stats": {},  # 将model_usage转换为model_stats
            "type_stats": {},  # 将query_type_distribution转换为type_stats
            "optimization_suggestions": report.get("optimization_suggestions", [])
        }
        
        # 转换model_usage为model_stats格式
        model_usage = metrics.get("model_usage", {})
        for model, count in model_usage.items():
            # 计算该模型的平均响应时间和成功率
            model_records = [
                usage for usage in self.monitor.usage_history 
                if usage.model_name == model and 
                datetime.fromisoformat(usage.timestamp).timestamp() > 
                (datetime.now().timestamp() - days * 24 * 3600)
            ]
            
            if model_records:
                avg_response_time = sum(r.response_time for r in model_records) / len(model_records)
                success_count = sum(1 for r in model_records if r.success)
                success_rate = (success_count / len(model_records)) * 100
            else:
                avg_response_time = 0
                success_rate = 0
            
            organized_report["model_stats"][model] = {
                "count": count,
                "avg_response_time": avg_response_time,
                "success_rate": success_rate
            }
        
        # 转换query_type_distribution为type_stats格式
        query_type_dist = metrics.get("query_type_distribution", {})
        for qtype, count in query_type_dist.items():
            # 计算该查询类型的平均响应时间和成功率
            type_records = [
                usage for usage in self.monitor.usage_history 
                if usage.query_type == qtype and 
                datetime.fromisoformat(usage.timestamp).timestamp() > 
                (datetime.now().timestamp() - days * 24 * 3600)
            ]
            
            if type_records:
                avg_response_time = sum(r.response_time for r in type_records) / len(type_records)
                success_count = sum(1 for r in type_records if r.success)
                success_rate = (success_count / len(type_records)) * 100
            else:
                avg_response_time = 0
                success_rate = 0
            
            organized_report["type_stats"][qtype] = {
                "count": count,
                "avg_response_time": avg_response_time,
                "success_rate": success_rate
            }
        
        return {"report": organized_report}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将报告添加到共享状态"""
        shared["resource_report"] = exec_res.get("report", {})
        return "default"


class ResourceMonitoringFlow(Flow):
    """资源监控流程"""
    
    def __init__(self, monitor: ResourceMonitor, model_name: str = "gpt-4o"):
        super().__init__()
        self.monitor = monitor
        
        # 创建节点
        self.query_node = ResourceAwareQueryNode(monitor, model_name)
        self.report_node = ResourceReportNode(monitor)
        
        # 设置流程
        self.start(self.query_node)
        self.query_node.next(self.report_node, "generate_report")
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：初始化共享状态"""
        shared["start_time"] = time.time()
        # 如果没有指定action，默认为查询
        if "action" not in shared:
            shared["action"] = "query"
        return {}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """后处理阶段：计算总处理时间"""
        end_time = time.time()
        total_time = end_time - shared.get("start_time", end_time)
        
        # 根据action决定下一步
        action = shared.get("action", "query")
        if action == "generate_report":
            # 如果是生成报告，需要确保report_node被执行
            return {
                "action": "generate_report",
                "query": shared.get("query", ""),
                "response": shared.get("response", ""),
                "model_name": shared.get("model_name", ""),
                "response_time": shared.get("response_time", 0),
                "input_tokens": shared.get("input_tokens", 0),
                "output_tokens": shared.get("output_tokens", 0),
                "success": shared.get("success", False),
                "resource_report": shared.get("resource_report", {}),
                "total_time": total_time
            }
        else:
            # 默认情况，返回查询结果
            return {
                "query": shared.get("query", ""),
                "response": shared.get("response", ""),
                "model_name": shared.get("model_name", ""),
                "response_time": shared.get("response_time", 0),
                "input_tokens": shared.get("input_tokens", 0),
                "output_tokens": shared.get("output_tokens", 0),
                "success": shared.get("success", False),
                "total_time": total_time
            }


# 异步版本的call_llm函数
async def call_llm_async(prompt):
    """异步版本的call_llm函数"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, call_llm, prompt)


# 工厂函数
def create_resource_monitoring_flow(model_name: str = "gpt-4o", storage_path: Optional[str] = None):
    """创建资源监控流程"""
    monitor = ResourceMonitor(storage_path)
    return ResourceMonitoringFlow(monitor, model_name), monitor


# 示例使用
async def main():
    """主函数：演示资源监控流程"""
    # 创建流程和监控器
    flow, monitor = create_resource_monitoring_flow()
    
    # 测试查询
    test_queries = [
        {"query": "法国的首都是哪里？", "query_type": "simple"},
        {"query": "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？", "query_type": "reasoning"},
        {"query": "请分析一下人工智能在医疗领域的应用前景和挑战", "query_type": "analysis"},
        {"query": "请写一个Python函数，实现快速排序算法", "query_type": "code"}
    ]
    
    # 处理每个查询
    for query_data in test_queries:
        print(f"\n处理查询: {query_data['query']}")
        print("-" * 50)
        
        # 运行流程
        shared_state = query_data
        result = await flow.run_async(shared_state)
        
        # 显示结果
        print(f"使用模型: {result['model_name']}")
        print(f"响应时间: {result['response_time']:.2f}秒")
        print(f"输入/输出Token: {result['input_tokens']}/{result['output_tokens']}")
        print(f"成功: {result['success']}")
        print(f"回答: {result['response'][:100]}...")
    
    # 生成资源使用报告
    print("\n" + "=" * 50)
    print("资源使用报告")
    print("=" * 50)
    
    shared_state = {"action": "generate_report", "report_days": 7}
    report_result = await flow.run_async(shared_state)
    
    report = report_result["resource_report"]
    metrics = report["metrics"]
    
    print(f"查询总数: {metrics['query_count']}")
    print(f"总成本: ${metrics['total_cost']:.4f}")
    print(f"总Token数: {metrics['total_tokens']}")
    print(f"平均响应时间: {metrics['avg_response_time']:.2f}秒")
    print(f"成功率: {metrics['success_rate']:.2%}")
    print(f"模型使用分布: {metrics['model_usage']}")
    print(f"查询类型分布: {metrics['query_type_distribution']}")
    
    print("\n优化建议:")
    for i, suggestion in enumerate(report["optimization_suggestions"], 1):
        print(f"{i}. {suggestion}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())