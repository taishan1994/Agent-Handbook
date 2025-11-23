"""
记忆管理示例 - 使用PocketFlow实现
演示如何使用PocketFlow框架实现短期和长期记忆管理
"""
import os
import sys
import time
from typing import Dict, Any, List

# 获取项目根目录路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
utils_path = os.path.join(project_root, 'utils')

# 直接导入模块
sys.path.insert(0, utils_path)
import utils

# 使用模块中的函数
call_llm = utils.call_llm

# 添加记忆管理模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from short_term_memory import SessionService, StateManager
from long_term_memory import MemoryService, MemoryManager

# 添加PocketFlow路径
pocketflow_path = os.path.join(project_root, 'PocketFlow')
sys.path.insert(0, pocketflow_path)
from pocketflow import Flow, Node

class GetUserInputNode(Node):
    """获取用户输入节点"""
    
    def __init__(self):
        super().__init__()
        self.name = "get_user_input"
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        user_input = input("请输入您的问题: ")
        context["user_input"] = user_input
        context["timestamp"] = time.time()
        return context

class RetrieveMemoriesNode(Node):
    """检索相关记忆节点"""
    
    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.name = "retrieve_memories"
        self.memory_manager = memory_manager
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        session_id = context.get("session_id")
        user_input = context.get("user_input", "")
        
        if not session_id or not user_input:
            return context
        
        # 搜索相关记忆
        relevant_memories = self.memory_manager.search_relevant_memories(
            session_id, user_input, top_k=3
        )
        
        context["relevant_memories"] = relevant_memories
        return context

class GenerateResponseNode(Node):
    """生成响应节点"""
    
    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.name = "generate_response"
        self.memory_manager = memory_manager
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        user_input = context.get("user_input", "")
        session_id = context.get("session_id")
        
        # 获取包含相关记忆的上下文
        if session_id:
            memory_context = self.memory_manager.get_context_with_memories(session_id, user_input)
            print(f"[DEBUG] 检索到的记忆数量: {len([m for m in memory_context if m.get('metadata', {}).get('type') == 'memory_context'])}")
            for m in memory_context:
                if m.get('metadata', {}).get('type') == 'memory_context':
                    print(f"[DEBUG] 记忆内容: {m['content'][:100]}...")
            
            # 构建提示
            prompt = self._build_prompt_with_context(user_input, memory_context)
        else:
            # 如果没有session_id，使用基本提示
            print("[DEBUG] 没有session_id，使用基本提示")
            prompt = self._build_prompt(user_input, [])
        
        # 调用LLM生成响应
        response = call_llm(prompt)
        
        context["assistant_response"] = response
        
        # 将对话添加到短期记忆
        if session_id:
            self.memory_manager.session_service.add_message(session_id, "user", user_input)
            self.memory_manager.session_service.add_message(session_id, "assistant", response)
        
        return context
    
    def _build_prompt_with_context(self, user_input: str, memory_context: List[Dict[str, Any]]) -> str:
        """构建包含记忆上下文的提示"""
        prompt = "你是一个有帮助的助手。请根据以下信息回答用户的问题。\n\n"
        
        # 添加记忆上下文
        for item in memory_context:
            if item.get("metadata", {}).get("type") == "memory_context":
                prompt += item["content"] + "\n\n"
        
        prompt += f"用户问题: {user_input}\n\n请回答:"
        
        return prompt
    
    def _build_prompt(self, user_input: str, relevant_memories: List[str]) -> str:
        """构建提示"""
        prompt = "你是一个有帮助的助手。请根据以下信息回答用户的问题。\n\n"
        
        if relevant_memories:
            prompt += "相关历史记忆:\n"
            for i, memory in enumerate(relevant_memories, 1):
                prompt += f"{i}. {memory}\n"
            prompt += "\n"
        
        prompt += f"用户问题: {user_input}\n\n请回答:"
        
        return prompt

class StoreMemoryNode(Node):
    """存储记忆节点"""
    
    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.name = "store_memory"
        self.memory_manager = memory_manager
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        session_id = context.get("session_id")
        user_input = context.get("user_input", "")
        assistant_response = context.get("assistant_response", "")
        
        if session_id and user_input and assistant_response:
            # 将对话添加到长期记忆
            self.memory_manager.add_conversation_to_memory(
                session_id, user_input, assistant_response
            )
        
        return context

