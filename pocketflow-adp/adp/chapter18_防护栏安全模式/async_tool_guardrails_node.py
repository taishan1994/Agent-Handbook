"""
异步工具调用防护栏节点 - 使用PocketFlow实现异步工具调用的安全控制
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel, Field
from pocketflow import AsyncNode
from enum import Enum


class ToolAccessLevel(str, Enum):
    """工具访问级别"""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    RESTRICTED = "restricted"


class ToolCallResult(BaseModel):
    """工具调用结果模型"""
    allowed: bool = Field(description="是否允许调用")
    tool_name: str = Field(description="工具名称")
    parameters: Dict[str, Any] = Field(description="调用参数")
    error_message: Optional[str] = Field(description="错误信息")
    execution_time: float = Field(description="执行时间")
    rate_limit_info: Dict[str, Any] = Field(description="速率限制信息")


class AsyncToolGuardrailsNode(AsyncNode):
    """
    异步工具调用防护栏节点
    
    功能：
    - 工具权限验证
    - 参数验证和清理
    - 调用频率限制
    - 安全审计日志
    - 错误处理和回退
    """
    
    def __init__(self,
                 tool_registry: Optional[Dict[str, Dict[str, Any]]] = None,
                 rate_limits: Optional[Dict[str, Dict[str, Any]]] = None,
                 user_permissions: Optional[Dict[str, List[str]]] = None,
                 enable_logging: bool = True,
                 enable_caching: bool = True):
        """
        初始化工具防护栏节点
        
        Args:
            tool_registry: 工具注册表
            rate_limits: 速率限制配置
            user_permissions: 用户权限配置
            enable_logging: 启用日志记录
            enable_caching: 启用缓存
        """
        super().__init__()
        
        # 默认工具注册表
        self.tool_registry = tool_registry or {
            "web_search": {
                "access_level": ToolAccessLevel.PUBLIC,
                "max_params": 5,
                "required_params": ["query"],
                "description": "网络搜索工具"
            },
            "calculator": {
                "access_level": ToolAccessLevel.PUBLIC,
                "max_params": 3,
                "required_params": ["expression"],
                "description": "计算器工具"
            },
            "file_reader": {
                "access_level": ToolAccessLevel.AUTHENTICATED,
                "max_params": 2,
                "required_params": ["file_path"],
                "description": "文件读取工具"
            },
            "code_executor": {
                "access_level": ToolAccessLevel.ADMIN,
                "max_params": 3,
                "required_params": ["code"],
                "description": "代码执行工具"
            },
            "database_query": {
                "access_level": ToolAccessLevel.RESTRICTED,
                "max_params": 4,
                "required_params": ["query"],
                "description": "数据库查询工具"
            }
        }
        
        # 默认速率限制配置
        self.rate_limits = rate_limits or {
            "web_search": {"requests_per_minute": 60, "requests_per_hour": 1000},
            "calculator": {"requests_per_minute": 120, "requests_per_hour": 2000},
            "file_reader": {"requests_per_minute": 30, "requests_per_hour": 500},
            "code_executor": {"requests_per_minute": 10, "requests_per_hour": 100},
            "database_query": {"requests_per_minute": 20, "requests_per_hour": 300}
        }
        
        # 默认用户权限
        self.user_permissions = user_permissions or {
            "anonymous": ["web_search", "calculator"],
            "user": ["web_search", "calculator", "file_reader"],
            "admin": ["web_search", "calculator", "file_reader", "code_executor", "database_query"]
        }
        
        self.enable_logging = enable_logging
        self.enable_caching = enable_caching
        
        # 调用记录（用于速率限制）
        self.call_history = {}
        
        # 缓存（用于避免重复调用）
        self.cache = {}
    
    async def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理：准备工具调用数据
        
        Args:
            shared: 共享数据字典
            
        Returns:
            处理后的数据
        """
        # 获取工具调用信息
        tool_call = shared.get("tool_call", {})
        user_info = shared.get("user_info", {})
        context = shared.get("context", {})
        
        return {
            "tool_call": tool_call,
            "user_info": user_info,
            "context": context,
            "original_shared": shared
        }
    
    async def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行：验证和执行工具调用
        
        Args:
            prep_res: 预处理结果
            
        Returns:
            工具调用结果
        """
        tool_call = prep_res.get("tool_call", {})
        user_info = prep_res.get("user_info", {})
        context = prep_res.get("context", {})
        
        if not tool_call:
            return {
                "tool_result": ToolCallResult(
                    allowed=False,
                    tool_name="",
                    parameters={},
                    error_message="未提供工具调用信息",
                    execution_time=0.0,
                    rate_limit_info={}
                )
            }
        
        tool_name = tool_call.get("name", "")
        parameters = tool_call.get("parameters", {})
        user_id = user_info.get("user_id", "anonymous")
        user_role = user_info.get("role", "anonymous")
        
        start_time = time.time()
        
        try:
            # 1. 工具存在性检查
            if tool_name not in self.tool_registry:
                return {
                    "tool_result": ToolCallResult(
                        allowed=False,
                        tool_name=tool_name,
                        parameters=parameters,
                        error_message=f"工具 '{tool_name}' 不存在",
                        execution_time=time.time() - start_time,
                        rate_limit_info={}
                    )
                }
            
            tool_config = self.tool_registry[tool_name]
            
            # 2. 权限检查（异步）
            permission_result = await self._check_permissions_async(tool_name, user_role, user_id)
            if not permission_result["allowed"]:
                return {
                    "tool_result": ToolCallResult(
                        allowed=False,
                        tool_name=tool_name,
                        parameters=parameters,
                        error_message=permission_result["error"],
                        execution_time=time.time() - start_time,
                        rate_limit_info={}
                    )
                }
            
            # 3. 速率限制检查（异步）
            rate_limit_result = await self._check_rate_limit_async(tool_name, user_id)
            if not rate_limit_result["allowed"]:
                return {
                    "tool_result": ToolCallResult(
                        allowed=False,
                        tool_name=tool_name,
                        parameters=parameters,
                        error_message=rate_limit_result["error"],
                        execution_time=time.time() - start_time,
                        rate_limit_info=rate_limit_result.get("info", {})
                    )
                }
            
            # 4. 参数验证（异步）
            param_result = await self._validate_parameters_async(tool_name, parameters)
            if not param_result["valid"]:
                return {
                    "tool_result": ToolCallResult(
                        allowed=False,
                        tool_name=tool_name,
                        parameters=parameters,
                        error_message=param_result["error"],
                        execution_time=time.time() - start_time,
                        rate_limit_info={}
                    )
                }
            
            # 5. 安全检查（异步）
            safety_result = await self._check_safety_async(tool_name, parameters, user_info, context)
            if not safety_result["safe"]:
                return {
                    "tool_result": ToolCallResult(
                        allowed=False,
                        tool_name=tool_name,
                        parameters=parameters,
                        error_message=safety_result["error"],
                        execution_time=time.time() - start_time,
                        rate_limit_info={}
                    )
                }
            
            # 6. 缓存检查（异步）
            if self.enable_caching:
                cache_key = await self._generate_cache_key_async(tool_name, parameters)
                cached_result = await self._get_from_cache_async(cache_key)
                if cached_result:
                    return {
                        "tool_result": ToolCallResult(
                            allowed=True,
                            tool_name=tool_name,
                            parameters=parameters,
                            error_message=None,
                            execution_time=time.time() - start_time,
                            rate_limit_info={"cached": True}
                        )
                    }
            
            # 7. 记录调用历史（异步）
            if self.enable_logging:
                await self._log_tool_call_async(tool_name, parameters, user_id, True)
            
            # 8. 更新速率限制（异步）
            await self._update_rate_limit_async(tool_name, user_id)
            
            execution_time = time.time() - start_time
            
            return {
                "tool_result": ToolCallResult(
                    allowed=True,
                    tool_name=tool_name,
                    parameters=parameters,
                    error_message=None,
                    execution_time=execution_time,
                    rate_limit_info={"cached": False}
                )
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 记录错误（异步）
            if self.enable_logging:
                await self._log_tool_call_async(tool_name, parameters, user_id, False, str(e))
            
            return {
                "tool_result": ToolCallResult(
                    allowed=False,
                    tool_name=tool_name,
                    parameters=parameters,
                    error_message=f"工具调用验证失败: {str(e)}",
                    execution_time=execution_time,
                    rate_limit_info={}
                )
            }
    
    async def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理：更新共享数据
        
        Args:
            shared: 共享数据字典
            prep_res: 预处理结果
            exec_res: 执行结果
            
        Returns:
            下一个节点的标识符
        """
        tool_result = exec_res.get("tool_result")
        
        if tool_result and tool_result.allowed:
            # 工具调用允许，更新共享数据
            shared["tool_call_allowed"] = True
            shared["tool_call_info"] = {
                "tool_name": tool_result.tool_name,
                "parameters": tool_result.parameters,
                "execution_time": tool_result.execution_time
            }
            return "default"
        else:
            # 工具调用被拒绝，记录错误信息
            shared["tool_call_allowed"] = False
            shared["tool_call_error"] = tool_result.error_message if tool_result else "未知错误"
            return "error"
    
    async def _check_permissions_async(self, tool_name: str, user_role: str, user_id: str) -> Dict[str, Any]:
        """异步权限检查"""
        if tool_name not in self.tool_registry:
            return {"allowed": False, "error": f"工具 '{tool_name}' 不存在"}
        
        tool_config = self.tool_registry[tool_name]
        required_access_level = tool_config.get("access_level", ToolAccessLevel.PUBLIC)
        
        # 检查用户角色权限
        user_allowed_tools = self.user_permissions.get(user_role, [])
        if tool_name not in user_allowed_tools:
            return {"allowed": False, "error": f"用户角色 '{user_role}' 没有权限使用工具 '{tool_name}'"}
        
        # 检查访问级别
        access_levels = {
            ToolAccessLevel.PUBLIC: 0,
            ToolAccessLevel.AUTHENTICATED: 1,
            ToolAccessLevel.ADMIN: 2,
            ToolAccessLevel.RESTRICTED: 3
        }
        
        user_access_level = access_levels.get(required_access_level, 0)
        
        # 检查是否需要管理员权限
        if required_access_level == ToolAccessLevel.ADMIN and user_role != "admin":
            return {"allowed": False, "error": f"工具 '{tool_name}' 需要管理员权限"}
        
        # 检查受限工具
        if required_access_level == ToolAccessLevel.RESTRICTED:
            # 检查用户ID是否在白名单中
            restricted_users = self.user_permissions.get("restricted_users", [])
            if user_id not in restricted_users:
                return {"allowed": False, "error": f"工具 '{tool_name}' 对用户 '{user_id}' 受限"}
        
        return {"allowed": True}
    
    async def _check_rate_limit_async(self, tool_name: str, user_id: str) -> Dict[str, Any]:
        """异步速率限制检查"""
        if tool_name not in self.rate_limits:
            return {"allowed": True}
        
        rate_config = self.rate_limits[tool_name]
        requests_per_minute = rate_config.get("requests_per_minute", 0)
        requests_per_hour = rate_config.get("requests_per_hour", 0)
        
        if requests_per_minute <= 0 and requests_per_hour <= 0:
            return {"allowed": True}
        
        # 获取当前时间
        current_time = time.time()
        
        # 初始化用户调用历史
        if user_id not in self.call_history:
            self.call_history[user_id] = {}
        
        if tool_name not in self.call_history[user_id]:
            self.call_history[user_id][tool_name] = []
        
        # 清理过期的调用记录（1小时前）
        self.call_history[user_id][tool_name] = [
            call_time for call_time in self.call_history[user_id][tool_name]
            if current_time - call_time < 3600
        ]
        
        # 检查每分钟限制
        if requests_per_minute > 0:
            recent_calls = [
                call_time for call_time in self.call_history[user_id][tool_name]
                if current_time - call_time < 60
            ]
            
            if len(recent_calls) >= requests_per_minute:
                return {
                    "allowed": False,
                    "error": f"工具 '{tool_name}' 的调用频率超出限制（每分钟 {requests_per_minute} 次）",
                    "info": {"limit_type": "per_minute", "limit": requests_per_minute}
                }
        
        # 检查每小时限制
        if requests_per_hour > 0:
            if len(self.call_history[user_id][tool_name]) >= requests_per_hour:
                return {
                    "allowed": False,
                    "error": f"工具 '{tool_name}' 的调用频率超出限制（每小时 {requests_per_hour} 次）",
                    "info": {"limit_type": "per_hour", "limit": requests_per_hour}
                }
        
        return {"allowed": True}
    
    async def _validate_parameters_async(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """异步参数验证"""
        if tool_name not in self.tool_registry:
            return {"valid": False, "error": f"工具 '{tool_name}' 不存在"}
        
        tool_config = self.tool_registry[tool_name]
        max_params = tool_config.get("max_params", 10)
        required_params = tool_config.get("required_params", [])
        
        # 检查参数数量
        if len(parameters) > max_params:
            return {"valid": False, "error": f"工具 '{tool_name}' 的参数数量超出限制（最大 {max_params} 个）"}
        
        # 检查必填参数
        missing_params = []
        for param in required_params:
            if param not in parameters or parameters[param] is None:
                missing_params.append(param)
        
        if missing_params:
            return {"valid": False, "error": f"工具 '{tool_name}' 缺少必填参数: {', '.join(missing_params)}"}
        
        # 参数类型和安全性检查
        for param_name, param_value in parameters.items():
            # 检查参数类型
            if not self._is_valid_parameter_type(param_value):
                return {"valid": False, "error": f"参数 '{param_name}' 的类型无效"}
            
            # 检查参数值的安全性
            if not self._is_safe_parameter_value(param_value):
                return {"valid": False, "error": f"参数 '{param_name}' 的值不安全"}
        
        return {"valid": True}
    
    def _is_valid_parameter_type(self, value: Any) -> bool:
        """检查参数类型是否有效"""
        valid_types = (str, int, float, bool, list, dict, type(None))
        return isinstance(value, valid_types)
    
    def _is_safe_parameter_value(self, value: Any) -> bool:
        """检查参数值是否安全"""
        if isinstance(value, str):
            # 检查是否包含恶意代码
            dangerous_patterns = [
                r'<script.*?>.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'on\w+\s*=',
                r'data:text/html',
                r'file://',
                r'\.\.\/',
                r'union.*select',
                r'drop.*table',
                r'exec\s*\(',
                r'system\s*\(',
                r'os\.system',
                r'subprocess\.call'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return False
            
            # 检查长度
            if len(value) > 10000:  # 最大长度限制
                return False
        
        elif isinstance(value, (list, dict)):
            # 递归检查复杂类型
            try:
                json_str = json.dumps(value)
                return self._is_safe_parameter_value(json_str)
            except:
                return False
        
        return True
    
    async def _check_safety_async(self, tool_name: str, parameters: Dict[str, Any], user_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """异步安全检查"""
        # 检查工具调用是否在安全上下文中
        
        # 检查用户是否被标记为恶意
        if user_info.get("is_malicious", False):
            return {"safe": False, "error": "用户被标记为恶意用户"}
        
        # 检查上下文是否安全
        if context.get("is_compromised", False):
            return {"safe": False, "error": "上下文已被破坏"}
        
        # 检查工具调用是否在当前对话上下文中合理
        if not await self._is_tool_call_reasonable_async(tool_name, parameters, context):
            return {"safe": False, "error": f"工具 '{tool_name}' 在当前上下文中不合理"}
        
        return {"safe": True}
    
    async def _is_tool_call_reasonable_async(self, tool_name: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """异步检查工具调用是否合理"""
        # 简单的合理性检查
        conversation_history = context.get("conversation_history", [])
        
        # 检查工具调用是否与对话历史一致
        if tool_name == "calculator" and conversation_history:
            # 如果用户最近问了数学问题，计算器调用是合理的
            recent_messages = conversation_history[-3:]
            math_keywords = ["计算", "多少", "加减乘除", "公式", "方程"]
            
            for message in recent_messages:
                if any(keyword in message for keyword in math_keywords):
                    return True
            
            # 如果没有数学相关的对话，计算器调用可能不合理
            return False
        
        # 对于其他工具，暂时允许
        return True
    
    async def _generate_cache_key_async(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """异步生成缓存键"""
        # 生成基于工具名和参数的缓存键
        param_str = json.dumps(parameters, sort_keys=True)
        return f"{tool_name}:{hash(param_str)}"
    
    async def _get_from_cache_async(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """异步从缓存获取结果"""
        return self.cache.get(cache_key)
    
    async def _log_tool_call_async(self, tool_name: str, parameters: Dict[str, Any], user_id: str, success: bool, error: str = None):
        """异步记录工具调用"""
        log_entry = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "user_id": user_id,
            "parameters": parameters,
            "success": success,
            "error": error
        }
        
        # 这里可以集成到实际的日志系统
        print(f"[TOOL_LOG] {json.dumps(log_entry, ensure_ascii=False)}")
    
    async def _update_rate_limit_async(self, tool_name: str, user_id: str):
        """异步更新速率限制"""
        current_time = time.time()
        
        # 初始化用户调用历史
        if user_id not in self.call_history:
            self.call_history[user_id] = {}
        
        if tool_name not in self.call_history[user_id]:
            self.call_history[user_id][tool_name] = []
        
        # 添加新的调用记录
        self.call_history[user_id][tool_name].append(current_time)