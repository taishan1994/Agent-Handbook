"""
示例Agent实现

本文件包含几个示例Agent，演示如何使用A2A协议实现Agent间通信。
"""

import asyncio
from typing import Dict, Any, List
import sys
import os

# 添加父目录到系统路径，以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adp.chapter15_agent_communication.agent_card import AgentCard, AgentSkill, AgentCapabilities
from adp.chapter15_agent_communication.a2a_flow import A2AFlow
from adp.chapter15_agent_communication.agent_registry import AgentRegistry


class WeatherAgent:
    """天气Agent，可以查询天气信息"""
    
    def __init__(self, url: str = "http://localhost:8001"):
        # 创建Agent技能
        weather_skill = AgentSkill(
            id="get_weather",
            name="获取天气",
            description="获取指定地点的天气信息",
            tags=["weather", "query"],
            examples=["北京今天天气怎么样？", "上海明天会下雨吗？"]
        )
        
        # 创建Agent能力
        capabilities = AgentCapabilities(streaming=True)
        
        # 创建AgentCard
        self.agent_card = AgentCard(
            id="weather-bot-001",
            name="WeatherBot",
            description="一个可以查询天气信息的Agent",
            version="1.0.0",
            capabilities=capabilities,
            skills=[weather_skill]
        )
        
        # 创建A2A流程
        self.a2a_flow = A2AFlow(self.agent_card)
    
    async def handle_weather_query(
        self,
        task_id: str,
        session_id: str,
        message: Dict[str, Any],
        agent_card: AgentCard,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理天气查询
        
        Args:
            task_id: 任务ID
            session_id: 会话ID
            message: 消息内容
            agent_card: AgentCard
            context: 执行上下文
            
        Returns:
            任务结果
        """
        # 提取消息文本
        text_parts = [
            part.get("text", "")
            for part in message.get("parts", [])
            if part.get("type") == "text"
        ]
        message_text = " ".join(text_parts)
        
        # 在实际实现中，这里应该调用天气API
        # 为了演示，我们生成一个简单的响应
        if "北京" in message_text:
            weather_info = "北京今天天气晴朗，温度25°C，微风，适合外出。"
        elif "上海" in message_text:
            weather_info = "上海今天多云，温度22°C，可能有阵雨，记得带伞。"
        elif "广州" in message_text:
            weather_info = "广州今天阴天，温度28°C，湿度较高，体感闷热。"
        else:
            weather_info = f"抱歉，我无法获取{message_text}的天气信息。请尝试查询北京、上海或广州的天气。"
        
        return {
            "task": {
                "id": task_id,
                "status": {
                    "state": "completed",
                    "timestamp": "2025-06-20T10:00:00Z"
                },
                "artifacts": [
                    {
                        "name": "weather_info",
                        "type": "text/plain",
                        "data": weather_info
                    }
                ]
            }
        }


class NewsAgent:
    """新闻Agent，可以获取新闻信息"""
    
    def __init__(self, url: str = "http://localhost:8002"):
        # 创建Agent技能
        news_skill = AgentSkill(
            id="get_news",
            name="获取新闻",
            description="获取最新的新闻信息",
            tags=["news", "query"],
            examples=["今天有什么新闻？", "最新的科技新闻是什么？"]
        )
        
        # 创建Agent能力
        capabilities = AgentCapabilities(streaming=True)
        
        # 创建AgentCard
        self.agent_card = AgentCard(
            id="news-bot-001",
            name="NewsBot",
            description="一个可以获取新闻信息的Agent",
            version="1.0.0",
            capabilities=capabilities,
            skills=[news_skill]
        )
        
        # 创建A2A流程
        self.a2a_flow = A2AFlow(self.agent_card)
    
    async def handle_news_query(
        self,
        task_id: str,
        session_id: str,
        message: Dict[str, Any],
        agent_card: AgentCard,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理新闻查询
        
        Args:
            task_id: 任务ID
            session_id: 会话ID
            message: 消息内容
            agent_card: AgentCard
            context: 执行上下文
            
        Returns:
            任务结果
        """
        # 提取消息文本
        text_parts = [
            part.get("text", "")
            for part in message.get("parts", [])
            if part.get("type") == "text"
        ]
        message_text = " ".join(text_parts)
        
        # 在实际实现中，这里应该调用新闻API
        # 为了演示，我们生成一个简单的响应
        if "科技" in message_text:
            news_info = "最新科技新闻：人工智能技术在医疗领域取得重大突破，新型AI系统能够更准确地诊断疾病。"
        elif "体育" in message_text:
            news_info = "最新体育新闻：中国女排在世界杯比赛中以3:0战胜对手，成功晋级seminal比赛。"
        elif "财经" in message_text:
            news_info = "最新财经新闻：全球股市今日普遍上涨，科技股领涨，投资者对经济复苏前景持乐观态度。"
        else:
            news_info = "今日要闻：1. 人工智能技术在医疗领域取得重大突破；2. 中国女排世界杯比赛晋级；3. 全球股市普遍上涨。"
        
        return {
            "task": {
                "id": task_id,
                "status": {
                    "state": "completed",
                    "timestamp": "2025-06-20T10:00:00Z"
                },
                "artifacts": [
                    {
                        "name": "news_info",
                        "type": "text/plain",
                        "data": news_info
                    }
                ]
            }
        }


class TranslationAgent:
    """翻译Agent，可以翻译文本"""
    
    def __init__(self, url: str = "http://localhost:8003"):
        # 创建Agent技能
        translation_skill = AgentSkill(
            id="translate_text",
            name="翻译文本",
            description="将文本从一种语言翻译到另一种语言",
            tags=["translation", "text"],
            examples=["将'Hello'翻译成中文", "把'你好'翻译成英文"]
        )
        
        # 创建Agent能力
        capabilities = AgentCapabilities(streaming=False)
        
        # 创建AgentCard
        self.agent_card = AgentCard(
            id="translation-bot-001",
            name="TranslationBot",
            description="一个可以翻译文本的Agent",
            version="1.0.0",
            capabilities=capabilities,
            skills=[translation_skill]
        )
        
        # 创建A2A流程
        self.a2a_flow = A2AFlow(self.agent_card)
    
    async def handle_translation_query(
        self,
        task_id: str,
        session_id: str,
        message: Dict[str, Any],
        agent_card: AgentCard,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理翻译查询
        
        Args:
            task_id: 任务ID
            session_id: 会话ID
            message: 消息内容
            agent_card: AgentCard
            context: 执行上下文
            
        Returns:
            任务结果
        """
        # 提取消息文本
        text_parts = [
            part.get("text", "")
            for part in message.get("parts", [])
            if part.get("type") == "text"
        ]
        message_text = " ".join(text_parts)
        
        # 在实际实现中，这里应该调用翻译API
        # 为了演示，我们生成一个简单的响应
        if "Hello" in message_text and "中文" in message_text:
            translation_result = "Hello 的中文翻译是：你好"
        elif "你好" in message_text and "英文" in message_text:
            translation_result = "你好的英文翻译是：Hello"
        elif "Thank you" in message_text and "中文" in message_text:
            translation_result = "Thank you 的中文翻译是：谢谢"
        elif "谢谢" in message_text and "英文" in message_text:
            translation_result = "谢谢的英文翻译是：Thank you"
        else:
            translation_result = f"抱歉，我无法翻译'{message_text}'。请尝试翻译简单的常用语，如'Hello'或'你好'。"
        
        return {
            "task": {
                "id": task_id,
                "status": {
                    "state": "completed",
                    "timestamp": "2025-06-20T10:00:00Z"
                },
                "artifacts": [
                    {
                        "name": "translation_result",
                        "type": "text/plain",
                        "data": translation_result
                    }
                ]
            }
        }


class CoordinatorAgent:
    """协调Agent，可以协调其他Agent完成任务"""
    
    def __init__(self, url: str = "http://localhost:8000"):
        # 创建Agent技能
        coordination_skill = AgentSkill(
            id="coordinate_agents",
            name="协调Agent",
            description="协调其他Agent共同完成任务",
            tags=["coordination", "management"],
            examples=["帮我查询北京天气和最新新闻", "翻译'Hello'并查询上海天气"]
        )
        
        # 创建Agent能力
        capabilities = AgentCapabilities(streaming=True)
        
        # 创建AgentCard
        self.agent_card = AgentCard(
            id="coordinator-bot-001",
            name="CoordinatorBot",
            description="一个可以协调其他Agent共同完成任务的Agent",
            version="1.0.0",
            capabilities=capabilities,
            skills=[coordination_skill]
        )
        
        # 创建A2A流程
        self.a2a_flow = A2AFlow(self.agent_card)
    
    async def handle_coordination_query(
        self,
        task_id: str,
        session_id: str,
        message: Dict[str, Any],
        agent_card: AgentCard,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理协调整询
        
        Args:
            task_id: 任务ID
            session_id: 会话ID
            message: 消息内容
            agent_card: AgentCard
            context: 执行上下文
            
        Returns:
            任务结果
        """
        # 提取消息文本
        text_parts = [
            part.get("text", "")
            for part in message.get("parts", [])
            if part.get("type") == "text"
        ]
        message_text = " ".join(text_parts)
        
        # 分析消息，确定需要调用哪些Agent
        agents_to_call = []
        if "天气" in message_text:
            agents_to_call.append("WeatherBot")
        if "新闻" in message_text:
            agents_to_call.append("NewsBot")
        if "翻译" in message_text:
            agents_to_call.append("TranslationBot")
        
        # 如果没有指定任何Agent，返回提示
        if not agents_to_call:
            return {
                "task": {
                    "id": task_id,
                    "status": {
                        "state": "completed",
                        "timestamp": "2025-06-20T10:00:00Z"
                    },
                    "artifacts": [
                        {
                            "name": "coordination_result",
                            "type": "text/plain",
                            "data": "抱歉，我不确定您需要什么帮助。请尝试查询天气、新闻或翻译。"
                        }
                    ]
                }
            }
        
        # 创建协作流程
        collaboration_flow = self.a2a_flow.create_collaboration_flow(
            agents=agents_to_call,
            initial_message=message,
            max_iterations=1
        )
        
        # 运行协作流程
        result = await collaboration_flow.run()
        
        # 提取结果
        if result.get("status") == "error":
            return {
                "task": {
                    "id": task_id,
                    "status": {
                        "state": "failed",
                        "timestamp": "2025-06-20T10:00:00Z"
                    },
                    "artifacts": [
                        {
                            "name": "coordination_result",
                            "type": "text/plain",
                            "data": f"协调失败: {result.get('error')}"
                        }
                    ]
                }
            }
        
        # 整理协作结果
        conversation_history = result.get("conversation_history", [])
        responses = []
        
        for entry in conversation_history:
            agent_name = entry.get("agent")
            response = entry.get("response")
            responses.append(f"{agent_name}: {response}")
        
        coordination_result = "\n\n".join(responses)
        
        return {
            "task": {
                "id": task_id,
                "status": {
                    "state": "completed",
                    "timestamp": "2025-06-20T10:00:00Z"
                },
                "artifacts": [
                    {
                        "name": "coordination_result",
                        "type": "text/plain",
                        "data": coordination_result
                    }
                ]
            }
        }


# 示例使用函数
async def demo_a2a_communication():
    """演示A2A通信"""
    # 创建Agent注册表
    registry = AgentRegistry()
    
    # 创建并注册Agent
    weather_agent = WeatherAgent()
    news_agent = NewsAgent()
    translation_agent = TranslationAgent()
    coordinator_agent = CoordinatorAgent()
    
    # 注册Agent到注册表
    registry.register_agent(weather_agent.agent_card)
    registry.register_agent(news_agent.agent_card)
    registry.register_agent(translation_agent.agent_card)
    registry.register_agent(coordinator_agent.agent_card)
    
    # 更新所有Agent的A2A流程使用同一个注册表
    weather_agent.a2a_flow.agent_registry = registry
    news_agent.a2a_flow.agent_registry = registry
    translation_agent.a2a_flow.agent_registry = registry
    coordinator_agent.a2a_flow.agent_registry = registry
    
    # 更新所有节点的注册表引用
    weather_agent.a2a_flow.receive_task_node.agent_registry = registry
    news_agent.a2a_flow.receive_task_node.agent_registry = registry
    translation_agent.a2a_flow.receive_task_node.agent_registry = registry
    coordinator_agent.a2a_flow.receive_task_node.agent_registry = registry
    
    # 创建协作Agent的A2A流程
    a2a_flow = coordinator_agent.a2a_flow
    
    # 演示1: 查询天气
    print("演示1: 查询天气")
    weather_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "id": "weather-001",
            "sessionId": "session-001",
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "北京今天天气怎么样？"
                    }
                ]
            },
            "acceptedOutputModes": ["text/plain"],
            "historyLength": 5
        }
    }
    
    weather_response = await weather_agent.a2a_flow.receive_task(
        receiver_id=weather_agent.agent_card.id,
        request=weather_request,
        task_handler=weather_agent.handle_weather_query
    )
    print(f"完整响应: {weather_response}")
    print(f"天气查询结果: {weather_response['response']['result']['task']['artifacts'][0]['data']}")
    
    # 演示2: 查询新闻
    print("\n演示2: 查询新闻")
    news_request = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tasks/send",
        "params": {
            "id": "news-001",
            "sessionId": "session-001",
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "最新的科技新闻是什么？"
                    }
                ]
            },
            "acceptedOutputModes": ["text/plain"],
            "historyLength": 5
        }
    }
    
    news_response = await news_agent.a2a_flow.receive_task(
        receiver_id=news_agent.agent_card.id,
        request=news_request,
        task_handler=news_agent.handle_news_query
    )
    print(f"新闻查询结果: {news_response['response']['result']['task']['artifacts'][0]['data']}")
    
    # 演示3: 翻译文本
    print("\n演示3: 翻译文本")
    translation_request = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tasks/send",
        "params": {
            "id": "translation-001",
            "sessionId": "session-001",
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "将'Hello'翻译成中文"
                    }
                ]
            },
            "acceptedOutputModes": ["text/plain"],
            "historyLength": 5
        }
    }
    
    translation_response = await translation_agent.a2a_flow.receive_task(
        receiver_id=translation_agent.agent_card.id,
        request=translation_request,
        task_handler=translation_agent.handle_translation_query
    )
    print(f"翻译结果: {translation_response['response']['result']['task']['artifacts'][0]['data']}")
    
    # 演示4: 协调多个Agent
    print("\n演示4: 协调多个Agent")
    coordination_request = {
        "jsonrpc": "2.0",
        "id": "4",
        "method": "tasks/send",
        "params": {
            "id": "coordination-001",
            "sessionId": "session-001",
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "帮我查询北京天气和最新科技新闻"
                    }
                ]
            },
            "acceptedOutputModes": ["text/plain"],
            "historyLength": 5
        }
    }
    
    coordination_response = await coordinator_agent.a2a_flow.receive_task(
        receiver_id=coordinator_agent.agent_card.id,
        request=coordination_request,
        task_handler=coordinator_agent.handle_coordination_query
    )
    print(f"协调结果: {coordination_response['response']['result']['task']['artifacts'][0]['data']}")


if __name__ == "__main__":
    asyncio.run(demo_a2a_communication())