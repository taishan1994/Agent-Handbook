"""
长期记忆管理模块
基于向量数据库的持久记忆实现
"""
import json
import time
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# 导入utils中的函数
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils import get_embedding

@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: float
    last_accessed: float
    access_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """从字典创建记忆项"""
        return cls(**data)

class VectorStore:
    """向量存储，用于长期记忆"""
    
    def __init__(self, dimension: int = 2560):  # 修改为与实际嵌入向量维度匹配
        self.dimension = dimension
        self.vectors: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def add_vector(self, vector_id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """添加向量"""
        if len(vector) != self.dimension:
            print(f"[DEBUG] 向量维度不匹配: 期望 {self.dimension}, 实际 {len(vector)}")
            return False
        
        self.vectors[vector_id] = vector
        self.metadata[vector_id] = metadata or {}
        print(f"[DEBUG] 向量已添加: {vector_id}, 总向量数: {len(self.vectors)}")
        return True
    
    def get_vector(self, vector_id: str) -> Optional[np.ndarray]:
        """获取向量"""
        return self.vectors.get(vector_id)
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """搜索最相似的向量"""
        if len(query_vector) != self.dimension:
            return []
        
        similarities = []
        for vector_id, vector in self.vectors.items():
            # 计算余弦相似度
            similarity = np.dot(query_vector, vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(vector)
            )
            similarities.append((vector_id, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def delete_vector(self, vector_id: str) -> bool:
        """删除向量"""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
            del self.metadata[vector_id]
            return True
        return False
    
    def update_vector(self, vector_id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新向量"""
        if len(vector) != self.dimension or vector_id not in self.vectors:
            return False
        
        self.vectors[vector_id] = vector
        if metadata is not None:
            self.metadata[vector_id].update(metadata)
        return True

class MemoryService:
    """记忆服务，管理长期记忆"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
        self.memory_items: Dict[str, MemoryItem] = {}
    
    def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None, 
                  memory_id: Optional[str] = None) -> str:
        """添加记忆"""
        if memory_id is None:
            memory_id = f"memory_{int(time.time())}_{len(self.memory_items)}"
        
        print(f"[DEBUG] 添加记忆: {memory_id}, 内容: {content[:50]}...")
        
        # 获取内容的嵌入向量
        embedding = get_embedding(content)
        print(f"[DEBUG] 嵌入向量维度: {len(embedding)}")
        
        # 创建记忆项
        current_time = time.time()
        memory_item = MemoryItem(
            id=memory_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            created_at=current_time,
            last_accessed=current_time,
            access_count=0
        )
        
        # 添加到存储
        self.memory_items[memory_id] = memory_item
        vector_added = self.vector_store.add_vector(memory_id, np.array(embedding), metadata)
        print(f"[DEBUG] 向量添加结果: {vector_added}")
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """获取记忆"""
        if memory_id in self.memory_items:
            # 更新访问信息
            memory_item = self.memory_items[memory_id]
            memory_item.last_accessed = time.time()
            memory_item.access_count += 1
            return memory_item
        return None
    
    def search_memories(self, query: str, top_k: int = 5, 
                       metadata_filter: Optional[Dict[str, Any]] = None) -> List[Tuple[MemoryItem, float]]:
        """搜索记忆"""
        # 获取查询的嵌入向量
        query_embedding = np.array(get_embedding(query))
        
        # 在向量存储中搜索
        search_results = self.vector_store.search(query_embedding, top_k * 2)  # 获取更多结果以便过滤
        
        print(f"[DEBUG] 向量搜索结果数量: {len(search_results)}")
        
        # 过滤并格式化结果
        filtered_results = []
        for memory_id, similarity in search_results:
            memory_item = self.memory_items.get(memory_id)
            if memory_item is None:
                continue
                
            print(f"[DEBUG] 检查记忆项 {memory_id}:")
            print(f"[DEBUG] 记忆元数据: {memory_item.metadata}")
            print(f"[DEBUG] 过滤器: {metadata_filter}")
                
            # 应用元数据过滤
            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    if key not in memory_item.metadata or memory_item.metadata[key] != value:
                        print(f"[DEBUG] 过滤失败 - {key}: {memory_item.metadata.get(key)} != {value}")
                        match = False
                        break
                
                if match:
                    print(f"[DEBUG] 过滤成功")
                else:
                    continue
            else:
                print(f"[DEBUG] 无过滤器，直接通过")
            
            filtered_results.append((memory_item, similarity))
            
            # 限制结果数量
            if len(filtered_results) >= top_k:
                break
        
        return filtered_results
    
    def update_memory(self, memory_id: str, content: Optional[str] = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新记忆"""
        if memory_id not in self.memory_items:
            return False
        
        memory_item = self.memory_items[memory_id]
        
        # 更新内容和嵌入向量
        if content is not None:
            memory_item.content = content
            embedding = get_embedding(content)
            memory_item.embedding = embedding
            self.vector_store.update_vector(memory_id, np.array(embedding))
        
        # 更新元数据
        if metadata is not None:
            memory_item.metadata.update(metadata)
            self.vector_store.update_vector(memory_id, 
                                          self.vector_store.get_vector(memory_id), 
                                          metadata)
        
        return True
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self.memory_items:
            del self.memory_items[memory_id]
            self.vector_store.delete_vector(memory_id)
            return True
        return False
    
    def get_memories_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[MemoryItem]:
        """根据元数据获取记忆"""
        filtered_memories = []
        for memory_item in self.memory_items.values():
            match = True
            for key, value in metadata_filter.items():
                if key not in memory_item.metadata or memory_item.metadata[key] != value:
                    match = False
                    break
            if match:
                filtered_memories.append(memory_item)
        return filtered_memories
    
    def get_recent_memories(self, count: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        sorted_memories = sorted(
            self.memory_items.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return sorted_memories[:count]
    
    def get_frequently_accessed_memories(self, count: int = 10) -> List[MemoryItem]:
        """获取经常访问的记忆"""
        sorted_memories = sorted(
            self.memory_items.values(),
            key=lambda x: x.access_count,
            reverse=True
        )
        return sorted_memories[:count]

class MemoryManager:
    """记忆管理器，整合短期和长期记忆"""
    
    def __init__(self, session_service, memory_service: Optional[MemoryService] = None):
        self.session_service = session_service
        self.memory_service = memory_service or MemoryService()
    
    def add_conversation_to_memory(self, session_id: str, user_message: str, 
                                 assistant_message: str, metadata: Optional[Dict[str, Any]] = None):
        """将对话添加到长期记忆"""
        # 从session_id中提取app_name和user_id
        # 假设session_id格式为: app_name_user_id_timestamp
        # 例如: memory_chat_default_user_1763023572
        parts = session_id.split('_')
        if len(parts) < 4:
            print(f"[DEBUG] session_id格式不正确: {session_id}, parts: {parts}")
            return
        
        # 第一个部分是app_name的一部分，第二个部分是app_name的另一部分
        app_name = f"{parts[0]}_{parts[1]}"  # 例如: memory_chat
        user_id = parts[2]  # 例如: default_user
        
        print(f"[DEBUG] 添加记忆 - session_id: {session_id}, app_name: {app_name}, user_id: {user_id}")
        
        # 获取会话信息
        session = self.session_service.get_session(app_name, user_id, session_id)
        if not session:
            print("[DEBUG] 会话不存在")
            return
        
        # 创建对话内容
        conversation = f"用户: {user_message}\n助手: {assistant_message}"
        
        # 创建元数据
        conversation_metadata = {
            "session_id": session_id,
            "app_name": session.app_name,
            "user_id": session.user_id,
            "type": "conversation",
            **(metadata or {})
        }
        
        # 添加到长期记忆
        self.memory_service.add_memory(conversation, conversation_metadata)
        print(f"[DEBUG] 记忆已添加: {conversation[:50]}...")
    
    def search_relevant_memories(self, session_id: str, query: str, top_k: int = 3) -> List[str]:
        """搜索相关记忆"""
        # 从session_id中提取app_name和user_id
        # 假设session_id格式为: app_name_user_id_timestamp
        # 例如: memory_chat_default_user_1763023572
        parts = session_id.split('_')
        if len(parts) < 4:
            print(f"[DEBUG] session_id格式不正确: {session_id}, parts: {parts}")
            return []
        
        # 第一个部分是app_name的一部分，第二个部分是app_name的另一部分
        app_name = f"{parts[0]}_{parts[1]}"  # 例如: memory_chat
        user_id = parts[2]  # 例如: default_user
        
        print(f"[DEBUG] 搜索记忆 - session_id: {session_id}, app_name: {app_name}, user_id: {user_id}")
        
        # 获取会话信息
        session = self.session_service.get_session(app_name, user_id, session_id)
        if not session:
            print("[DEBUG] 会话不存在")
            return []
        
        # 创建元数据过滤器
        metadata_filter = {
            "user_id": session.user_id,
            "app_name": session.app_name
        }
        
        print(f"[DEBUG] 元数据过滤器: {metadata_filter}")
        print(f"[DEBUG] 总记忆数量: {len(self.memory_service.memory_items)}")
        
        # 搜索记忆
        search_results = self.memory_service.search_memories(query, top_k, metadata_filter)
        
        print(f"[DEBUG] 搜索结果数量: {len(search_results)}")
        for memory_item, similarity in search_results:
            print(f"[DEBUG] 记忆内容: {memory_item.content[:50]}..., 相似度: {similarity:.4f}")
        
        # 提取内容
        return [memory_item.content for memory_item, _ in search_results]
    
    def get_context_with_memories(self, session_id: str, query: str, 
                                 max_memory_items: int = 3) -> List[Dict[str, Any]]:
        """获取包含相关记忆的上下文"""
        # 获取会话上下文
        context = self.session_service.get_context_window(session_id)
        
        # 搜索相关记忆
        relevant_memories = self.search_relevant_memories(session_id, query, max_memory_items)
        
        # 将记忆添加到上下文
        if relevant_memories:
            memory_context = {
                "role": "system",
                "content": "相关历史记忆:\n" + "\n".join(relevant_memories),
                "timestamp": time.time(),
                "metadata": {"type": "memory_context"}
            }
            context.insert(0, memory_context)
        
        return context

# 示例使用
if __name__ == "__main__":
    # 创建向量存储和记忆服务
    vector_store = VectorStore()
    memory_service = MemoryService(vector_store)
    
    # 添加一些记忆
    memory_id1 = memory_service.add_memory(
        "用户询问了关于机器学习的问题，我解释了监督学习和无监督学习的区别。",
        {"topic": "机器学习", "user_id": "user123", "type": "conversation"}
    )
    
    memory_id2 = memory_service.add_memory(
        "用户询问了关于深度学习的问题，我解释了神经网络的基本原理。",
        {"topic": "深度学习", "user_id": "user123", "type": "conversation"}
    )
    
    memory_id3 = memory_service.add_memory(
        "用户询问了关于自然语言处理的问题，我介绍了NLP的主要应用领域。",
        {"topic": "自然语言处理", "user_id": "user123", "type": "conversation"}
    )
    
    # 搜索记忆
    search_results = memory_service.search_memories("神经网络", top_k=2)
    print(f"搜索结果数量: {len(search_results)}")
    for memory_item, similarity in search_results:
        print(f"内容: {memory_item.content[:50]}...")
        print(f"相似度: {similarity:.4f}")
        print(f"元数据: {memory_item.metadata}")
        print("---")
    
    # 获取最近的记忆
    recent_memories = memory_service.get_recent_memories(2)
    print(f"\n最近的记忆数量: {len(recent_memories)}")
    for memory in recent_memories:
        print(f"内容: {memory.content[:50]}...")
        print(f"创建时间: {time.ctime(memory.created_at)}")
        print("---")