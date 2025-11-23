"""
AgentCard类定义

本文件包含AgentCard、AgentSkill和AgentCapabilities类，用于描述Agent的能力和通信端点。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import sys
import os

# 添加父目录到系统路径，以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class AgentSkill:
    """
    Agent技能类
    
    描述Agent能够执行的特定技能或任务。
    """
    id: str
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            AgentSkill的字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "examples": self.examples
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentSkill':
        """
        从字典创建AgentSkill
        
        Args:
            data: 字典数据
            
        Returns:
            AgentSkill实例
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            examples=data.get("examples", [])
        )


@dataclass
class AgentCapabilities:
    """
    Agent能力类
    
    描述Agent的能力，如流式处理、音频输入/输出等。
    """
    streaming: bool = False
    audio_input: bool = False
    audio_output: bool = False
    video_input: bool = False
    video_output: bool = False
    attachment_upload: bool = False
    attachment_download: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            AgentCapabilities的字典表示
        """
        return {
            "streaming": self.streaming,
            "audio_input": self.audio_input,
            "audio_output": self.audio_output,
            "video_input": self.video_input,
            "video_output": self.video_output,
            "attachment_upload": self.attachment_upload,
            "attachment_download": self.attachment_download
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCapabilities':
        """
        从字典创建AgentCapabilities
        
        Args:
            data: 字典数据
            
        Returns:
            AgentCapabilities实例
        """
        return cls(
            streaming=data.get("streaming", False),
            audio_input=data.get("audio_input", False),
            audio_output=data.get("audio_output", False),
            video_input=data.get("video_input", False),
            video_output=data.get("video_output", False),
            attachment_upload=data.get("attachment_upload", False),
            attachment_download=data.get("attachment_download", False)
        )
    
    def has_capability(self, capability: str) -> bool:
        """
        检查是否具有指定能力
        
        Args:
            capability: 能力名称
            
        Returns:
            是否具有该能力
        """
        return getattr(self, capability, False)


@dataclass
class CommunicationEndpoint:
    """
    通信端点类
    
    描述Agent的通信端点信息。
    """
    host: str
    port: int
    protocol: str = "http"
    path: str = "/a2a"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            CommunicationEndpoint的字典表示
        """
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "path": self.path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunicationEndpoint':
        """
        从字典创建CommunicationEndpoint
        
        Args:
            data: 字典数据
            
        Returns:
            CommunicationEndpoint实例
        """
        return cls(
            host=data.get("host", "localhost"),
            port=data.get("port", 8000),
            protocol=data.get("protocol", "http"),
            path=data.get("path", "/a2a")
        )


@dataclass
class CommunicationInfo:
    """
    通信信息类
    
    描述Agent的通信相关信息。
    """
    endpoints: List[CommunicationEndpoint] = field(default_factory=list)
    supported_protocols: List[str] = field(default_factory=lambda: ["http", "websocket"])
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            CommunicationInfo的字典表示
        """
        return {
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
            "supported_protocols": self.supported_protocols
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunicationInfo':
        """
        从字典创建CommunicationInfo
        
        Args:
            data: 字典数据
            
        Returns:
            CommunicationInfo实例
        """
        endpoints = [CommunicationEndpoint.from_dict(endpoint_data) 
                    for endpoint_data in data.get("endpoints", [])]
        
        return cls(
            endpoints=endpoints,
            supported_protocols=data.get("supported_protocols", ["http", "websocket"])
        )


@dataclass
class AgentCard:
    """
    AgentCard类
    
    描述Agent的能力、技能和通信端点，作为Agent的数字身份文件。
    """
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    skills: List[AgentSkill] = field(default_factory=list)
    communication: CommunicationInfo = field(default_factory=CommunicationInfo)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            AgentCard的字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities.to_dict(),
            "skills": [skill.to_dict() for skill in self.skills],
            "communication": self.communication.to_dict(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCard':
        """
        从字典创建AgentCard
        
        Args:
            data: 字典数据
            
        Returns:
            AgentCard实例
        """
        capabilities = AgentCapabilities.from_dict(data.get("capabilities", {}))
        skills = [AgentSkill.from_dict(skill_data) for skill_data in data.get("skills", [])]
        communication = CommunicationInfo.from_dict(data.get("communication", {}))
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            capabilities=capabilities,
            skills=skills,
            communication=communication,
            metadata=data.get("metadata", {})
        )
    
    def add_skill(self, skill: AgentSkill):
        """
        添加技能
        
        Args:
            skill: 要添加的技能
        """
        # 检查技能是否已存在
        for existing_skill in self.skills:
            if existing_skill.id == skill.id:
                # 更新现有技能
                existing_skill.name = skill.name
                existing_skill.description = skill.description
                existing_skill.tags = skill.tags
                existing_skill.examples = skill.examples
                return
        
        # 添加新技能
        self.skills.append(skill)
    
    def remove_skill(self, skill_id: str):
        """
        移除技能
        
        Args:
            skill_id: 要移除的技能ID
        """
        self.skills = [skill for skill in self.skills if skill.id != skill_id]
    
    def has_skill(self, skill_id: str) -> bool:
        """
        检查是否具有指定技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            是否具有该技能
        """
        return any(skill.id == skill_id for skill in self.skills)
    
    def has_tag(self, tag: str) -> bool:
        """
        检查是否具有指定标签
        
        Args:
            tag: 标签名称
            
        Returns:
            是否具有该标签
        """
        return any(tag in skill.tags for skill in self.skills)
    
    def has_capability(self, capability: str) -> bool:
        """
        检查是否具有指定能力
        
        Args:
            capability: 能力名称
            
        Returns:
            是否具有该能力
        """
        return self.capabilities.has_capability(capability)
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            AgentCard的字符串表示
        """
        return f"AgentCard(id={self.id}, name={self.name}, version={self.version})"