#!/usr/bin/env python3
"""
资源感知优化与监控演示 - 美化版

该演示展示了如何结合资源感知优化系统和资源监控器，
实现智能的资源管理和优化，并提供美观的资源使用报告。
"""

import sys
import os
import time
from typing import Dict, Any

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils import call_llm
from pocketflow import Node, Flow

# 导入资源监控器
from resource_monitor import ResourceMonitor, create_resource_monitoring_flow

# 导入资源感知优化系统
from resource_aware_optimization import (
    TaskClassifierNode, 
    SimpleQueryNode, 
    ReasoningQueryNode,
    ResourceAwareOptimizationFlow,
    call_llm_async
)


class MonitoredTaskClassifierNode(Node):
    """
    带监控的任务分类节点
    """
    
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        self.system_prompt = """
        你是一个任务分类器，分析用户查询并返回以下两个类别之一：
        
        - simple: 直接事实性问题，不需要复杂推理或当前事件信息
        - reasoning: 需要逻辑推理、数学计算或多步骤推理的问题
        
        规则:
        - 对于可以直接回答的事实性问题使用'simple'
        - 对于逻辑、数学或多步骤推理问题使用'reasoning'
        
        只返回JSON格式，例如: {"classification": "simple"}
        """
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取用户查询"""
        return {"query": shared.get("query", "")}
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用LLM对任务进行分类"""
        query = prep_res["query"]
        start_time = time.time()
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            response = call_llm(messages)
            end_time = time.time()
            response_time = end_time - start_time
            
            # 解析响应
            try:
                import json
                result = json.loads(response)
                classification = result.get("classification", "simple")
            except:
                classification = "simple"
            
            # 记录资源使用
            usage = self.monitor.record_usage(
                model_name="gpt-4o-mini",
                input_tokens=len(query.split()),
                output_tokens=len(response.split()),
                response_time=response_time,
                success=True,
                query_type="classification"
            )
            
            return {"classification": classification, "query": query}
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录失败
            self.monitor.record_usage(
                model_name="gpt-4o-mini",
                input_tokens=len(query.split()),
                output_tokens=0,
                response_time=response_time,
                success=False,
                query_type="classification"
            )
            
            # 如果分类失败，默认为simple
            return {"classification": "simple", "query": query, "error": str(e)}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将分类结果添加到共享状态"""
        shared["classification"] = exec_res.get("classification", "simple")
        shared["query"] = exec_res.get("query", "")
        return exec_res.get("classification", "simple")


class MonitoredSimpleQueryNode(Node):
    """
    带监控的简单查询节点
    """
    
    def __init__(self, monitor, model_name="gpt-4o-mini"):
        super().__init__()
        self.monitor = monitor
        self.model_name = model_name
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取查询内容"""
        return {"query": shared.get("query", "")}
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用轻量级模型处理查询"""
        query = prep_res["query"]
        start_time = time.time()
        
        try:
            response = call_llm(query)
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录资源使用
            usage = self.monitor.record_usage(
                model_name=self.model_name,
                input_tokens=len(query.split()),
                output_tokens=len(response.split()),
                response_time=response_time,
                success=True,
                query_type="simple"
            )
            
            return {
                "response": response,
                "model": self.model_name,
                "classification": "simple"
            }
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录失败
            self.monitor.record_usage(
                model_name=self.model_name,
                input_tokens=len(query.split()),
                output_tokens=0,
                response_time=response_time,
                success=False,
                query_type="simple"
            )
            
            return {
                "response": f"处理简单查询时出错: {str(e)}",
                "model": self.model_name,
                "classification": "simple",
                "error": str(e)
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将结果添加到共享状态"""
        shared["response"] = exec_res.get("response", "")
        shared["model_used"] = exec_res.get("model", self.model_name)
        shared["classification"] = exec_res.get("classification", "simple")
        return "default"


