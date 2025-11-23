import sys
import os
import asyncio
import copy
from typing import Dict, Any, List, Optional

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils import call_llm_async
from pocketflow import AsyncNode, AsyncFlow, _ConditionalTransition


class GeneratorNode(AsyncNode):
    """生成器节点，负责生成初始输出"""
    
    def __init__(self, name="generator"):
        super().__init__(max_retries=1, wait=0)
        self.name = name
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备生成器节点的输入"""
        task_prompt = shared_state.get("task_prompt", "")
        previous_critique = shared_state.get("previous_critique", "")
        iteration = shared_state.get("iteration", 1)
        
        # 如果是第一次迭代，直接使用任务提示
        if iteration == 1:
            prompt = task_prompt
        else:
            # 后续迭代，结合之前的批评意见
            prompt = f"""
            原始任务：{task_prompt}
            
            之前的代码版本：
            {shared_state.get('current_code', '')}
            
            评审意见：
            {previous_critique}
            
            请根据评审意见改进代码。确保解决所有指出的问题。
            """
        
        return {"prompt": prompt}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行生成器节点"""
        prompt = prep_result.get("prompt", "")
        generated_content = await call_llm_async(prompt)
        return {"generated_content": generated_content}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理生成器节点结果"""
        shared_state["current_code"] = exec_result.get("generated_content", "")
        shared_state["iteration"] = shared_state.get("iteration", 1) + 1
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        return "default"  # 返回默认action字符串


class ReviewerNode(AsyncNode):
    """评审者节点，负责评估生成器的输出"""
    
    def __init__(self, name="reviewer"):
        super().__init__(max_retries=1, wait=0)
        self.name = name
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备评审者节点的输入"""
        task_prompt = shared_state.get("task_prompt", "")
        current_code = shared_state.get("current_code", "")
        
        reviewer_prompt = f"""
        你是一名高级软件工程师和Python专家。
        你的角色是执行细致的代码审查。
        根据原始任务要求批判性地评估提供的Python代码。
        查找错误、风格问题、缺失的边缘情况和改进领域。
        
        原始任务：
        {task_prompt}
        
        要审查的代码：
        {current_code}
        
        如果代码完美并满足所有要求，用单一短语'CODE_IS_PERFECT'响应。
        否则，提供批评的项目符号列表。
        """
        
        return {"prompt": reviewer_prompt}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行评审者节点"""
        prompt = prep_result.get("prompt", "")
        critique = await call_llm_async(prompt)
        return {"critique": critique}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理评审者节点结果"""
        critique = exec_result.get("critique", "")
        shared_state["previous_critique"] = critique
        
        # 检查代码是否完美
        if "CODE_IS_PERFECT" in critique:
            shared_state["is_perfect"] = True
            shared_state["final_critique"] = "代码评审通过，无需进一步修改。"
        else:
            shared_state["is_perfect"] = False
            shared_state["final_critique"] = critique
        
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        return "default"  # 返回默认action字符串


class CheckPerfectionNode(AsyncNode):
    """检查代码是否完美的节点"""
    
    def __init__(self, name="check_perfection"):
        super().__init__(max_retries=1, wait=0)
        self.name = name
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备检查节点的输入"""
        is_perfect = shared_state.get("is_perfect", False)
        max_iterations = shared_state.get("max_iterations", 3)
        current_iteration = shared_state.get("iteration", 1)
        
        return {
            "is_perfect": is_perfect,
            "max_iterations": max_iterations,
            "current_iteration": current_iteration
        }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行检查节点"""
        is_perfect = prep_result.get("is_perfect", False)
        max_iterations = prep_result.get("max_iterations", 3)
        current_iteration = prep_result.get("current_iteration", 1)
        
        # 如果代码完美或达到最大迭代次数，则结束流程
        should_continue = not (is_perfect or current_iteration > max_iterations)
        
        return {"should_continue": should_continue}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理检查节点结果"""
        shared_state["should_continue"] = exec_result.get("should_continue", False)
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        
        # 根据should_continue决定返回的action
        should_continue = shared_state.get("should_continue", False)
        return "continue" if should_continue else "end"


class ReflectionFlow(AsyncFlow):
    """反思模式流程"""
    
    def __init__(self):
        # 创建节点
        generator = GeneratorNode("generator")
        reviewer = ReviewerNode("reviewer")
        check_perfection = CheckPerfectionNode("check_perfection")
        
        # 设置流程
        super().__init__(start=generator)
        
        # 定义节点之间的转换
        generator.next(reviewer)  # 生成器完成后进入评审者
        reviewer.next(check_perfection)  # 评审者完成后检查条件
        
        # 使用条件转换
        check_perfection - "continue" >> generator  # 如果需要继续，返回生成器
        check_perfection.next(None)  # 默认结束流程
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备流程输入"""
        # 设置默认值
        shared_state.setdefault("iteration", 1)
        shared_state.setdefault("max_iterations", 3)
        shared_state.setdefault("is_perfect", False)
        
        return shared_state
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理流程结果"""
        # 添加最终结果摘要
        shared_state["final_result"] = shared_state.get("current_code", "")
        shared_state["total_iterations"] = shared_state.get("iteration", 1) - 1
        shared_state["completed_successfully"] = shared_state.get("is_perfect", False)
        
        return shared_state
    
    async def _orch_async(self, shared_state, params=None):
        """重写编排方法以支持条件转换"""
        curr = copy.copy(self.start_node)
        p = params or {**self.params}
        last_action = None
        
        while curr:
            curr.set_params(p)
            
            if isinstance(curr, AsyncNode):
                last_action = await curr._run_async(shared_state)
            else:
                last_action = curr._run(shared_state)
            
            # 特殊处理CheckPerfectionNode
            if isinstance(curr, CheckPerfectionNode):
                should_continue = shared_state.get("should_continue", False)
                if should_continue:
                    curr = copy.copy(self.get_next_node(curr, "continue"))
                else:
                    curr = None
            else:
                curr = copy.copy(self.get_next_node(curr, last_action))
        
        return last_action


async def run_reflection_example():
    """运行反思模式示例"""
    
    # 定义任务
    task_prompt = """
    你的任务是创建一个名为`calculate_factorial`的Python函数。
    此函数应执行以下操作：
    1. 接受单个整数`n`作为输入。
    2. 计算其阶乘(n!)。
    3. 包含清楚解释函数功能的文档字符串。
    4. 处理边缘情况：0的阶乘是1。
    5. 处理无效输入：如果输入是负数，则引发ValueError。
    """
    
    # 初始化共享状态
    shared_state = {
        "task_prompt": task_prompt,
        "max_iterations": 3
    }
    
    # 创建并运行反思流程
    reflection_flow = ReflectionFlow()
    result = await reflection_flow.run_async(shared_state)
    
    # 打印结果
    print("\n" + "="*30 + " 最终结果 " + "="*30)
    print(f"\n总迭代次数: {result['total_iterations']}")
    print(f"是否成功完成: {'是' if result['completed_successfully'] else '否'}")
    print("\n反思过程后的最终精炼代码：\n")
    print(result['final_result'])
    
    if not result['completed_successfully'] and result['total_iterations'] >= result['max_iterations']:
        print("\n注意: 达到最大迭代次数，但代码仍未完全满足要求。")
        print("\n最后一次评审意见：\n")
        print(result['final_critique'])
    
    return result


if __name__ == "__main__":
    asyncio.run(run_reflection_example())