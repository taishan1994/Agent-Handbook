"""
人机协同模式节点实现

本模块包含了人机协同模式所需的各种节点实现，包括：
- TaskProcessor: 处理初始任务
- HumanEscalation: 处理需要人工干预的情况
- HumanInput: 接收和处理人类输入
- ResponseGenerator: 生成最终响应
"""

import sys
import os
import time
import random
from typing import Dict, Any, Optional, List

# 添加utils路径
utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
if utils_path not in sys.path:
    sys.path.append(utils_path)

# 添加PocketFlow路径
pocketflow_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if pocketflow_path not in sys.path:
    sys.path.append(pocketflow_path)

try:
    from pocketflow import Node
except ImportError:
    print("警告: 无法导入PocketFlow，使用模拟Node类")
    class Node:
        def __init__(self, name: str = ""):
            self.name = name
            self.successors = {}
            self.params = {}
        
        def set_params(self, params):
            self.params = params
        
        def prep(self, shared):
            return None
        
        def exec(self, prep_res):
            return f"{self.name}_action"
        
        def post(self, shared, prep_res, exec_res):
            return exec_res
        
        def next(self, node, action="default"):
            self.successors[action] = node
            return node
        
        def __rshift__(self, other):
            return self.next(other)

try:
    from call_llm import call_llm
except ImportError:
    print("警告: 无法导入call_llm，使用模拟函数")
    def call_llm(prompt: str, model: str = "default") -> str:
        # 简单的模拟LLM响应，基于提示词生成更有意义的内容
        if "天气" in prompt:
            return "根据最新气象数据，明天北京天气晴朗，气温在15-25摄氏度之间，微风，适合外出活动。"
        elif "项目计划" in prompt and "多部门" in prompt:
            return "针对您的多部门协作项目计划，建议如下：1) 成立跨部门项目组，明确各部门职责；2) 制定详细时间表，设置关键里程碑；3) 建立定期沟通机制，确保信息同步；4) 预留应急预算，应对可能的风险。"
        elif "人类专家" in prompt:
            return "基于人类专家的建议，我已整合出以下方案：首先分析任务核心需求，然后制定详细计划，分步骤执行并设置检查点。对于涉及多部门协作的任务，建议成立专门项目组，确保各部门有效沟通和协作。"
        else:
            return "根据您的需求，我已经分析了相关信息并制定了相应的处理方案。如有任何疑问或需要进一步调整，请随时告知。"

try:
    from exa_search_main import search_web_exa
