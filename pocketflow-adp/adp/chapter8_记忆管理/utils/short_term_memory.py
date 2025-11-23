"""
短期记忆管理模块
基于会话的上下文记忆实现
"""
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class Session:
    """会话数据结构"""
    id: str
    app_name: str
    user_id: str
    messages: List[Dict[str, Any]]
    state: Dict[str, Any]
    created_at: float
    last_update_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建会话"""
        return cls(**data)

class SessionService:
    """会话服务，管理短期记忆"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    def create_session(self, app_name: str, user_id: str, session_id: Optional[str] = None, 
                      state: Optional[Dict[str, Any]] = None) -> Session:
        """创建新会话"""
        if session_id is None:
            session_id = f"{app_name}_{user_id}_{int(time.time())}"
        
        current_time = time.time()
        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            messages=[],
            state=state or {},
            created_at=current_time,
            last_update_time=current_time
        )
        
        self.sessions[session_id] = session
        return session
    
    def get_session(self, app_name: str, user_id: str, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, app_name: str, user_id: str) -> List[Session]:
        """获取用户的所有会话"""
        return [
            session for session in self.sessions.values()
            if session.app_name == app_name and session.user_id == user_id
        ]
    
    def update_session_state(self, session_id: str, state_delta: Dict[str, Any]) -> bool:
        """更新会话状态"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.state.update(state_delta)
        session.last_update_time = time.time()
        return True
    
    def add_message(self, session_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """向会话添加消息"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        session.messages.append(message)
        session.last_update_time = time.time()
        return True
    
    def delete_session(self, app_name: str, user_id: str, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.app_name == app_name and session.user_id == user_id:
                del self.sessions[session_id]
                return True
        return False
    
    def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的消息"""
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        return session.messages[-count:] if len(session.messages) > count else session.messages
    
    def get_context_window(self, session_id: str, max_tokens: int = 4000) -> List[Dict[str, Any]]:
        """获取适合上下文窗口的消息"""
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        # 简单实现：从最新消息开始，估算token数量
        # 实际应用中应该使用更精确的token计算方法
        messages = []
        current_tokens = 0
        
        for message in reversed(session.messages):
            # 粗略估算：1个token约等于4个字符
            message_tokens = len(message["content"]) // 4
            
            if current_tokens + message_tokens > max_tokens:
                break
                
            messages.insert(0, message)
            current_tokens += message_tokens
        
        return messages

class StateManager:
    """状态管理器，处理会话状态的前缀和范围"""
    
    # 状态前缀定义
    USER_PREFIX = "user:"
    APP_PREFIX = "app:"
    TEMP_PREFIX = "temp:"
    
    @staticmethod
    def get_user_state_key(key: str) -> str:
        """获取用户状态键"""
        return f"{StateManager.USER_PREFIX}{key}"
    
    @staticmethod
    def get_app_state_key(key: str) -> str:
        """获取应用状态键"""
        return f"{StateManager.APP_PREFIX}{key}"
    
    @staticmethod
    def get_temp_state_key(key: str) -> str:
        """获取临时状态键"""
        return f"{StateManager.TEMP_PREFIX}{key}"
    
    @staticmethod
    def filter_state_by_prefix(state: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        """根据前缀过滤状态"""
        return {
            key[len(prefix):]: value
            for key, value in state.items()
            if key.startswith(prefix)
        }
    
    @staticmethod
    def merge_state_updates(current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """合并状态更新"""
        new_state = current_state.copy()
        new_state.update(updates)
        return new_state

# 示例使用
if __name__ == "__main__":
    # 创建会话服务
    session_service = SessionService()
    
    # 创建新会话
    session = session_service.create_session(
        app_name="chatbot",
        user_id="user123",
        session_id="session1"
    )
    
    # 添加消息
    session_service.add_message(session.id, "user", "你好，我想了解一下人工智能")
    session_service.add_message(session.id, "assistant", "你好！人工智能是一个广泛的领域...")
    session_service.add_message(session.id, "user", "能详细解释一下机器学习吗？")
    
    # 更新状态
    session_service.update_session_state(session.id, {
        StateManager.get_user_state_key("language"): "zh-CN",
        StateManager.get_user_state_key("interests"): ["AI", "ML"],
        StateManager.get_temp_state_key("current_topic"): "machine_learning"
    })
    
    # 获取会话信息
    updated_session = session_service.get_session("chatbot", "user123", "session1")
    print(f"会话ID: {updated_session.id}")
    print(f"消息数量: {len(updated_session.messages)}")
    print(f"状态: {updated_session.state}")
    
    # 获取上下文窗口
    context = session_service.get_context_window(session.id)
    print(f"上下文消息数量: {len(context)}")