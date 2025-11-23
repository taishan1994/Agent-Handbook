"""
研究智能体节点 - 负责收集和分析信息
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Node
from utils.utils import call_llm
from utils.exa_search_main import exa_web_search, extract_relevant_info, fetch_page_content


class ResearcherNode(Node):
    """
    研究智能体节点，负责收集和分析特定主题的信息
    """
    
    def prep(self, shared):
        """准备研究任务"""
        # 从共享状态中获取研究主题
        research_topic = shared.get("research_topic", "")
        context = shared.get("context", "")
        
        # 构建研究提示
        research_prompt = f"""
        作为一名高级研究分析师，请研究以下主题：
        主题：{research_topic}
        上下文：{context}
        
        请提供关于该主题的全面分析，包括：
        1. 关键概念和定义
        2. 最新发展趋势
        3. 实际应用案例
        4. 潜在影响和未来展望
        """
        
        return research_prompt
    
    def exec(self, research_prompt):
        """执行研究任务"""
        # 首先尝试使用LLM进行初步研究
        initial_research = call_llm(research_prompt)
        
        # 如果需要更深入的研究，可以使用网络搜索
        # 这里简化处理，直接返回LLM的研究结果
        return initial_research
    
    def post(self, shared, prep_res, exec_res):
        """处理研究结果"""
        # 将研究结果存储到共享状态
        shared["research_results"] = exec_res
        shared["research_completed"] = True


class WebResearcherNode(Node):
    """
    基于网络搜索的研究智能体节点
    """
    
    def prep(self, shared):
        """准备网络搜索任务"""
        # 从共享状态中获取研究主题
        research_topic = shared.get("research_topic", "")
        
        # 构建搜索查询
        search_query = f"{research_topic} 最新趋势 应用案例"
        
        return search_query
    
    def exec(self, search_query):
        """执行网络搜索"""
        # 使用Exa搜索API进行网络搜索
        search_url = "https://api.exa.ai/search"
        search_results = exa_web_search(search_query, search_url, num_result=5)
        
        # 提取相关信息
        relevant_info = extract_relevant_info(search_results)
        
        # 获取页面内容
        urls = [info["url"] for info in relevant_info]
        snippets = {info["url"]: info["snippet"] for info in relevant_info}
        
        # 并行获取页面内容
        page_contents = fetch_page_content(urls, snippets=snippets)
        
        # 整合搜索结果
        search_summary = call_llm(f"""
        基于以下搜索结果，请总结关于"{search_query}"的关键信息：
        
        {str(relevant_info)}
        
        请提供：
        1. 主要发现和趋势
        2. 重要数据点
        3. 实际应用案例
        4. 未来展望
        """)
        
        return {
            "search_results": relevant_info,
            "page_contents": page_contents,
            "search_summary": search_summary
        }
    
    def post(self, shared, prep_res, exec_res):
        """处理网络搜索结果"""
        # 将搜索结果存储到共享状态
        shared["web_research_results"] = exec_res
        shared["web_research_completed"] = True