except ImportError:
    print("警告: 无法导入search_web_exa，使用模拟函数")
    def search_web_exa(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        return [
            {"title": f"模拟搜索结果 {i+1}", "url": f"https://example.com/{i+1}", "snippet": f"模拟搜索摘要 {i+1}"}
            for i in range(num_results)
        ]


class TaskProcessor(Node):
    """任务处理器节点，负责处理初始任务"""
    
    def __init__(self, complexity_threshold: float = 0.7):
        """
        初始化任务处理器
        
        Args:
            complexity_threshold: 复杂度阈值，超过此值需要人工干预
        """
        super().__init__()
        self.complexity_threshold = complexity_threshold
    
    def prep(self, shared):
        """准备阶段：获取任务信息"""
        task = shared.get("task", "")
        print(f"🔧 TaskProcessor: 开始处理任务")
        print(f"📝 任务内容: {task}")
        return {"task": task}
    
    def exec(self, prep_res):
        """执行阶段：评估复杂度并决定处理方式"""
        task = prep_res.get("task", "")
        
        # 模拟任务复杂度评估
        complexity = self._assess_complexity(task)
        print(f"📊 任务复杂度评估: {complexity:.2f} (阈值: {self.complexity_threshold})")
        
        # 决定处理方式
        if complexity < self.complexity_threshold:
            return {
                "action": "auto_processed",
                "complexity": complexity,
                "requires_human_intervention": False
            }
        else:
            return {
                "action": "escalate_to_human",
                "complexity": complexity,
                "requires_human_intervention": True,
                "escalation_reason": f"任务复杂度({complexity:.2f})超过阈值({self.complexity_threshold})"
            }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：更新共享状态并处理任务"""
        task = prep_res.get("task", "")
        action = exec_res.get("action")
        complexity = exec_res.get("complexity")
        
        # 更新共享数据
        shared["task_complexity"] = complexity
        shared["requires_human_intervention"] = exec_res.get("requires_human_intervention", False)
        
        if action == "auto_processed":
            print("✅ TaskProcessor: 任务复杂度较低，尝试自动处理")
            result = self._process_task(task, shared)
            shared["task_result"] = result
        else:
            print("⚠️ TaskProcessor: 任务复杂度过高，需要人工干预")
            shared["escalation_reason"] = exec_res.get("escalation_reason", "")
        
        return action
    
    def _assess_complexity(self, task: str) -> float:
        """
        评估任务复杂度
        
        Args:
            task: 任务描述
            
        Returns:
            float: 复杂度分数 (0-1)
        """
        # 简单的复杂度评估逻辑
        complexity_indicators = [
            "复杂", "困难", "挑战", "多步骤", "跨部门", "敏感", "高风险",
            "道德", "伦理", "法律", "安全", "隐私", "紧急", "危机"
        ]
        
        base_complexity = 0.3  # 基础复杂度
        
        # 根据关键词增加复杂度
        for indicator in complexity_indicators:
            if indicator in task:
                base_complexity += 0.1
        
        # 根据任务长度增加复杂度
        length_factor = min(len(task) / 200, 0.3)
        base_complexity += length_factor
        
        # 添加一些随机性
        random_factor = random.uniform(-0.05, 0.05)
        base_complexity += random_factor
        
        # 确保复杂度在0-1范围内
        return max(0.1, min(1.0, base_complexity))
    
    def _process_task(self, task: str, shared_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动处理任务
        
        Args:
            task: 任务描述
            shared_data: 共享数据字典
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        print("🔍 TaskProcessor: 搜索相关信息...")
        search_results = search_web_exa(task)
        
        print("🤖 TaskProcessor: 生成任务处理方案...")
        prompt = f"""
        任务: {task}
        
        参考信息:
        {search_results}
        
        请基于以上信息，为这个任务提供一个完整的处理方案。
        """
        
        response = call_llm(prompt)
        
        return {
            "status": "completed",
            "response": response,
            "search_results": search_results,
            "processing_time": time.time()
        }


class HumanEscalation(Node):
    """人工升级节点 - 处理需要人工干预的情况"""
    
    def __init__(self):
        super().__init__()
    
    def prep(self, shared):
        """准备阶段：获取升级信息"""
        task = shared.get("task", "")
        escalation_reason = shared.get("escalation_reason", "")
        task_complexity = shared.get("task_complexity", 0)
        
        print(f"🚨 HumanEscalation: 准备人工干预")
        print(f"📋 任务: {task}")
        print(f"📌 升级原因: {escalation_reason}")
        print(f"📊 复杂度: {task_complexity:.2f}")
        
        return {
            "task": task,
            "escalation_reason": escalation_reason,
            "task_complexity": task_complexity
        }
    
    def exec(self, prep_res):
        """执行阶段：处理升级逻辑"""
        task = prep_res.get("task", "")
        escalation_reason = prep_res.get("escalation_reason", "")
        task_complexity = prep_res.get("task_complexity", 0)
        
        # 准备人工干预所需的信息
        escalation_info = {
            "task": task,
            "complexity": task_complexity,
            "reason": escalation_reason,
            "timestamp": time.time(),
            "status": "pending_human_input"
        }
        
        # 生成人工干预请求
        print("📝 HumanEscalation: 生成人工干预请求...")
        escalation_request = self._generate_escalation_request(task, escalation_reason, task_complexity)
        
        print("🔄 HumanEscalation: 等待人工输入...")
        
        return {
            "action": "request_human_input",
            "escalation_info": escalation_info,
            "escalation_request": escalation_request
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：更新共享状态"""
        shared["escalation_info"] = exec_res.get("escalation_info", {})
        shared["human_input_required"] = True
        shared["escalation_request"] = exec_res.get("escalation_request", "")
        
        print("已触发人工干预流程")
        return exec_res.get("action", "request_human_input")
    
    def _generate_escalation_request(self, task: str, reason: str, complexity: float) -> str:
        """
        生成人工干预请求
        
        Args:
            task: 任务描述
            reason: 升级原因
            complexity: 复杂度分数
            
        Returns:
            str: 人工干预请求文本
        """
        prompt = f"""
        请为以下任务生成一个清晰的人工干预请求，包括：
        1. 任务描述
        2. 需要人工干预的原因
        3. 建议的人工处理方向
        4. 任何相关的背景信息
        
        任务: {task}
        干预原因: {reason}
        复杂度评分: {complexity:.2f}/1.0
        """
        
        return call_llm(prompt)


class HumanInput(Node):
    """人工输入节点 - 接收和分析人类输入"""
    
    def __init__(self):
        super().__init__()
    
    def prep(self, shared):
        # 准备阶段：获取人工输入所需的信息
        escalation_info = shared.get("escalation_info", {})
        escalation_request = shared.get("escalation_request", "")
        
        return {
            "escalation_info": escalation_info,
            "escalation_request": escalation_request,
            "task": shared.get("task", ""),
            "task_complexity": shared.get("task_complexity", 0)
        }
    
    def exec(self, prep_res):
        # 执行阶段：获取人工输入
        escalation_request = prep_res.get("escalation_request", "")
        
        print(f"👤 请提供人工输入")
        print(f"📋 请求详情: {escalation_request}")
        
        # 模拟人工输入（实际应用中可能是GUI、API等）
        human_input = self._simulate_human_input(prep_res)
        
        return {
            "action": "process_human_input",
            "human_input": human_input,
            "input_source": "simulated"
        }
    
    def post(self, shared, prep_res, exec_res):
        # 后处理阶段：更新共享状态
        human_input = exec_res.get("human_input", "")
        
        shared["human_input"] = human_input
        if "processing_history" not in shared:
            shared["processing_history"] = []
        shared["processing_history"].append({
            "node": "HumanInput",
            "result": "process_human_input",
            "timestamp": time.time(),
            "human_input": human_input
        })
        
        print(f"✅ 已接收人工输入: {human_input}")
        return exec_res.get("action", "process_human_input")
    
    def _simulate_human_input(self, shared_data: Dict[str, Any]) -> str:
        """
        模拟人类输入（用于测试）
        
        Args:
            shared_data: 共享数据字典
            
        Returns:
            str: 模拟的人类输入
        """
        task = shared_data.get("task", "")
        complexity = shared_data.get("task_complexity", 0)
        
        # 根据任务复杂度生成不同质量的模拟输入
        if complexity > 0.8:
            return f"对于任务'{task}'，我建议采用以下方法：1. 首先分析核心需求 2. 制定详细计划 3. 分步骤执行 4. 设置检查点。这个任务需要跨部门协作，建议成立专门项目组。"
        elif complexity > 0.5:
            return f"关于任务'{task}'，我认为需要更多背景信息。建议先进行需求调研，然后制定初步方案，最后提交审批。"
        else:
            return f"任务'{task}'可以直接按照标准流程处理，无需特殊干预。"
    
    def _analyze_human_input(self, human_input: str) -> Dict[str, Any]:
        """
        分析人类输入
        
        Args:
            human_input: 人类输入文本
            
        Returns:
            Dict[str, Any]: 输入分析结果
        """
        # 简单的输入分析
        analysis = {
            "length": len(human_input),
            "word_count": len(human_input.split()),
            "has_action_items": "建议" in human_input or "应该" in human_input or "需要" in human_input,
            "sentiment": "neutral"  # 在实际应用中，可以使用情感分析
        }
        
        # 根据关键词判断输入类型
        if "批准" in human_input or "同意" in human_input:
            analysis["input_type"] = "approval"
        elif "拒绝" in human_input or "不同意" in human_input:
            analysis["input_type"] = "rejection"
        elif "修改" in human_input or "调整" in human_input:
            analysis["input_type"] = "modification"
        else:
            analysis["input_type"] = "general_guidance"
        
        return analysis


class ResponseGenerator(Node):
    """响应生成节点 - 生成最终响应"""
    
    def __init__(self):
        super().__init__()
    
    def prep(self, shared):
        """准备阶段：获取响应生成所需的信息"""
        task = shared.get("task", "")
        task_result = shared.get("task_result", None)
        human_input = shared.get("human_input", None)
        requires_human_intervention = shared.get("requires_human_intervention", False)
        
        return {
            "task": task,
            "task_result": task_result,
            "human_input": human_input,
            "requires_human_intervention": requires_human_intervention
        }
    
    def exec(self, prep_res):
        """执行阶段：生成响应"""
        task = prep_res.get("task", "")
        task_result = prep_res.get("task_result", None)
        human_input = prep_res.get("human_input", None)
        requires_human_intervention = prep_res.get("requires_human_intervention", False)
        
        print(f"📝 ResponseGenerator: 生成最终响应")
        
        if requires_human_intervention:
            # 需要人工干预的情况
            human_input_analysis = prep_res.get("human_input_analysis", {})
            
            print("🤝 ResponseGenerator: 整合人工输入生成响应")
            response = self._generate_human_integrated_response(task, human_input, human_input_analysis)
            response_type = "human_integrated"
        else:
            # 自动处理的情况
            print("🤖 ResponseGenerator: 生成自动处理响应")
            response = self._generate_auto_response(task, task_result or {})
            response_type = "automated"
        
        return {
            "action": "response_generated",
            "response": response,
            "response_type": response_type
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：更新共享状态"""
        response = exec_res.get("response", "")
        response_type = exec_res.get("response_type", "automated")
        
        shared["final_response"] = response
        shared["response_type"] = response_type
        shared["response_timestamp"] = time.time()
        
        if "processing_history" not in shared:
            shared["processing_history"] = []
        shared["processing_history"].append({
            "node": "ResponseGenerator",
            "result": "response_generated",
            "timestamp": time.time(),
            "response_type": response_type
        })
        
        print("✅ ResponseGenerator: 最终响应已生成")
        return exec_res.get("action", "response_generated")
    
    def _generate_human_integrated_response(self, task: str, human_input: str, input_analysis: Dict[str, Any]) -> str:
        """
        生成整合人工输入的响应
        
        Args:
            task: 原始任务
            human_input: 人类输入
            input_analysis: 人类输入分析
            
        Returns:
            str: 整合响应
        """
        prompt = f"""
        原始任务: {task}
        
        人类专家输入: {human_input}
        
        输入分析: {input_analysis}
        
        请基于以上信息，生成一个完整的响应，包括：
        1. 对任务的理解
        2. 人类专家的关键建议
        3. 最终的处理方案
        4. 后续执行步骤
        """
        
        return call_llm(prompt)
    
    def _generate_auto_response(self, task: str, task_result: Dict[str, Any]) -> str:
        """
        生成自动处理的响应
        
        Args:
            task: 原始任务
            task_result: 自动处理结果
            
        Returns:
            str: 自动响应
        """
        prompt = f"""
        原始任务: {task}
        
        自动处理结果: {task_result.get('response', '')}
        
        请基于以上信息，生成一个完整的响应，说明任务已自动处理完成，并提供处理结果的摘要。
        """
        
        return call_llm(prompt)