import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# 添加PocketFlow目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

from flow import routing_flow

def test_routing_examples():
    """测试路由模式的示例"""
    # 测试用例：预订请求
    booking_request = "我想预订一张从北京到上海的机票，时间是明天下午。"
    
    # 测试用例：信息查询
    info_request = "请告诉我上海迪士尼乐园的开放时间。"
    
    # 测试用例：不清楚的请求
    unclear_request = "帮我做点事"
    
    # 测试用例列表
    test_cases = [
        ("预订请求", booking_request),
        ("信息查询", info_request),
        ("不清楚的请求", unclear_request)
    ]
    
    # 运行测试
    for case_name, request in test_cases:
        print(f"\n{'='*50}")
        print(f"测试案例: {case_name}")
        print(f"用户请求: {request}")
        print(f"{'='*50}")
        
        # 创建共享状态
        shared_state = {"user_request": request}
        
        # 运行路由流程
        result = routing_flow.run(shared_state)
        
        # 显示结果
        route_decision = shared_state.get("route_decision", "未知")
        final_result = shared_state.get("final_result", "无结果")
        
        print(f"路由决策: {route_decision}")
        print(f"处理结果:\n{final_result}")
        print(f"{'='*50}\n")

if __name__ == "__main__":
    print("Chapter 2: Routing with PocketFlow")
    print("本示例展示了如何使用PocketFlow实现路由模式，根据用户请求动态决定处理流程。")
    test_routing_examples()