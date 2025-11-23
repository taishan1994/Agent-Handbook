import os
import sys
from typing import Dict, Any

# 添加上级目录到路径，以便导入PocketFlow和utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pocketflow import Flow
from document_retriever import DocumentRetriever, VectorDocumentRetriever
from response_generator import ResponseGenerator, AgenticResponseGenerator

class RAGFlow:
    """基于PocketFlow的RAG流程实现"""
    
    def __init__(self, retriever_type="web", generator_type="basic"):
        """
        初始化RAG流程
        
        Args:
            retriever_type: 检索器类型 ("web" 或 "vector")
            generator_type: 生成器类型 ("basic" 或 "agentic")
        """
        self.retriever_type = retriever_type
        self.generator_type = generator_type
        self.flow = None
        self._build_flow()
    
    def _build_flow(self):
        """构建RAG流程"""
        # 创建检索器节点
        if self.retriever_type == "web":
            retriever = DocumentRetriever(max_results=5)
        elif self.retriever_type == "vector":
            retriever = VectorDocumentRetriever(top_k=5)
        else:
            raise ValueError(f"Unsupported retriever type: {self.retriever_type}")
        
        # 创建生成器节点
        if self.generator_type == "basic":
            generator = ResponseGenerator()
        elif self.generator_type == "agentic":
            generator = AgenticResponseGenerator()
        else:
            raise ValueError(f"Unsupported generator type: {self.generator_type}")
        
        # 构建流程
        retriever.next(generator)
        self.flow = Flow(start=retriever)
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        运行RAG流程
        
        Args:
            query: 用户查询
            
        Returns:
            包含查询结果的字典
        """
        # 初始化共享状态
        shared = {
            "query": query,
            "retrieved_documents": [],
            "response": "",
            "analysis": ""
        }
        
        # 运行流程
        self.flow.run(shared)
        
        return shared
    
    def add_documents(self, documents):
        """添加文档到向量检索器（仅当使用向量检索器时有效）"""
        if self.retriever_type == "vector":
            retriever = self.flow.start_node
            if hasattr(retriever, 'add_documents'):
                retriever.add_documents(documents)
        else:
            print("Web检索器不支持添加文档，请使用向量检索器类型")


class AgenticRAGFlow(RAGFlow):
    """智能RAG流程，包含额外的推理和验证步骤"""
    
    def __init__(self, retriever_type="web"):
        """
        初始化智能RAG流程
        
        Args:
            retriever_type: 检索器类型 ("web" 或 "vector")
        """
        super().__init__(retriever_type=retriever_type, generator_type="agentic")
    
    def run_with_analysis(self, query: str) -> Dict[str, Any]:
        """
        运行智能RAG流程并返回详细分析
        
        Args:
            query: 用户查询
            
        Returns:
            包含查询结果和分析的字典
        """
        result = self.run(query)
        
        # 添加额外的分析信息
        result["flow_type"] = "agentic"
        result["retriever_type"] = self.retriever_type
        result["analysis"] = result.get("analysis", "")
        
        return result


# 预定义的文档集合，用于向量检索示例
sample_documents = [
    {
        "title": "人工智能概述",
        "content": "人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。"
    },
    {
        "title": "机器学习基础",
        "content": "机器学习是人工智能的核心，是使计算机具有智能的根本途径。机器学习涉及概率论、统计学、逼近论、凸分析、算法复杂度理论等多门学科。机器学习算法包括监督学习、无监督学习和强化学习。"
    },
    {
        "title": "深度学习简介",
        "content": "深度学习是机器学习的一个子领域，它基于人工神经网络的学习方法。深度学习模型由多层神经网络组成，能够自动学习数据的层次化表示。深度学习在计算机视觉、自然语言处理等领域取得了突破性进展。"
    },
    {
        "title": "自然语言处理",
        "content": "自然语言处理是人工智能和语言学领域的分支学科，研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。自然语言处理包括语音识别、自然语言理解、自然语言生成等子领域。"
    },
    {
        "title": "计算机视觉",
        "content": "计算机视觉是一门研究如何使机器'看'的科学，更进一步的说，就是指用摄影机和电脑代替人眼对目标进行识别、跟踪和测量等机器视觉，并进一步做图形处理，使电脑处理成为更适合人眼观察或传送给仪器检测的图像。"
    }
]