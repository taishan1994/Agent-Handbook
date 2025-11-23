import asyncio
import sys
import os
from typing import Dict, Any, List
import copy

# 添加utils目录和PocketFlow路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

from utils import call_llm_async
from pocketflow import AsyncNode, AsyncFlow, _ConditionalTransition


class ContentGenerator(AsyncNode):
    """内容生成器节点，负责生成初始内容"""
    
    def __init__(self, name="content_generator"):
        super().__init__(max_retries=1, wait=0)
        self.name = name
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备生成器节点的输入"""
        topic = shared_state.get("topic", "")
        content_type = shared_state.get("content_type", "文章")
        previous_feedback = shared_state.get("previous_feedback", "")
        iteration = shared_state.get("iteration", 1)
        
        # 如果是第一次迭代，直接使用主题
        if iteration == 1:
            prompt = f"""
            请写一篇关于"{topic}"的{content_type}。
            要求内容准确、信息丰富、结构清晰。
            字数控制在500字左右。
            """
        else:
            # 后续迭代，结合之前的反馈
            prompt = f"""
            原始主题：{topic}
            内容类型：{content_type}
            
            之前的内容：
            {shared_state.get('current_content', '')}
            
            反馈意见：
            {previous_feedback}
            
            请根据反馈意见改进内容，确保解决所有指出的问题。
            """
        
        return {"prompt": prompt}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行生成器节点"""
        prompt = prep_result.get("prompt", "")
        generated_content = await call_llm_async(prompt)
        return {"generated_content": generated_content}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理生成器节点结果"""
        shared_state["current_content"] = exec_result.get("generated_content", "")
        shared_state["iteration"] = shared_state.get("iteration", 1) + 1
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        return "default"  # 返回默认action字符串


class ContentReviewer(AsyncNode):
    """内容评审者节点，负责评估生成的内容"""
    
    def __init__(self, name="content_reviewer"):
        super().__init__(max_retries=1, wait=0)
        self.name = name
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备评审者节点的输入"""
        topic = shared_state.get("topic", "")
        content_type = shared_state.get("content_type", "文章")
        current_content = shared_state.get("current_content", "")
        
        reviewer_prompt = f"""
        你是一名专业的内容编辑和评审专家。
        你的任务是评估以下关于"{topic}"的{content_type}。
        
        评估标准：
        1. 内容准确性 - 信息是否准确可靠
        2. 结构清晰度 - 内容组织是否清晰合理
        3. 语言表达 - 语言是否流畅、专业
        4. 完整性 - 是否全面覆盖主题
        5. 目标受众 - 是否适合目标受众
        
        要评估的内容：
        {current_content}
        
        如果内容完美并满足所有标准，用单一短语'CONTENT_IS_PERFECT'响应。
        否则，提供具体的改进建议列表。
        """
        
        return {"prompt": reviewer_prompt}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行评审者节点"""
        prompt = prep_result.get("prompt", "")
        review = await call_llm_async(prompt)
        return {"review": review}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理评审者节点结果"""
        review = exec_result.get("review", "")
        shared_state["previous_feedback"] = review
        
        # 检查内容是否完美
        if "CONTENT_IS_PERFECT" in review:
            shared_state["is_perfect"] = True
            shared_state["final_feedback"] = "内容评审通过，无需进一步修改。"
        else:
            shared_state["is_perfect"] = False
            shared_state["final_feedback"] = review
        
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        return "default"  # 返回默认action字符串


