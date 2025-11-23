import os
import sys
import numpy as np
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import re

# 添加上级目录到路径，以便导入PocketFlow和utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pocketflow import Node
from utils.utils import get_embedding, call_llm
from utils.exa_search_main import exa_web_search, extract_relevant_info, extract_text_from_url

class DocumentRetriever(Node):
    """文档检索节点，负责从外部知识库检索相关文档"""
    
    def __init__(self, search_engine="exa", max_results=5):
        super().__init__()
        self.search_engine = search_engine
        self.max_results = max_results
        self.search_url = "https://api.exa.ai/search"
        
    def prep(self, shared):
        """准备阶段：从共享状态中获取查询"""
        query = shared.get("query", "")
        return {"query": query}
    
    def exec(self, prep_res):
        """执行阶段：根据查询检索相关文档"""
        query = prep_res["query"]
        
        # 使用Exa搜索引擎进行搜索
        if self.search_engine == "exa":
            search_results = exa_web_search(
                query=query,
                url=self.search_url,
                num_result=self.max_results
            )
            
            # 提取相关信息
            relevant_info = extract_relevant_info(search_results)
            
            # 获取每个搜索结果的详细内容
            documents = []
            for info in relevant_info:
                content = extract_text_from_url(info["url"], info["snippet"])
                documents.append({
                    "title": info["title"],
                    "url": info["url"],
                    "snippet": info["snippet"],
                    "content": content
                })
            
            return documents
        else:
            raise ValueError(f"Unsupported search engine: {self.search_engine}")
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将检索结果添加到共享状态中"""
        shared["retrieved_documents"] = exec_res
        return "default"


class VectorDocumentRetriever(Node):
    """向量文档检索节点，使用向量相似度检索文档"""
    
    def __init__(self, documents=None, top_k=5):
        super().__init__()
        self.documents = documents or []
        self.top_k = top_k
        self.embeddings = None
        
    def prep(self, shared):
        """准备阶段：从共享状态中获取查询并计算嵌入"""
        query = shared.get("query", "")
        query_embedding = get_embedding(query)
        return {"query": query, "query_embedding": query_embedding}
    
    def exec(self, prep_res):
        """执行阶段：计算文档相似度并返回最相关的文档"""
        query = prep_res["query"]
        query_embedding = prep_res["query_embedding"]
        
        # 如果文档嵌入尚未计算，先计算它们
        if self.embeddings is None:
            self.embeddings = []
            for doc in self.documents:
                content = doc.get("content", "")
                if content:
                    embedding = get_embedding(content)
                    self.embeddings.append(embedding)
                else:
                    self.embeddings.append(np.zeros_like(query_embedding))
        
        # 计算查询与每个文档的相似度
        similarities = []
        for doc_embedding in self.embeddings:
            # 计算余弦相似度
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            similarities.append(similarity)
        
        # 获取最相关的文档
        top_indices = np.argsort(similarities)[-self.top_k:][::-1]
        relevant_docs = [self.documents[i] for i in top_indices]
        
        return relevant_docs
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将检索结果添加到共享状态中"""
        shared["retrieved_documents"] = exec_res
        return "default"
    
    def add_documents(self, documents):
        """添加文档到检索器"""
        self.documents.extend(documents)
        # 重置嵌入，以便重新计算
        self.embeddings = None