class DisplayResponseNode(Node):
    """显示响应节点"""
    
    def __init__(self):
        super().__init__()
        self.name = "display_response"
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        assistant_response = context.get("assistant_response", "")
        print(f"\n助手: {assistant_response}\n")
        return context

class CheckContinueNode(Node):
    """检查是否继续节点"""
    
    def __init__(self):
        super().__init__()
        self.name = "check_continue"
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        continue_chat = input("是否继续对话? (y/n): ").lower()
        context["continue_chat"] = continue_chat == 'y'
        return context

class MemoryChatFlow:
    """记忆聊天流程"""
    
    def __init__(self):
        # 初始化记忆管理组件
        self.session_service = SessionService()
        self.memory_service = MemoryService()
        self.memory_manager = MemoryManager(self.session_service, self.memory_service)
        
        # 创建节点
        self.get_user_input_node = GetUserInputNode()
        self.retrieve_memories_node = RetrieveMemoriesNode(self.memory_manager)
        self.generate_response_node = GenerateResponseNode(self.memory_manager)
        self.store_memory_node = StoreMemoryNode(self.memory_manager)
        self.display_response_node = DisplayResponseNode()
        self.check_continue_node = CheckContinueNode()
        
        # 创建流程并连接节点
        self.flow = Flow("memory_chat_flow")
        
        # 使用PocketFlow的连接方式
        self.get_user_input_node >> self.retrieve_memories_node
        self.retrieve_memories_node >> self.generate_response_node
        self.generate_response_node >> self.store_memory_node
        self.store_memory_node >> self.display_response_node
        self.display_response_node >> self.check_continue_node
        
        # 设置流程的起始节点
        self.flow.start(self.get_user_input_node)
    
    def start_chat(self, app_name: str = "memory_chat", user_id: str = "default_user"):
        """开始聊天"""
        print("=== 记忆聊天助手 ===")
        print("这个助手会记住你们的对话历史，并利用这些信息提供更好的回答。")
        
        # 尝试获取用户最近的会话，如果没有则创建新会话
        user_sessions = self.session_service.get_user_sessions(app_name, user_id)
        if user_sessions:
            # 选择最近更新的会话
            session = max(user_sessions, key=lambda s: s.last_update_time)
        else:
            session = self.session_service.create_session(app_name, user_id)
        
        session_id = session.id
        
        print(f"会话ID: {session_id}")
        print("输入 'exit' 退出对话。\n")
        
        # 初始化上下文
        context = {
            "session_id": session_id,
            "app_name": app_name,
            "user_id": user_id
        }
        
        # 运行流程
        try:
            while True:
                # 获取用户输入
                user_input = input("请输入您的问题: ")
                if user_input.lower() == 'exit':
                    break
                
                context["user_input"] = user_input
                context["timestamp"] = time.time()
                
                # 手动执行流程中的节点
                # 1. 检索相关记忆
                context = self.retrieve_memories_node.execute(context)
                
                # 2. 生成响应
                context = self.generate_response_node.execute(context)
                
                # 3. 存储记忆
                context = self.store_memory_node.execute(context)
                
                # 4. 显示响应
                context = self.display_response_node.execute(context)
                
                # 检查是否继续
                continue_chat = input("是否继续对话? (y/n): ").lower()
                if continue_chat != 'y':
                    break
            
            print("\n对话结束。感谢使用记忆聊天助手！")
            
            # 显示会话统计
            self._show_session_stats(session_id)
            
        except KeyboardInterrupt:
            print("\n\n对话被中断。")
        except Exception as e:
            print(f"\n发生错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_session_stats(self, session_id: str):
        """显示会话统计"""
        session = self.session_service.get_session("", "", session_id)
        if not session:
            return
        
        print("\n=== 会话统计 ===")
        print(f"消息数量: {len(session.messages)}")
        print(f"会话时长: {time.time() - session.created_at:.2f} 秒")
        
        # 显示用户状态
        user_state = StateManager.filter_state_by_prefix(session.state, StateManager.USER_PREFIX)
        if user_state:
            print(f"用户状态: {user_state}")
        
        # 显示相关记忆数量
        user_memories = self.memory_service.get_memories_by_metadata({"user_id": session.user_id})
        print(f"长期记忆数量: {len(user_memories)}")

# 主函数
def main():
    """主函数"""
    chat_flow = MemoryChatFlow()
    chat_flow.start_chat()

if __name__ == "__main__":
    main()