class ContentQualityCheck(AsyncNode):
    """检查内容质量的节点"""
    
    def __init__(self, name="quality_check"):
        super().__init__(max_retries=1, wait=0)
        self.name = name
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备检查节点的输入"""
        return {
            "content": shared_state.get("current_content", ""),
            "feedback": shared_state.get("feedback", "")
        }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行内容质量检查"""
        content = prep_result.get("content", "")
        feedback = prep_result.get("feedback", "")
        
        # 简单的质量检查逻辑
        quality_score = 0
        
        # 检查内容长度
        if len(content) > 100:
            quality_score += 1
        
        # 检查是否包含特定关键词
        keywords = ["示例", "说明", "步骤", "总结"]
        for keyword in keywords:
            if keyword in content:
                quality_score += 1
        
        # 检查是否有结构
        if "1." in content or "第一步" in content or "首先" in content:
            quality_score += 1
        
        # 检查是否有总结
        if "总结" in content or "结论" in content or "总之" in content:
            quality_score += 1
        
        # 如果有反馈，检查是否解决了反馈中的问题
        if feedback and feedback in content:
            quality_score += 1
        
        # 质量达到4分或以上认为合格
        is_perfect = quality_score >= 4
        
        return {
            "quality_score": quality_score,
            "is_perfect": is_perfect
        }
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理检查节点结果"""
        shared_state["is_perfect"] = exec_result.get("is_perfect", False)
        shared_state["quality_score"] = exec_result.get("quality_score", 0)
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        
        # 根据is_perfect决定返回的action
        is_perfect = shared_state.get("is_perfect", False)
        return "continue" if not is_perfect else "end"


class ContentReflectionFlow(AsyncFlow):
    """内容反思流程"""
    
    def __init__(self):
        # 创建节点
        generator = ContentGenerator()
        reviewer = ContentReviewer()
        quality_check = ContentQualityCheck()
        
        # 设置流程
        super().__init__(start=generator)
        
        # 定义节点之间的转换
        generator.next(reviewer)  # 生成器完成后进入评审者
        reviewer.next(quality_check)  # 评审者完成后检查条件
        
        # 使用条件转换
        quality_check - "continue" >> generator  # 如果需要继续，返回生成器
        quality_check.next(None)  # 默认结束流程
    
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
        shared_state["final_content"] = shared_state.get("current_content", "")
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
            
            # 特殊处理ContentQualityCheck
            if isinstance(curr, ContentQualityCheck):
                should_continue = not shared_state.get("is_perfect", False)
                if should_continue:
                    curr = copy.copy(self.get_next_node(curr, "continue"))
                else:
                    curr = None
            else:
                curr = copy.copy(self.get_next_node(curr, last_action))
        
        return last_action
    
    async def run(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """运行内容反思流程"""
        # 运行流程
        result = await self._run_async(shared_state)
        
        return result


async def demonstrate_content_reflection():
    """演示内容反思模式"""
    
    # 定义主题和内容类型
    topic = "人工智能在医疗健康领域的应用"
    content_type = "科普文章"
    
    # 初始化共享状态
    shared_state = {
        "topic": topic,
        "content_type": content_type,
        "max_iterations": 3
    }
    
    print(f"\n{'='*20} 内容反思模式演示 {'='*20}")
    print(f"主题: {topic}")
    print(f"内容类型: {content_type}")
    print(f"最大迭代次数: {shared_state['max_iterations']}")
    print("\n开始反思流程...\n")
    
    # 创建并运行内容反思流程
    reflection_flow = ContentReflectionFlow()
    result = await reflection_flow.run(shared_state)
    
    # 打印结果
    print("\n" + "="*20 + " 最终结果 " + "="*20)
    print(f"\n总迭代次数: {result['total_iterations']}")
    print(f"是否成功完成: {'是' if result['completed_successfully'] else '否'}")
    print("\n反思过程后的最终内容：\n")
    print(result['final_content'])
    
    if not result['completed_successfully'] and result['total_iterations'] >= result['max_iterations']:
        print("\n注意: 达到最大迭代次数，但内容可能仍有改进空间。")
        print("\n最后一次评审意见：\n")
        print(result['final_feedback'])
    
    return result


async def demonstrate_code_reflection():
    """演示代码反思模式"""
    from flow import ReflectionFlow
    
    # 定义任务
    task_prompt = """
    你的任务是创建一个名为`binary_search`的Python函数。
    此函数应执行以下操作：
    1. 接受一个已排序的列表和一个目标值作为输入。
    2. 使用二分查找算法在列表中查找目标值。
    3. 如果找到目标值，返回其索引；否则返回-1。
    4. 包含清楚解释函数功能的文档字符串。
    5. 处理边缘情况：空列表、单元素列表。
    6. 添加适当的类型提示。
    """
    
    # 初始化共享状态
    shared_state = {
        "task_prompt": task_prompt,
        "max_iterations": 3
    }
    
    print(f"\n{'='*20} 代码反思模式演示 {'='*20}")
    print("任务: 创建一个二分查找函数")
    print("要求: 包含文档字符串、处理边缘情况、添加类型提示")
    print("\n开始反思流程...\n")
    
    # 创建并运行反思流程
    reflection_flow = ReflectionFlow()
    result = await reflection_flow.run_async(shared_state)
    
    # 打印结果
    print("\n" + "="*20 + " 最终结果 " + "="*20)
    print(f"\n总迭代次数: {result['total_iterations']}")
    print(f"是否成功完成: {'是' if result['completed_successfully'] else '否'}")
    print("\n反思过程后的最终代码：\n")
    print(result['final_result'])
    
    if not result['completed_successfully'] and result['total_iterations'] >= result['max_iterations']:
        print("\n注意: 达到最大迭代次数，但代码可能仍有改进空间。")
    
    return result


async def main():
    """主函数，演示不同类型的反思模式"""
    print("="*60)
    print("PocketFlow 反思模式多样化演示")
    print("="*60)
    print("\n本演示将展示两种不同类型的反思模式应用：")
    print("1. 内容反思模式 - 用于改进文章内容")
    print("2. 代码反思模式 - 用于优化代码实现")
    
    # 演示内容反思模式
    await demonstrate_content_reflection()
    
    # 演示代码反思模式
    await demonstrate_code_reflection()
    
    # 打印总结
    print("\n" + "="*60)
    print("反思模式多样化演示完成")
    print("="*60)
    print("\n反思模式的关键优势:")
    print("- 通过迭代改进提升输出质量")
    print("- 自动识别和修复问题")
    print("- 适应不同类型的内容和任务")
    print("- 提供结构化的反馈和改进循环")
    
    print("\nPocketFlow实现的特点:")
    print("- 模块化节点设计，易于扩展")
    print("- 灵活的条件转换控制流程")
    print("- 简洁的异步处理机制")
    print("- 直观的流程定义和管理")


if __name__ == "__main__":
    asyncio.run(main())