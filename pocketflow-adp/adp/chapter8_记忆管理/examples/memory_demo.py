"""
演示短期和长期记忆的基本功能
"""
import sys
import os
import time

# 获取项目根目录路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
utils_path = os.path.join(project_root, 'utils')

# 直接导入模块
sys.path.insert(0, utils_path)
import utils
import exa_search_main

# 使用模块中的函数
call_llm = utils.call_llm
search_web_exa = exa_search_main.exa_web_search

# 添加记忆管理模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from short_term_memory import SessionService, StateManager
from long_term_memory import MemoryService, MemoryManager

def demo_short_term_memory():
    """演示短期记忆功能"""
    print("=== 短期记忆演示 ===")
    
    # 创建会话服务
    session_service = SessionService()
    
    # 创建新会话
    session = session_service.create_session(
        app_name="demo_app",
        user_id="demo_user",
        session_id="demo_session"
    )
    
    print(f"创建会话: {session.id}")
    
    # 添加一些消息
    messages = [
        ("user", "你好，我想了解一下人工智能"),
        ("assistant", "你好！人工智能是一个广泛的领域，包括机器学习、深度学习等多个方向。"),
        ("user", "能详细解释一下机器学习吗？"),
        ("assistant", "机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。")
    ]
    
    for role, content in messages:
        session_service.add_message(session.id, role, content)
        print(f"添加{role}消息: {content[:30]}...")
    
    # 更新会话状态
    session_service.update_session_state(session.id, {
        StateManager.get_user_state_key("language"): "zh-CN",
        StateManager.get_user_state_key("interests"): ["AI", "ML"],
        StateManager.get_temp_state_key("current_topic"): "machine_learning"
    })
    
    # 获取会话信息
    updated_session = session_service.get_session("demo_app", "demo_user", "demo_session")
    print(f"\n会话信息:")
    print(f"消息数量: {len(updated_session.messages)}")
    print(f"状态: {updated_session.state}")
    
    # 获取上下文窗口
    context = session_service.get_context_window(session.id)
    print(f"\n上下文窗口消息数量: {len(context)}")
    
    print("\n短期记忆演示完成\n")

def demo_long_term_memory():
    """演示长期记忆功能"""
    print("=== 长期记忆演示 ===")
    
    # 创建记忆服务
    memory_service = MemoryService()
    
    # 添加一些记忆
    memories = [
        ("用户询问了关于机器学习的问题，我解释了监督学习和无监督学习的区别。", 
         {"topic": "机器学习", "user_id": "demo_user", "type": "conversation"}),
        
        ("用户询问了关于深度学习的问题，我解释了神经网络的基本原理。", 
         {"topic": "深度学习", "user_id": "demo_user", "type": "conversation"}),
        
        ("用户询问了关于自然语言处理的问题，我介绍了NLP的主要应用领域。", 
         {"topic": "自然语言处理", "user_id": "demo_user", "type": "conversation"}),
    ]
    
    memory_ids = []
    for content, metadata in memories:
        memory_id = memory_service.add_memory(content, metadata)
        memory_ids.append(memory_id)
        print(f"添加记忆: {content[:30]}...")
    
    # 搜索记忆
    search_query = "神经网络"
    search_results = memory_service.search_memories(search_query, top_k=2)
    
    print(f"\n搜索 '{search_query}' 的结果:")
    for memory_item, similarity in search_results:
        print(f"内容: {memory_item.content}")
        print(f"相似度: {similarity:.4f}")
        print(f"元数据: {memory_item.metadata}")
        print("---")
    
    # 获取最近的记忆
    recent_memories = memory_service.get_recent_memories(2)
    print(f"\n最近的记忆:")
    for memory in recent_memories:
        print(f"内容: {memory.content}")
        print(f"创建时间: {time.ctime(memory.created_at)}")
        print("---")
    
    print("\n长期记忆演示完成\n")

def demo_memory_integration():
    """演示记忆集成功能"""
    print("=== 记忆集成演示 ===")
    
    # 创建会话服务和记忆服务
    session_service = SessionService()
    memory_service = MemoryService()
    memory_manager = MemoryManager(session_service, memory_service)
    
    # 创建会话 - 使用正确的session_id格式
    session = session_service.create_session(
        app_name="integrated_demo",
        user_id="demo_user",
        session_id="integrated_demo_demo_user_integrated_session"
    )
    
    print(f"创建会话: {session.id}")
    
    # 模拟一些对话
    conversations = [
        ("你好，我想了解一下人工智能", "你好！人工智能是一个广泛的领域，包括机器学习、深度学习等多个方向。"),
        ("机器学习有哪些类型？", "机器学习主要分为监督学习、无监督学习和强化学习三种类型。"),
        ("监督学习和无监督学习有什么区别？", "监督学习使用标记数据进行训练，而无监督学习从未标记数据中发现模式。")
    ]
    
    for user_msg, assistant_msg in conversations:
        # 添加到短期记忆
        session_service.add_message(session.id, "user", user_msg)
        session_service.add_message(session.id, "assistant", assistant_msg)
        
        # 添加到长期记忆
        memory_manager.add_conversation_to_memory(session.id, user_msg, assistant_msg)
        
        print(f"对话: {user_msg[:30]}...")
    
    # 模拟新查询
    new_query = "请解释一下监督学习的概念"
    print(f"\n新查询: {new_query}")
    
    # 搜索相关记忆
    relevant_memories = memory_manager.search_relevant_memories(session.id, new_query, top_k=2)
    
    print("\n相关记忆:")
    for memory in relevant_memories:
        print(f"- {memory}")
    
    # 获取包含记忆的上下文
    context = memory_manager.get_context_with_memories(session.id, new_query)
    
    print(f"\n上下文消息数量: {len(context)}")
    for i, msg in enumerate(context):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:50] + "..."
        print(f"{i+1}. [{role}] {content}")
    
    print("\n记忆集成演示完成\n")

def demo_web_search_integration():
    """演示网络搜索集成功能"""
    print("=== 网络搜索集成演示 ===")
    
    try:
        # 执行网络搜索
        query = "人工智能最新发展"
        print(f"搜索查询: {query}")
        
        # 使用Exa搜索API URL
        exa_api_url = "https://api.exa.ai/search"
        search_results = search_web_exa(query, exa_api_url, num_result=3)
        
        # 提取搜索结果
        extracted_results = exa_search_main.extract_relevant_info(search_results)
        
        print("\n搜索结果:")
        for i, result in enumerate(extracted_results, 1):
            title = result.get("title", "无标题")
            url = result.get("url", "无URL")
            print(f"{i}. {title}")
            print(f"   URL: {url}")
        
        # 将搜索结果添加到记忆
        memory_service = MemoryService()
        search_memory = f"用户搜索了 '{query}'，找到了 {len(search_results)} 个结果。"
        memory_id = memory_service.add_memory(
            search_memory,
            {"type": "web_search", "query": query, "result_count": len(search_results)}
        )
        
        print(f"\n搜索记忆已添加，ID: {memory_id}")
        
    except Exception as e:
        print(f"搜索过程中出错: {e}")
        print("这可能是由于缺少搜索API密钥或其他配置问题。")
    
    print("\n网络搜索集成演示完成\n")

def main():
    """主函数"""
    print("记忆管理演示程序\n")
    
    # 演示短期记忆
    demo_short_term_memory()
    
    # 演示长期记忆
    demo_long_term_memory()
    
    # 演示记忆集成
    demo_memory_integration()
    
    # 演示网络搜索集成
    demo_web_search_integration()
    
    print("所有演示完成！")

if __name__ == "__main__":
    main()