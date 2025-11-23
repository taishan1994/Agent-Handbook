"""
响应生成节点类 - 负责生成最终结果（使用真实语言模型）
"""
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import AsyncNode
from utils.utils import call_llm_async


class ResponseGeneratorNode(AsyncNode):
    """响应生成节点，负责根据所有步骤的结果生成最终响应"""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared):
        """准备阶段：收集所有信息用于生成最终响应"""
        task = shared.get("task", "")
        context = shared.get("context", "")
        plan = shared.get("plan", {})
        step_results = shared.get("step_results", [])
        
        print("\n=== 响应生成阶段开始 ===")
        print(f"任务: {task}")
        print(f"上下文: {context}")
        print(f"计划步骤数: {len(plan.get('steps', []))}")
        print(f"已执行步骤数: {len(step_results)}")
        
        return {
            "task": task,
            "context": context,
            "plan": plan,
            "step_results": step_results
        }
    
    async def exec_async(self, prep_res):
        """执行阶段：生成最终响应"""
        task = prep_res["task"]
        context = prep_res["context"]
        plan = prep_res["plan"]
        step_results = prep_res["step_results"]
        
        print("\n=== 生成最终响应 ===")
        print("正在整合所有步骤的结果...")
        
        # 构建提示，包含所有相关信息
        prompt = f"""
请根据以下信息，为任务生成一个全面、结构化的最终响应:

原始任务: {task}

上下文: {context}

执行计划:
{json.dumps(plan, ensure_ascii=False, indent=2)}

执行步骤结果:
{json.dumps(step_results, ensure_ascii=False, indent=2)}

请生成一个高质量的最终响应，包括:
1. 任务执行总结
2. 关键发现和见解
3. 详细的结果分析
4. 结论和建议

响应应该:
- 直接回答原始任务
- 结构清晰，易于理解
- 包含所有相关的重要信息
- 语言专业、准确
- 基于实际搜索和分析结果，避免编造信息
"""
        
        try:
            print("正在调用语言模型生成响应...")
            final_response = await call_llm_async(prompt)
            print("最终响应已生成")
            return final_response
        except Exception as e:
            # 如果生成响应失败，返回一个基本响应
            print(f"生成响应时出错: {str(e)}")
            return f"生成最终响应时出错: {str(e)}\n\n基本结果:\n{json.dumps(step_results, ensure_ascii=False, indent=2)}"
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理阶段：保存最终响应"""
        shared["final_response"] = exec_res
        
        print("\n=== 响应生成阶段完成 ===")
        print("最终响应已保存到共享状态")
        print("\n=== 任务执行完成 ===")
        
        # 打印响应摘要
        response_length = len(exec_res)
        print(f"最终响应长度: {response_length} 字符")
        print("\n最终响应内容:")
        print(exec_res)
        
        return "end"  # 流程结束