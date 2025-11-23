import os
import sys
from typing import List, Dict, Any

# 添加上级目录到路径，以便导入PocketFlow和utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pocketflow import Node
from utils.utils import call_llm

class ResponseGenerator(Node):
    """响应生成节点，使用检索到的文档生成最终答案"""
    
    def __init__(self, model_name=None, temperature=0.01, max_tokens=4000):
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = """你是一个用于问答任务的助手。使用以下检索到的上下文来回答问题。
如果你不知道答案，就直接说不知道。最多使用三句话，并保持回答简洁。"""
    
    def prep(self, shared):
        """准备阶段：从共享状态中获取查询和检索到的文档"""
        query = shared.get("query", "")
        documents = shared.get("retrieved_documents", [])
        return {"query": query, "documents": documents}
    
    def exec(self, prep_res):
        """执行阶段：使用LLM生成响应"""
        query = prep_res["query"]
        documents = prep_res["documents"]
        
        # 从文档格式化上下文
        context = ""
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            if content:
                context += f"\n文档 {i+1}:\n{content[:1000]}...\n"  # 限制每个文档的长度
        
        # 创建提示
        prompt = f"{self.system_prompt}\n\n问题：{query}\n上下文：{context}\n回答："
        
        # 调用LLM生成响应
        response = call_llm(prompt)
        
        return response
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将生成的响应添加到共享状态中"""
        shared["response"] = exec_res
        return "default"


class AgenticResponseGenerator(Node):
    """智能响应生成节点，使用多步推理和验证生成更准确的答案"""
    
    def __init__(self, model_name=None, temperature=0.01, max_tokens=4000):
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = """你是一个高级问答助手。你需要分析提供的文档，评估它们的相关性，
并基于最相关的信息生成准确的回答。如果文档不足以回答问题，请说明需要更多信息。"""
    
    def prep(self, shared):
        """准备阶段：从共享状态中获取查询和检索到的文档"""
        query = shared.get("query", "")
        documents = shared.get("retrieved_documents", [])
        return {"query": query, "documents": documents}
    
    def exec(self, prep_res):
        """执行阶段：使用多步推理生成响应"""
        query = prep_res["query"]
        documents = prep_res["documents"]
        
        # 第一步：评估文档相关性
        relevance_prompt = f"""对于问题："{query}"，评估以下文档的相关性（1-10分），
并简要说明原因。只返回评分和原因，不要回答问题本身。

文档：
"""
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            title = doc.get("title", "")
            relevance_prompt += f"\n文档 {i+1}: {title}\n{content[:500]}...\n"
        
        relevance_response = call_llm(relevance_prompt)
        
        # 第二步：基于相关性分析生成最终答案
        final_prompt = f"""{self.system_prompt}

问题：{query}

文档相关性分析：
{relevance_response}

请基于最相关的文档生成准确的回答。如果信息不足，请说明需要哪些额外信息。
"""
        
        final_response = call_llm(final_prompt)
        
        return final_response
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将生成的响应添加到共享状态中"""
        shared["response"] = exec_res
        shared["analysis"] = exec_res  # 保存分析过程
        return "default"