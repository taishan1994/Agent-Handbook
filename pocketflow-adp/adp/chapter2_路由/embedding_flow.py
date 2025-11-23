import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# 添加PocketFlow目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

from pocketflow import Node, Flow
from utils.utils import call_llm, get_embedding
from flow import BookingHandlerNode, InfoHandlerNode, UnclearHandlerNode
import numpy as np

class EmbeddingRouterNode(Node):
    """
    基于嵌入的路由节点：使用嵌入相似度决定路由到哪个处理节点
    """
    def __init__(self):
        super().__init__()
        # 预定义的示例请求及其对应的路由
        self.examples = {
            "booker": [
                "我想预订一张机票",
                "帮我预订酒店",
                "预订一个会议室",
                "我想订火车票"
            ],
            "info": [
                "请告诉我天气情况",
                "查询股票价格",
                "了解新闻",
                "获取产品信息"
            ],
            "unclear": [
                "帮我做点事",
                "随便来点",
                "不知道"
            ]
        }
        
        # 预计算示例的嵌入
        self.example_embeddings = {}
        for category, examples in self.examples.items():
            self.example_embeddings[category] = get_embedding(examples)
    
    def prep(self, shared):
        # 从共享状态中获取用户请求
        return shared["user_request"]
    
    def exec(self, request):
        # 获取用户请求的嵌入
        request_embedding = get_embedding([request])[0]
        
        # 计算与各类别的相似度
        similarities = {}
        for category, embeddings in self.example_embeddings.items():
            # 计算余弦相似度
            similarities[category] = np.mean([
                np.dot(request_embedding, emb) / (np.linalg.norm(request_embedding) * np.linalg.norm(emb))
                for emb in embeddings
            ])
        
        # 选择相似度最高的类别
        best_category = max(similarities, key=similarities.get)
        return best_category
    
    def post(self, shared, prep_res, exec_res):
        # 将路由决策存储到共享状态
        shared["route_decision"] = exec_res
        # 返回路由决策，用于流程控制
        return exec_res

class HybridRouterNode(Node):
    """
    混合路由节点：结合LLM和嵌入分析决定路由
    """
    def __init__(self):
        super().__init__()
        # 预定义的示例请求及其对应的路由
        self.examples = {
            "booker": [
                "我想预订一张机票",
                "帮我预订酒店",
                "预订一个会议室",
                "我想订火车票"
            ],
            "info": [
                "请告诉我天气情况",
                "查询股票价格",
                "了解新闻",
                "获取产品信息"
            ],
            "unclear": [
                "帮我做点事",
                "随便来点",
                "不知道"
            ]
        }
        
        # 预计算示例的嵌入
        self.example_embeddings = {}
        for category, examples in self.examples.items():
            self.example_embeddings[category] = get_embedding(examples)
    
    def prep(self, shared):
        # 从共享状态中获取用户请求
        return shared["user_request"]
    
    def exec(self, request):
        # 获取用户请求的嵌入
        request_embedding = get_embedding([request])[0]
        
        # 计算与各类别的相似度
        similarities = {}
        for category, embeddings in self.example_embeddings.items():
            # 计算余弦相似度
            similarities[category] = np.mean([
                np.dot(request_embedding, emb) / (np.linalg.norm(request_embedding) * np.linalg.norm(emb))
                for emb in embeddings
            ])
        
        # 获取相似度最高的类别
        embedding_category = max(similarities, key=similarities.get)
        embedding_confidence = similarities[embedding_category]
        
        # 如果嵌入相似度足够高，直接使用嵌入结果
        if embedding_confidence > 0.7:
            return embedding_category
        
        # 否则使用LLM进行更细致的分析
        prompt = f"""分析以下用户请求并确定哪个专家处理程序应处理它。
- 如果请求与预订航班或酒店相关，输出 'booker'。
- 对于所有其他一般信息问题，输出 'info'。
- 如果请求不清楚或不适合任一类别，输出 'unclear'。
只输出一个词：'booker'、'info' 或 'unclear'。

用户请求: {request}"""
        
        llm_category = call_llm(prompt).strip().lower()
        
        # 结合嵌入和LLM的结果，优先考虑LLM的结果
        return llm_category if llm_category in ["booker", "info", "unclear"] else embedding_category
    
    def post(self, shared, prep_res, exec_res):
        # 将路由决策存储到共享状态
        shared["route_decision"] = exec_res
        # 返回路由决策，用于流程控制
        return exec_res

class EmbeddingRoutingFlow:
    """
    基于嵌入的路由流程
    """
    def __init__(self):
        # 创建节点实例
        self.router = EmbeddingRouterNode()
        self.booking_handler = BookingHandlerNode()
        self.info_handler = InfoHandlerNode()
        self.unclear_handler = UnclearHandlerNode()
        
        # 设置节点连接
        self.router.next(self.booking_handler, action="booker")
        self.router.next(self.info_handler, action="info")
        self.router.next(self.unclear_handler, action="unclear")
        
        # 创建流程
        self.flow = Flow(start=self.router)
    
    def run(self, shared_state):
        """运行基于嵌入的路由流程"""
        return self.flow.run(shared_state)

class HybridRoutingFlow:
    """
    混合路由流程：结合嵌入和LLM分析
    """
    def __init__(self):
        # 创建节点实例
        self.router = HybridRouterNode()
        self.booking_handler = BookingHandlerNode()
        self.info_handler = InfoHandlerNode()
        self.unclear_handler = UnclearHandlerNode()
        
        # 设置节点连接
        self.router.next(self.booking_handler, action="booker")
        self.router.next(self.info_handler, action="info")
        self.router.next(self.unclear_handler, action="unclear")
        
        # 创建流程
        self.flow = Flow(start=self.router)
    
    def run(self, shared_state):
        """运行混合路由流程"""
        return self.flow.run(shared_state)

# 创建全局流程实例
embedding_routing_flow = EmbeddingRoutingFlow()
hybrid_routing_flow = HybridRoutingFlow()