class MonitoredReasoningQueryNode(Node):
    """
    带监控的推理查询节点
    """
    
    def __init__(self, monitor, model_name="gpt-4o"):
        super().__init__()
        self.monitor = monitor
        self.model_name = model_name
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取查询内容"""
        return {"query": shared.get("query", "")}
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：使用强大模型处理推理任务"""
        query = prep_res["query"]
        start_time = time.time()
        
        # 添加推理提示
        reasoning_prompt = f"""
        请仔细分析以下问题，并进行逐步推理：
        
        {query}
        
        请提供详细的推理过程和最终答案。
        """
        
        try:
            response = call_llm(reasoning_prompt)
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录资源使用
            usage = self.monitor.record_usage(
                model_name=self.model_name,
                input_tokens=len(reasoning_prompt.split()),
                output_tokens=len(response.split()),
                response_time=response_time,
                success=True,
                query_type="reasoning"
            )
            
            return {
                "response": response,
                "model": self.model_name,
                "classification": "reasoning"
            }
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录失败
            self.monitor.record_usage(
                model_name=self.model_name,
                input_tokens=len(reasoning_prompt.split()),
                output_tokens=0,
                response_time=response_time,
                success=False,
                query_type="reasoning"
            )
            
            return {
                "response": f"处理推理查询时出错: {str(e)}",
                "model": self.model_name,
                "classification": "reasoning",
                "error": str(e)
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将结果添加到共享状态"""
        shared["response"] = exec_res.get("response", "")
        shared["model_used"] = exec_res.get("model", self.model_name)
        shared["classification"] = exec_res.get("classification", "reasoning")
        return "default"


class IntegratedResourceAwareFlow(Flow):
    """
    集成的资源感知优化流程
    结合了资源感知优化和资源监控功能
    """
    
    def __init__(self):
        super().__init__()
        
        # 创建资源监控器
        self.monitor = ResourceMonitor()
        
        # 创建带监控的节点
        self.classifier = MonitoredTaskClassifierNode(self.monitor)
        self.simple_handler = MonitoredSimpleQueryNode(self.monitor)
        self.reasoning_handler = MonitoredReasoningQueryNode(self.monitor)
        
        # 设置流程
        self.start(self.classifier)
        self.classifier.next(self.simple_handler, "simple")
        self.classifier.next(self.reasoning_handler, "reasoning")
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：初始化共享状态"""
        shared["start_time"] = time.time()
        return {}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """后处理阶段：计算处理时间和资源使用情况"""
        end_time = time.time()
        processing_time = end_time - shared.get("start_time", end_time)
        
        return {
            "query": shared.get("query", ""),
            "response": shared.get("response", ""),
            "classification": shared.get("classification", ""),
            "model_used": shared.get("model_used", ""),
            "processing_time": processing_time
        }
    
    def get_monitor(self):
        """获取资源监控器"""
        return self.monitor


def format_report(report_data):
    """格式化资源使用报告"""
    metrics = report_data['metrics']
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    资源使用报告                              ║
╚══════════════════════════════════════════════════════════════╝

📊 总体统计:
  • 总成本: ${metrics['total_cost']:.6f}
  • 总Token数: {metrics['total_tokens']}
  • 平均响应时间: {metrics['avg_response_time']:.2f}秒
  • 成功率: {metrics['success_rate']*100:.2f}%
  • 查询次数: {metrics['query_count']}

🤖 按模型统计:
"""
    
    for model, count in metrics['model_usage'].items():
        report += f"  • {model}: {count}次查询\n"
    
    report += "\n📋 按查询类型统计:\n"
    for query_type, count in metrics['query_type_distribution'].items():
        report += f"  • {query_type}: {count}次查询\n"
    
    if 'optimization_suggestions' in metrics and metrics['optimization_suggestions']:
        report += "\n💡 优化建议:\n"
        for suggestion in metrics['optimization_suggestions']:
            report += f"  • {suggestion}\n"
    
    return report


def demo_integrated_resource_aware():
    """演示集成的资源感知优化系统"""
    print("=== 集成资源感知优化系统演示 ===\n")
    
    # 创建流程
    flow = IntegratedResourceAwareFlow()
    monitor = flow.get_monitor()
    
    # 测试查询
    test_queries = [
        "法国的首都是哪里？",  # simple
        "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？",  # reasoning
        "解释量子纠缠的原理及其在量子计算中的应用",  # reasoning
        "分析人工智能在医疗领域的应用前景，包括技术挑战和伦理考虑",  # reasoning
        "编写一个Python函数实现快速排序算法"  # simple
    ]
    
    # 处理每个查询
    for i, query in enumerate(test_queries, 1):
        print(f"--- 测试查询 {i}: {query} ---")
        
        # 运行流程
        shared_state = {"query": query}
        result = flow.run(shared_state)
        
        # 显示结果
        print(f"分类: {result['classification']}")
        print(f"使用模型: {result['model_used']}")
        print(f"处理时间: {result['processing_time']:.2f}秒")
        print(f"回答: {result['response'][:200]}...")
        print()
    
    # 生成资源使用报告
    print("--- 资源使用报告 ---")
    report_data = monitor.get_usage_report()
    formatted_report = format_report(report_data)
    print(formatted_report)


if __name__ == "__main__":
    demo_integrated_resource_aware()