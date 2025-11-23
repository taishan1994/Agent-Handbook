import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# 添加PocketFlow目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

from flow import routing_flow
from embedding_flow import embedding_routing_flow, hybrid_routing_flow

def test_embedding_routing_examples():
    """测试基于嵌入的路由模式示例"""
    # 测试用例
    test_cases = [
        ("预订请求", "我想预订一张从北京到上海的机票"),
        ("信息查询", "请告诉我今天的天气情况"),
        ("不清楚的请求", "帮我做点事"),
        ("相似预订请求", "帮我订个酒店房间"),
        ("相似信息查询", "查询最新的股票价格"),
        ("相似不清楚请求", "随便来点")
    ]
    
    print("\n" + "="*80)
    print("测试基于嵌入的路由模式")
    print("="*80)
    
    for case_name, request in test_cases:
        print(f"\n{'='*50}")
        print(f"测试案例: {case_name}")
        print(f"用户请求: {request}")
        print(f"{'='*50}")
        
        # 创建共享状态
        shared_state = {"user_request": request}
        
        # 运行基于嵌入的路由流程
        result = embedding_routing_flow.run(shared_state)
        
        # 显示结果
        route_decision = shared_state.get("route_decision", "未知")
        final_result = shared_state.get("final_result", "无结果")
        
        print(f"嵌入路由决策: {route_decision}")
        print(f"处理结果:\n{final_result}")
        print(f"{'='*50}\n")

def test_hybrid_routing_examples():
    """测试混合路由模式示例"""
    # 测试用例
    test_cases = [
        ("预订请求", "我想预订一张从北京到上海的机票"),
        ("信息查询", "请告诉我今天的天气情况"),
        ("不清楚的请求", "帮我做点事"),
        ("复杂预订请求", "我下个月要去上海出差，需要预订机票和酒店，要求是商务舱"),
        ("复杂信息查询", "分析一下最近科技行业的趋势"),
        ("复杂不清楚请求", "帮我处理一下那个事情")
    ]
    
    print("\n" + "="*80)
    print("测试混合路由模式（嵌入+LLM）")
    print("="*80)
    
    for case_name, request in test_cases:
        print(f"\n{'='*50}")
        print(f"测试案例: {case_name}")
        print(f"用户请求: {request}")
        print(f"{'='*50}")
        
        # 创建共享状态
        shared_state = {"user_request": request}
        
        # 运行混合路由流程
        result = hybrid_routing_flow.run(shared_state)
        
        # 显示结果
        route_decision = shared_state.get("route_decision", "未知")
        final_result = shared_state.get("final_result", "无结果")
        
        print(f"混合路由决策: {route_decision}")
        print(f"处理结果:\n{final_result}")
        print(f"{'='*50}\n")

def compare_routing_methods():
    """比较不同路由方法的决策"""
    # 测试用例
    test_cases = [
        "我想预订一张机票",
        "请告诉我天气情况",
        "帮我做点事",
        "帮我订个酒店房间",
        "查询最新的股票价格",
        "随便来点"
    ]
    
    print("\n" + "="*80)
    print("比较不同路由方法的决策")
    print("="*80)
    
    for request in test_cases:
        print(f"\n{'='*50}")
        print(f"用户请求: {request}")
        print(f"{'='*50}")
        
        # 创建共享状态
        shared_state_llm = {"user_request": request}
        shared_state_embedding = {"user_request": request}
        shared_state_hybrid = {"user_request": request}
        
        # 运行不同的路由流程
        routing_flow.run(shared_state_llm)
        embedding_routing_flow.run(shared_state_embedding)
        hybrid_routing_flow.run(shared_state_hybrid)
        
        # 显示结果
        llm_decision = shared_state_llm.get("route_decision", "未知")
        embedding_decision = shared_state_embedding.get("route_decision", "未知")
        hybrid_decision = shared_state_hybrid.get("route_decision", "未知")
        
        print(f"LLM路由决策: {llm_decision}")
        print(f"嵌入路由决策: {embedding_decision}")
        print(f"混合路由决策: {hybrid_decision}")
        print(f"{'='*50}\n")

if __name__ == "__main__":
    print("Chapter 2: Advanced Routing with PocketFlow")
    print("本示例展示了如何使用PocketFlow实现更高级的路由模式，包括基于嵌入的路由和混合路由。")
    
    # 测试基于嵌入的路由
    test_embedding_routing_examples()
    
    # 测试混合路由
    test_hybrid_routing_examples()
    
    # 比较不同路由方法
    compare_routing_methods()