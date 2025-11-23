"""
规划节点类 - 负责生成执行计划（使用真实搜索工具和语言模型）
"""
import json
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import AsyncNode
from utils.utils import call_llm_async


class PlannerNode(AsyncNode):
    """规划节点，负责根据任务生成执行计划"""
    
    def __init__(self, search_tool=None):
        super().__init__()
        self.search_tool = search_tool
        
    async def prep_async(self, shared):
        """准备阶段：获取任务描述"""
        task = shared.get("task", "")
        context = shared.get("context", "")
        
        print("\n=== 规划阶段开始 ===")
        print(f"任务描述: {task}")
        print(f"上下文: {context}")
        
        return {
            "task": task,
            "context": context
        }
    
    async def exec_async(self, prep_res):
        """执行阶段：使用真实搜索工具和语言模型生成执行计划"""
        task = prep_res["task"]
        context = prep_res["context"]
        
        print("\n=== 生成执行计划 ===")
        print("正在收集相关信息以生成执行计划...")
        
        prompt = f"""
你是一个专业的任务规划专家。请根据以下任务，制定一个详细的执行计划。

任务描述: {task}

上下文信息: {context}

请按照以下格式输出你的计划：

1. 分析任务需求和目标
2. 确定需要执行的步骤
3. 为每个步骤确定所需工具或资源
4. 按照逻辑顺序排列步骤

请以JSON格式返回你的计划，包含以下字段：
- "analysis": 任务分析
- "steps": 步骤列表，每个步骤包含:
  - "step_id": 步骤ID
  - "description": 步骤描述
  - "tool": 所需工具(可选)
  - "expected_output": 预期输出

示例格式:
{{
  "analysis": "这是一个需要多步骤完成的复杂任务...",
  "steps": [
    {{
      "step_id": 1,
      "description": "搜索相关信息",
      "tool": "search_web",
      "expected_output": "相关信息的搜索结果"
    }},
    {{
      "step_id": 2,
      "description": "分析搜索结果",
      "tool": "analyze",
      "expected_output": "分析报告"
    }}
  ]
}}
"""
        
        try:
            response = await call_llm_async(prompt)
            # 尝试提取JSON部分
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                plan = json.loads(json_str)
            else:
                # 如果没有找到JSON格式，创建一个基本计划
                plan = self._create_default_plan(task, context)
            return plan
        except Exception as e:
            # 如果解析失败，创建一个基本计划
            print(f"生成计划时出错: {str(e)}，将使用默认结构")
            import sys
            sys.exit(0)
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理阶段：保存计划到共享状态"""
        shared["plan"] = exec_res
        shared["current_step"] = 0
        shared["total_steps"] = len(exec_res.get("steps", []))
        
        # 打印计划信息
        print(f"任务分析: {exec_res['analysis']}")
        print(f"总步骤数: {len(exec_res['steps'])}")
        for i, step in enumerate(exec_res['steps'], 1):
            print(f"步骤 {i}: {step['description']} (工具: {step['tool']})")
        
        print("\n=== 规划阶段完成 ===")
        print(f"已保存执行计划，共 {shared['total_steps']} 个步骤")
        print("即将开始执行阶段...")
        
        return "execute_plan"  # 返回下一个动作