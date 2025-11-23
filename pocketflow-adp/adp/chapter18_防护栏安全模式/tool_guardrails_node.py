"""
工具调用防护栏节点 - 使用PocketFlow实现工具调用的安全控制
"""

import json
import time
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel, Field
from pocketflow import BaseNode
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


class ToolGuardrailsNode(BaseNode):
    """
    工具调用防护栏节点
    
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
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
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
            
            # 2. 权限检查
            permission_result = self._check_permissions(tool_name, user_role, user_id)
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
            
            # 3. 参数验证
            param_result = self._validate_parameters(tool_name, parameters)
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
            
            # 4. 速率限制检查
            rate_limit_result = self._check_rate_limit(tool_name, user_id)
            if not rate_limit_result["allowed"]:
                return {
                    "tool_result": ToolCallResult(
                        allowed=False,
                        tool_name=tool_name,
                        parameters=parameters,
                        error_message=rate_limit_result["error"],
                        execution_time=time.time() - start_time,
                        rate_limit_info=rate_limit_result["info"]
                    )
                }
            
            # 5. 安全检查
            security_result = self._security_check(tool_name, parameters, user_id)
            if not security_result["safe"]:
                return {
                    "tool_result": ToolCallResult(
                        allowed=False,
                        tool_name=tool_name,
                        parameters=parameters,
                        error_message=security_result["error"],
                        execution_time=time.time() - start_time,
                        rate_limit_info={}
                    )
                }
            
            # 6. 记录调用
            if self.enable_logging:
                self._log_tool_call(tool_name, parameters, user_id, True, "")
            
            # 7. 更新调用历史
            self._update_call_history(tool_name, user_id)
            
            execution_time = time.time() - start_time
            
            return {
                "tool_result": ToolCallResult(
                    allowed=True,
                    tool_name=tool_name,
                    parameters=param_result["cleaned_params"],
                    error_message=None,
                    execution_time=execution_time,
                    rate_limit_info=rate_limit_result["info"]
                )
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工具调用处理失败: {str(e)}"
            
            if self.enable_logging:
                self._log_tool_call(tool_name, parameters, user_id, False, error_msg)
            
            return {
                "tool_result": ToolCallResult(
                    allowed=False,
                    tool_name=tool_name,
                    parameters=parameters,
                    error_message=error_msg,
                    execution_time=execution_time,
                    rate_limit_info={}
                )
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        后处理：更新共享数据
        
        Args:
            exec_res: 执行结果
            shared: 共享数据字典
            
        Returns:
            更新后的共享数据
        """
        tool_result = exec_res.get("tool_result")
        
        if tool_result.allowed:
            shared["tool_call_approved"] = True
            shared["approved_tool_call"] = {
                "name": tool_result.tool_name,
                "parameters": tool_result.parameters
            }
            shared["tool_execution_time"] = tool_result.execution_time
        else:
            shared["tool_call_approved"] = False
            shared["tool_call_error"] = tool_result.error_message
            shared["tool_call_denied_reason"] = tool_result.error_message
        
        shared["tool_guardrails_metadata"] = {
            "tool_name": tool_result.tool_name,
            "execution_time": tool_result.execution_time,
            "rate_limit_info": tool_result.rate_limit_info,
            "user_id": shared.get("user_info", {}).get("user_id", "anonymous")
        }
        
        return "default"
    
    def _check_permissions(self, tool_name: str, user_role: str, user_id: str) -> Dict[str, Any]:
        """检查用户权限"""
        # 获取用户权限列表
        user_perms = self.user_permissions.get(user_role, [])
        
        if tool_name not in user_perms:
            return {
                "allowed": False,
                "error": f"用户角色 '{user_role}' 没有权限使用工具 '{tool_name}'"
            }
        
        # 检查工具访问级别
        tool_access = self.tool_registry[tool_name]["access_level"]
        
        if tool_access == ToolAccessLevel.RESTRICTED:
            # 受限工具需要额外验证
            if not self._is_authorized_for_restricted_tool(user_id, tool_name):
                return {
                    "allowed": False,
                    "error": f"用户 '{user_id}' 未授权使用受限工具 '{tool_name}'"
                }
        
        return {"allowed": True, "error": ""}
    
    def _validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证工具参数"""
        tool_config = self.tool_registry[tool_name]
        
        # 检查必填参数
        required_params = tool_config.get("required_params", [])
        missing_params = []
        
        for param in required_params:
            if param not in parameters or parameters[param] is None:
                missing_params.append(param)
        
        if missing_params:
            return {
                "valid": False,
                "error": f"缺少必填参数: {', '.join(missing_params)}"
            }
        
        # 检查参数数量
        max_params = tool_config.get("max_params", 10)
        if len(parameters) > max_params:
            return {
                "valid": False,
                "error": f"参数数量超过限制 ({len(parameters)} > {max_params})"
            }
        
        # 参数清理
        cleaned_params = self._clean_parameters(parameters, tool_name)
        
        return {"valid": True, "error": "", "cleaned_params": cleaned_params}
    
    def _check_rate_limit(self, tool_name: str, user_id: str) -> Dict[str, Any]:
        """检查速率限制"""
        if tool_name not in self.rate_limits:
            return {"allowed": True, "error": "", "info": {}}
        
        limits = self.rate_limits[tool_name]
        current_time = time.time()
        
        # 获取用户调用历史
        user_history = self.call_history.get(user_id, {}).get(tool_name, [])
        
        # 清理过期的调用记录（1小时前）
        user_history = [t for t in user_history if current_time - t < 3600]
        
        # 检查每分钟限制
        recent_calls = [t for t in user_history if current_time - t < 60]
        rpm_limit = limits.get("requests_per_minute", 60)
        
        if len(recent_calls) >= rpm_limit:
            return {
                "allowed": False,
                "error": f"工具 '{tool_name}' 的速率限制已超出 (每分钟 {rpm_limit} 次)",
                "info": {
                    "limit_type": "rpm",
                    "limit": rpm_limit,
                    "current": len(recent_calls),
                    "retry_after": 60 - (current_time - min(recent_calls)) if recent_calls else 60
                }
            }
        
        # 检查每小时限制
        rph_limit = limits.get("requests_per_hour", 1000)
        
        if len(user_history) >= rph_limit:
            return {
                "allowed": False,
                "error": f"工具 '{tool_name}' 的速率限制已超出 (每小时 {rph_limit} 次)",
                "info": {
                    "limit_type": "rph",
                    "limit": rph_limit,
                    "current": len(user_history),
                    "retry_after": 3600 - (current_time - min(user_history)) if user_history else 3600
                }
            }
        
        return {
            "allowed": True,
            "error": "",
            "info": {
                "rpm_remaining": rpm_limit - len(recent_calls),
                "rph_remaining": rph_limit - len(user_history)
            }
        }
    
    def _security_check(self, tool_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """安全检查"""
        # 参数安全检查
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                # 检查危险模式
                dangerous_patterns = [
                    r'<script.*?>.*?</script>',
                    r'javascript:',
                    r'\.\.\/',
                    r'\.\.\\',
                    r'\/etc\/passwd',
                    r'C:\\Windows',
                    r'rm -rf',
                    r'del .*',
                    r'format .*'
                ]
                
                for pattern in dangerous_patterns:
                    if re.search(pattern, param_value, re.IGNORECASE):
                        return {
                            "safe": False,
                            "error": f"参数 '{param_name}' 包含潜在危险内容"
                        }
        
        return {"safe": True, "error": ""}
    
    def _clean_parameters(self, parameters: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """清理参数"""
        cleaned = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # 移除控制字符
                cleaned_value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
                cleaned[key] = cleaned_value.strip()
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _is_authorized_for_restricted_tool(self, user_id: str, tool_name: str) -> bool:
        """检查用户是否授权使用受限工具"""
        # 在实际应用中，这里应该查询数据库或权限系统
        # 这里简化处理，只允许特定用户
        authorized_users = {
            "admin_user": ["database_query", "code_executor"],
            "system": ["database_query", "code_executor"]
        }
        
        user_tools = authorized_users.get(user_id, [])
        return tool_name in user_tools
    
    def _update_call_history(self, tool_name: str, user_id: str) -> None:
        """更新调用历史"""
        current_time = time.time()
        
        if user_id not in self.call_history:
            self.call_history[user_id] = {}
        
        if tool_name not in self.call_history[user_id]:
            self.call_history[user_id][tool_name] = []
        
        self.call_history[user_id][tool_name].append(current_time)
    
    def _log_tool_call(self, tool_name: str, parameters: Dict[str, Any], user_id: str, allowed: bool, error: str) -> None:
        """记录工具调用日志"""
        log_entry = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "user_id": user_id,
            "parameters": parameters,
            "allowed": allowed,
            "error": error
        }
        
        # 在实际应用中，这里应该写入日志系统
        if allowed:
            print(f"[TOOL_LOG] ✅ 用户 {user_id} 调用工具 {tool_name} 成功")
        else:
            print(f"[TOOL_LOG] ❌ 用户 {user_id} 调用工具 {tool_name} 失败: {error}")


# 测试函数
async def test_tool_guardrails_node():
    """测试工具防护栏节点"""
    from pocketflow import Flow
    
    # 创建工具防护栏节点
    guardrails_node = ToolGuardrailsNode()
    
    # 测试用例
    test_cases = [
        {
            "tool_call": {"name": "web_search", "parameters": {"query": "今天天气"}},
            "user_info": {"user_id": "user123", "role": "user"},
            "context": {}
        },
        {
            "tool_call": {"name": "database_query", "parameters": {"query": "SELECT * FROM users"}},
            "user_info": {"user_id": "user123", "role": "user"},
            "context": {}
        },
        {
            "tool_call": {"name": "code_executor", "parameters": {"code": "print('hello')"}},
            "user_info": {"user_id": "admin_user", "role": "admin"},
            "context": {}
        },
        {
            "tool_call": {"name": "web_search", "parameters": {"query": "<script>alert('xss')</script>"}},
            "user_info": {"user_id": "user123", "role": "user"},
            "context": {}
        },
        {
            "tool_call": {"name": "nonexistent_tool", "parameters": {}},
            "user_info": {"user_id": "user123", "role": "user"},
            "context": {}
        }
    ]
    
    print("=== 工具防护栏节点测试 ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print(f"工具调用: {test_case['tool_call']}")
        print(f"用户信息: {test_case['user_info']}")
        
        # 创建临时共享数据
        shared_data = test_case.copy()
        
        # 执行节点
        result = guardrails_node(shared_data)
        
        if result.get("tool_call_approved"):
            print("✅ 工具调用通过")
            print(f"执行时间: {result.get('tool_execution_time', 0):.3f}秒")
        else:
            print("❌ 工具调用被拒绝")
            print(f"拒绝原因: {result.get('tool_call_error')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tool_guardrails_node())