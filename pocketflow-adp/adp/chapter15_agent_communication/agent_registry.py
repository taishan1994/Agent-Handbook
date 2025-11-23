"""
Agent注册表实现

本文件包含Agent注册表功能，用于Agent的注册、发现和管理。
"""

import json
import os
from typing import Dict, List, Optional, Any
import sys
import os

# 添加父目录到系统路径，以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adp.chapter15_agent_communication.agent_card import AgentCard
from dataclasses import dataclass, field


@dataclass
class AgentRegistry:
    """
    Agent注册表类，用于存储和管理AgentCard信息
    
    该类实现了Agent的注册、发现和管理功能，是A2A协议中的关键组件。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化Agent注册表
        
        Args:
            storage_path: 存储路径，如果未提供则使用内存存储
        """
        self.storage_path = storage_path
        self._agents: Dict[str, AgentCard] = {}
        
        # 如果提供了存储路径，则从文件加载Agent
        if storage_path and os.path.exists(storage_path):
            self._load_from_file()
    
    def register_agent(self, agent_card: AgentCard) -> bool:
        """
        注册Agent
        
        Args:
            agent_card: 要注册的AgentCard
            
        Returns:
            注册是否成功
        """
        try:
            self._agents[agent_card.name] = agent_card
            
            # 如果提供了存储路径，则保存到文件
            if self.storage_path:
                self._save_to_file()
            
            return True
        except Exception:
            return False
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        注销Agent
        
        Args:
            agent_name: 要注销的Agent名称
            
        Returns:
            注销是否成功
        """
        if agent_name in self._agents:
            del self._agents[agent_name]
            
            # 如果提供了存储路径，则保存到文件
            if self.storage_path:
                self._save_to_file()
            
            return True
        return False
    
    def get_agent(self, agent_name: str) -> Optional[AgentCard]:
        """
        获取Agent
        
        Args:
            agent_name: Agent名称
            
        Returns:
            AgentCard或None
        """
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[AgentCard]:
        """
        列出所有Agent
        
        Returns:
            AgentCard列表
        """
        return list(self._agents.values())
    
    def find_agents_by_skill(self, skill_id: Optional[str] = None, skill_name: Optional[str] = None) -> List[AgentCard]:
        """
        根据技能查找Agent
        
        Args:
            skill_id: 技能ID
            skill_name: 技能名称
            
        Returns:
            匹配的AgentCard列表
        """
        matching_agents = []
        
        for agent_card in self._agents.values():
            for skill in agent_card.skills:
                if (skill_id and skill.id == skill_id) or (skill_name and skill.name == skill_name):
                    matching_agents.append(agent_card)
                    break
        
        return matching_agents
    
    def find_agents_by_tag(self, tag: str) -> List[AgentCard]:
        """
        根据标签查找Agent
        
        Args:
            tag: 标签
            
        Returns:
            匹配的AgentCard列表
        """
        matching_agents = []
        
        for agent_card in self._agents.values():
            for skill in agent_card.skills:
                if tag in skill.tags:
                    matching_agents.append(agent_card)
                    break
        
        return matching_agents
    
    def find_agents_by_capability(self, capability: str) -> List[AgentCard]:
        """
        根据能力查找Agent
        
        Args:
            capability: 能力名称
            
        Returns:
            匹配的AgentCard列表
        """
        matching_agents = []
        
        for agent_card in self._agents.values():
            if agent_card.has_capability(capability):
                matching_agents.append(agent_card)
        
        return matching_agents
    
    def search_agents(self, query) -> List[AgentCard]:
        """
        搜索Agent
        
        Args:
            query: 搜索查询，可以是字符串或字典
            
        Returns:
            匹配的AgentCard列表
        """
        # 处理字典类型的查询
        if isinstance(query, dict):
            # 如果查询是字典，可以扩展这里以支持更复杂的查询条件
            # 目前简单地返回所有Agent
            return list(self._agents.values())
        
        # 处理字符串类型的查询
        query_str = query.lower()
        matching_agents = []
        
        for agent_card in self._agents.values():
            # 检查名称和描述
            if (query_str in agent_card.name.lower() or 
                query_str in agent_card.description.lower()):
                matching_agents.append(agent_card)
                continue
            
            # 检查技能
            for skill in agent_card.skills:
                if (query_str in skill.id.lower() or
                    query_str in skill.name.lower() or 
                    query_str in skill.description.lower() or
                    any(query_str in tag.lower() for tag in skill.tags)):
                    matching_agents.append(agent_card)
                    break
        
        return matching_agents
    
    def _save_to_file(self) -> None:
        """保存Agent到文件"""
        if not self.storage_path:
            return
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # 准备保存的数据
        data = {
            "agents": {
                name: agent_card.to_dict()
                for name, agent_card in self._agents.items()
            }
        }
        
        # 保存到文件
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_from_file(self) -> None:
        """从文件加载Agent"""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        
        try:
            # 从文件加载
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 解析AgentCard
            for name, agent_data in data.get("agents", {}).items():
                agent_card = AgentCard.from_dict(agent_data)
                self._agents[name] = agent_card
        except Exception:
            # 如果加载失败，则忽略并继续使用空注册表
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """将注册表转换为字典"""
        return {
            "agents": {
                name: agent_card.to_dict()
                for name, agent_card in self._agents.items()
            }
        }
    
    def __len__(self) -> int:
        """返回注册的Agent数量"""
        return len(self._agents)
    
    def __contains__(self, agent_name: str) -> bool:
        """检查Agent是否已注册"""
        return agent_name in self._agents