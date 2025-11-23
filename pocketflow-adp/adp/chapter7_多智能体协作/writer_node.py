"""
写作智能体节点 - 负责根据研究结果生成内容
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Node
from utils.utils import call_llm


class WriterNode(Node):
    """
    写作智能体节点，负责根据研究结果生成内容
    """
    
    def prep(self, shared):
        """准备写作任务"""
        # 从共享状态中获取研究结果
        research_results = shared.get("research_results", "")
        web_research_results = shared.get("web_research_results", {})
        target_audience = shared.get("target_audience", "一般读者")
        content_type = shared.get("content_type", "博客文章")
        word_count = shared.get("word_count", "500")
        
        # 构建写作提示
        if web_research_results and "search_summary" in web_research_results:
            # 如果有网络搜索结果，结合使用
            writing_prompt = f"""
            作为一名技术内容作家，请基于以下研究结果撰写一篇{content_type}：
            
            研究结果：
            {research_results}
            
            网络搜索总结：
            {web_research_results['search_summary']}
            
            目标受众：{target_audience}
            字数要求：约{word_count}字
            
            请确保内容：
            1. 结构清晰，逻辑连贯
            2. 语言通俗易懂，适合目标受众
            3. 包含实际案例和应用
            4. 有吸引力的标题和引言
            """
        else:
            # 只有基础研究结果
            writing_prompt = f"""
            作为一名技术内容作家，请基于以下研究结果撰写一篇{content_type}：
            
            研究结果：
            {research_results}
            
            目标受众：{target_audience}
            字数要求：约{word_count}字
            
            请确保内容：
            1. 结构清晰，逻辑连贯
            2. 语言通俗易懂，适合目标受众
            3. 包含实际案例和应用
            4. 有吸引力的标题和引言
            """
        
        return writing_prompt
    
    def exec(self, writing_prompt):
        """执行写作任务"""
        # 使用LLM生成内容
        content = call_llm(writing_prompt)
        return content
    
    def post(self, shared, prep_res, exec_res):
        """处理写作结果"""
        # 将生成的内容存储到共享状态
        shared["generated_content"] = exec_res
        shared["writing_completed"] = True


class ReviewerNode(Node):
    """
    审阅智能体节点，负责审阅和改进内容
    """
    
    def prep(self, shared):
        """准备审阅任务"""
        # 从共享状态中获取生成的内容
        content = shared.get("generated_content", "")
        review_criteria = shared.get("review_criteria", "准确性、可读性、吸引力")
        
        # 构建审阅提示
        review_prompt = f"""
        请审阅以下内容，并提供改进建议：
        
        内容：
        {content}
        
        审阅标准：{review_criteria}
        
        请提供：
        1. 内容优点分析
        2. 需要改进的地方
        3. 具体修改建议
        4. 修改后的完整内容（如果需要）
        """
        
        return review_prompt
    
    def exec(self, review_prompt):
        """执行审阅任务"""
        # 使用LLM进行内容审阅
        review_result = call_llm(review_prompt)
        return review_result
    
    def post(self, shared, prep_res, exec_res):
        """处理审阅结果"""
        # 将审阅结果存储到共享状态
        shared["review_result"] = exec_res
        shared["review_completed"] = True


class FinalizerNode(Node):
    """
    最终化智能体节点，负责整合所有结果并生成最终输出
    """
    
    def prep(self, shared):
        """准备最终化任务"""
        # 从共享状态中获取所有相关结果
        generated_content = shared.get("generated_content", "")
        review_result = shared.get("review_result", "")
        
        # 构建最终化提示
        finalization_prompt = f"""
        基于原始内容和审阅结果，请生成最终版本：
        
        原始内容：
        {generated_content}
        
        审阅结果：
        {review_result}
        
        请整合审阅建议，生成最终版本的内容，确保：
        1. 内容准确、完整
        2. 语言流畅、专业
        3. 结构清晰、有逻辑
        4. 符合目标受众需求
        """
        
        return finalization_prompt
    
    def exec(self, finalization_prompt):
        """执行最终化任务"""
        # 使用LLM生成最终内容
        final_content = call_llm(finalization_prompt)
        return final_content
    
    def post(self, shared, prep_res, exec_res):
        """处理最终化结果"""
        # 将最终内容存储到共享状态
        shared["final_content"] = exec_res
        shared["finalization_completed"] = True