import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# 添加PocketFlow目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

from pocketflow import Node, Flow
from utils.utils import call_llm

class RouterNode(Node):
    """
    路由节点：分析用户请求并决定路由到哪个处理节点
    """
    def prep(self, shared):
        # 从共享状态中获取用户请求
        return shared["user_request"]
    
    def exec(self, request):
        # 使用LLM分析请求并决定路由
        prompt = f"""分析以下用户请求并确定哪个专家处理程序应处理它。
- 如果请求与预订航班或酒店相关，输出 'booker'。
- 对于所有其他一般信息问题，输出 'info'。
- 如果请求不清楚或不适合任一类别，输出 'unclear'。
只输出一个词：'booker'、'info' 或 'unclear'。

用户请求: {request}"""
        return call_llm(prompt).strip().lower()
    
    def post(self, shared, prep_res, exec_res):
        # 将路由决策存储到共享状态
        shared["route_decision"] = exec_res
        # 返回路由决策，用于流程控制
        return exec_res

class BookingHandlerNode(Node):
    """
    预订处理节点：处理与预订相关的请求
    """
    def prep(self, shared):
        # 从共享状态中获取用户请求
        return shared["user_request"]
    
    def exec(self, request):
        # 模拟预订处理
        prompt = f"""处理以下预订请求，提供预订确认信息：
{request}

请提供一个模拟的预订确认，包括预订编号、日期和关键详情。"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # 将处理结果存储到共享状态
        shared["final_result"] = exec_res

class InfoHandlerNode(Node):
    """
    信息处理节点：处理一般信息查询
    """
    def prep(self, shared):
        # 从共享状态中获取用户请求
        return shared["user_request"]
    
    def exec(self, request):
        # 模拟信息查询处理
        prompt = f"""回答以下一般信息问题：
{request}

请提供准确、有用的信息来回答这个问题。"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # 将处理结果存储到共享状态
        shared["final_result"] = exec_res

class UnclearHandlerNode(Node):
    """
    不清楚请求处理节点：处理无法明确分类的请求
    """
    def prep(self, shared):
        # 从共享状态中获取用户请求
        return shared["user_request"]
    
    def exec(self, request):
        # 处理不清楚的请求
        prompt = f"""以下请求不清楚或无法分类，请提供一个澄清响应：
{request}

请礼貌地请求用户澄清他们的需求，并提供一些可能的选项。"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # 将处理结果存储到共享状态
        shared["final_result"] = exec_res

class ConditionalFlow:
    """
    条件流程：根据路由决策执行不同的处理节点
    """
    def __init__(self):
        # 创建节点实例
        self.router = RouterNode()
        self.booking_handler = BookingHandlerNode()
        self.info_handler = InfoHandlerNode()
        self.unclear_handler = UnclearHandlerNode()
        
        # 设置节点连接 - 使用条件路由
        self.router.next(self.booking_handler, action="booker")
        self.router.next(self.info_handler, action="info")
        self.router.next(self.unclear_handler, action="unclear")
        
        # 创建流程
        self.flow = Flow(start=self.router)
    
    def run(self, shared_state):
        """运行条件流程"""
        return self.flow.run(shared_state)

# 创建全局流程实例
routing_flow = ConditionalFlow()