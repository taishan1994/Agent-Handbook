"""执行节点类 - 负责执行计划中的步骤（使用真实工具）"""
import asyncio
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import AsyncNode
from utils.utils import call_llm_async


class ExecutorNode(AsyncNode):
    """执行节点，负责执行计划中的步骤"""
    
    def __init__(self):
        super().__init__()
        
    async def prep_async(self, shared):
        """准备阶段：获取当前步骤和计划"""
        current_step = shared.get("current_step", 0)
        plan = shared.get("plan", {})
        steps = plan.get("steps", [])
        
        if current_step >= len(steps):
            return None  # 所有步骤已完成
            
        current_step_info = steps[current_step]
        
        print(f"\n=== 执行步骤 {current_step + 1}/{len(steps)} ===")
        print(f"步骤描述: {current_step_info.get('description', '')}")
        print(f"使用工具: {current_step_info.get('tool', 'general')}")
        
        return {
            "step_info": current_step_info,
            "task": shared.get("task", ""),
            "context": shared.get("context", ""),
            "step_results": shared.get("step_results", []),
            "current_step": current_step,
            "total_steps": len(steps)
        }
    
    async def exec_async(self, prep_res):
        """执行阶段：执行当前步骤"""
        if prep_res is None:
            return {"status": "completed", "result": "所有步骤已完成"}
            
        step_info = prep_res["step_info"]
        task = prep_res["task"]
        context = prep_res["context"]
        step_results = prep_res["step_results"]
        current_step = prep_res["current_step"]
        total_steps = prep_res["total_steps"]
        
        tool = step_info.get("tool", "general")
        description = step_info.get("description", "")
        
        print(f"正在执行: {description}")
        
        # 根据工具类型执行不同的操作
        if tool == "search_web":
            # 执行网络搜索
            search_query = f"{task} {description}"
            print(f"搜索查询: {search_query}")
            search_result = await self._search_web_async(search_query)
            print(f"搜索完成，找到 {len(search_result)} 条结果")
            result = {
                "step_id": step_info.get("step_id", current_step + 1),
                "description": description,
                "tool": tool,
                "result": search_result
            }
        elif tool == "analyze":
            # 执行分析
            print("正在分析收集到的信息...")
            analysis_result = await self._analyze_async(task, context, step_results)
            print("分析完成")
            result = {
                "step_id": step_info.get("step_id", current_step + 1),
                "description": description,
                "tool": tool,
                "result": analysis_result
            }
        else:
            # 通用执行
            print("正在执行通用步骤...")
            general_result = await self._execute_general_async(task, description, context, step_results)
            print("步骤执行完成")
            result = {
                "step_id": step_info.get("step_id", current_step + 1),
                "description": description,
                "tool": tool,
                "result": general_result
            }
            
        return result
    
    async def _search_web_async(self, query):
        """异步执行网络搜索"""
        try:
            # 使用exa_search_main中的search_web_exa函数进行搜索
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
            from exa_search_main import search_web_exa
            search_result_str = await asyncio.get_event_loop().run_in_executor(
                None, search_web_exa, query
            )
            
            # 将搜索结果字符串转换为字典列表格式
            # 由于search_web_exa返回格式化字符串，我们需要解析它
            # 这里简单地将整个结果作为一个条目返回
            formatted_results = [{
                "title": f"搜索结果: {query}",
                "snippet": search_result_str[:500] + "..." if len(search_result_str) > 500 else search_result_str,
                "link": ""
            }]
            
            return formatted_results
        except Exception as e:
            print(f"搜索错误: {str(e)}")
            return [{"title": "搜索错误", "snippet": str(e), "link": ""}]
    
    async def _analyze_async(self, task, context, step_results):
        """异步执行分析"""
        prompt = f"""
请分析以下信息，为任务提供有价值的见解:

任务: {task}

上下文: {context}

之前的步骤结果:
{json.dumps(step_results, ensure_ascii=False, indent=2)}

请提供详细的分析报告，包括:
1. 关键信息总结
2. 发现的模式或趋势
3. 潜在的问题或挑战
4. 建议的下一步行动
"""
        
        try:
            analysis = await call_llm_async(prompt)
            return analysis
        except Exception as e:
            return f"分析出错: {str(e)}"
    
    async def _execute_general_async(self, task, description, context, step_results):
        """异步执行通用步骤"""
        prompt = f"""
请执行以下步骤:

任务: {task}

步骤描述: {description}

上下文: {context}

之前的步骤结果:
{json.dumps(step_results, ensure_ascii=False, indent=2)}

请执行此步骤并提供结果。
"""
        
        try:
            result = await call_llm_async(prompt)
            return result
        except Exception as e:
            return f"执行出错: {str(e)}"
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理阶段：更新共享状态"""
        if prep_res is None:
            print("\n=== 所有步骤执行完成 ===")
            return "generate_response"  # 所有步骤已完成，生成最终响应
            
        # 更新步骤结果
        step_results = shared.get("step_results", [])
        step_results.append(exec_res)
        shared["step_results"] = step_results
        
        # 更新当前步骤
        current_step = shared.get("current_step", 0)
        shared["current_step"] = current_step + 1
        
        # 打印步骤结果摘要
        step_id = exec_res.get("step_id", current_step + 1)
        description = exec_res.get("description", "")
        tool = exec_res.get("tool", "general")
        result = exec_res.get("result", "")
        
        print(f"\n步骤 {step_id} 结果摘要:")
        print(f"描述: {description}")
        print(f"工具: {tool}")
        
        # 确保result是字典类型
        if isinstance(result, str):
            # 如果result是字符串，转换为字典格式
            result_dict = {
                "content": result,
                "type": "text"
            }
        elif isinstance(result, list):
            # 如果result是列表，保持原样
            result_dict = result
        else:
            # 其他情况，尝试转换为字典
            try:
                result_dict = dict(result) if hasattr(result, '__dict__') else {"content": str(result)}
            except:
                result_dict = {"content": str(result)}
        
        if tool == "search_web" and isinstance(result_dict, list):
            print(f"找到 {len(result_dict)} 条搜索结果:")
            for i, item in enumerate(result_dict[:3], 1):  # 只显示前3条结果
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                print(f"  {i}. {title}")
                if snippet:
                    print(f"     {snippet[:100]}...")  # 只显示前100个字符
        else:
            # 对于其他工具，显示结果的前100个字符
            if isinstance(result_dict, dict) and "content" in result_dict:
                result_str = result_dict["content"]
            else:
                result_str = str(result_dict)
            if len(result_str) > 100:
                result_str = result_str[:100] + "..."
            print(f"结果: {result_str}")
        
        # 检查是否还有更多步骤
        total_steps = shared.get("total_steps", 0)
        if shared["current_step"] >= total_steps:
            print(f"\n=== 所有步骤执行完成 ({shared['current_step']}/{total_steps}) ===")
            return "generate_response"  # 所有步骤已完成，生成最终响应
        else:
            print(f"\n步骤 {shared['current_step']}/{total_steps} 完成，继续下一步...")
            return "execute_plan"  # 继续执行下一个步骤