"""
异步错误处理节点 - 使用PocketFlow实现异步优雅的错误处理和安全恢复
"""

import json
import time
import asyncio
import traceback
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel, Field
from pocketflow import AsyncNode
from enum import Enum


class ErrorType(str, Enum):
    """错误类型枚举"""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TOOL_ERROR = "tool_error"
    CONTENT_SAFETY_ERROR = "content_safety_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"


class ErrorHandlingResult(BaseModel):
    """错误处理结果模型"""
    error_resolved: bool = Field(description="错误是否已解决")
    recovery_action: str = Field(description="恢复操作")
    fallback_response: Optional[str] = Field(description="回退响应")
    error_details: Dict[str, Any] = Field(description="错误详细信息")
    user_message: str = Field(description="给用户的消息")
    should_retry: bool = Field(description="是否应该重试")
    retry_count: int = Field(description="重试次数")


class AsyncErrorHandlingNode(AsyncNode):
    """
    异步错误处理节点
    
    功能：
    - 错误分类和诊断
    - 自动恢复和重试
    - 回退响应生成
    - 用户友好的错误消息
    - 审计日志记录
    """
    
    def __init__(self,
                 enable_auto_recovery: bool = True,
                 enable_fallback_responses: bool = True,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 enable_logging: bool = True,
                 custom_handlers: Optional[Dict[str, Callable]] = None):
        """
        初始化错误处理节点
        
        Args:
            enable_auto_recovery: 启用自动恢复
            enable_fallback_responses: 启用回退响应
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            enable_logging: 启用日志记录
            custom_handlers: 自定义错误处理器
        """
        super().__init__()
        self.enable_auto_recovery = enable_auto_recovery
        self.enable_fallback_responses = enable_fallback_responses
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_logging = enable_logging
        self.custom_handlers = custom_handlers or {}
        
        # 回退响应模板
        self.fallback_responses = {
            ErrorType.VALIDATION_ERROR: "抱歉，您的输入格式不正确。请检查输入内容并重试。",
            ErrorType.PERMISSION_ERROR: "抱歉，您没有权限执行此操作。请联系管理员获取帮助。",
            ErrorType.RATE_LIMIT_ERROR: "抱歉，当前请求过于频繁。请稍后再试。",
            ErrorType.TOOL_ERROR: "抱歉，工具调用失败。请稍后重试或联系技术支持。",
            ErrorType.CONTENT_SAFETY_ERROR: "抱歉，检测到不当内容。请修改您的输入并重试。",
            ErrorType.SYSTEM_ERROR: "抱歉，系统暂时不可用。请稍后重试。",
            ErrorType.NETWORK_ERROR: "抱歉，网络连接出现问题。请检查网络连接并重试。",
            ErrorType.TIMEOUT_ERROR: "抱歉，请求超时。请稍后重试。"
        }
        
        # 异步自动恢复策略
        self.recovery_strategies = {
            ErrorType.VALIDATION_ERROR: self._handle_validation_error_async,
            ErrorType.PERMISSION_ERROR: self._handle_permission_error_async,
            ErrorType.RATE_LIMIT_ERROR: self._handle_rate_limit_error_async,
            ErrorType.TOOL_ERROR: self._handle_tool_error_async,
            ErrorType.CONTENT_SAFETY_ERROR: self._handle_content_safety_error_async,
            ErrorType.SYSTEM_ERROR: self._handle_system_error_async,
            ErrorType.NETWORK_ERROR: self._handle_network_error_async,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error_async
        }
    
    async def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理：准备错误处理数据
        
        Args:
            shared: 共享数据字典
            
        Returns:
            处理后的数据
        """
        # 检查是否有错误信息
        error_info = shared.get("error_info", {})
        validation_errors = shared.get("validation_errors", [])
        tool_call_error = shared.get("tool_call_error", "")
        filter_warnings = shared.get("filter_warnings", [])
        
        # 确定错误类型
        error_type = await self._classify_error_async(error_info, validation_errors, tool_call_error, filter_warnings)
        
        return {
            "error_type": error_type,
            "error_info": error_info,
            "validation_errors": validation_errors,
            "tool_call_error": tool_call_error,
            "filter_warnings": filter_warnings,
            "context": shared.get("context", {}),
            "user_info": shared.get("user_info", {}),
            "original_shared": shared
        }
    
    async def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行：处理错误
        
        Args:
            prep_res: 预处理结果
            
        Returns:
            错误处理结果
        """
        error_type = prep_res.get("error_type", ErrorType.SYSTEM_ERROR)
        error_info = prep_res.get("error_info", {})
        validation_errors = prep_res.get("validation_errors", [])
        tool_call_error = prep_res.get("tool_call_error", "")
        filter_warnings = prep_res.get("filter_warnings", [])
        context = prep_res.get("context", {})
        user_info = prep_res.get("user_info", {})
        
        # 获取重试次数
        retry_count = context.get("retry_count", 0)
        
        # 记录错误日志
        if self.enable_logging:
            await self._log_error_async(error_type, error_info, validation_errors, tool_call_error, filter_warnings)
        
        # 尝试自动恢复
        if self.enable_auto_recovery and retry_count < self.max_retries:
            recovery_result = await self._attempt_recovery_async(error_type, error_info, retry_count)
            
            if recovery_result["resolved"]:
                return {
                    "error_result": ErrorHandlingResult(
                        error_resolved=True,
                        recovery_action=recovery_result["action"],
                        fallback_response=None,
                        error_details=error_info,
                        user_message="问题已自动解决，请重试您的操作。",
                        should_retry=True,
                        retry_count=retry_count + 1
                    )
                }
        
        # 生成回退响应
        fallback_response = None
        if self.enable_fallback_responses:
            fallback_response = await self._generate_fallback_response_async(error_type, error_info, user_info)
        
        # 生成用户友好的错误消息
        user_message = await self._generate_user_message_async(error_type, error_info, validation_errors, tool_call_error)
        
        # 根据恢复结果决定是否重试
        # 验证错误不应该重试
        if error_type == ErrorType.VALIDATION_ERROR:
            should_retry = False
        else:
            should_retry = error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR, ErrorType.SYSTEM_ERROR]
        
        error_result = ErrorHandlingResult(
            error_resolved=recovery_result.get("resolved", False),
            recovery_action=recovery_result.get("action", "fallback_response"),
            fallback_response=fallback_response,
            error_details={
                "error_type": error_type,
                "error_info": error_info,
                "validation_errors": validation_errors,
                "tool_call_error": tool_call_error,
                "filter_warnings": filter_warnings,
                "timestamp": time.time()
            },
            user_message=user_message,
            should_retry=should_retry,
            retry_count=retry_count
        )
        
        return {"error_result": error_result}
    
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
        error_result = exec_res.get("error_result")
        
        if error_result:
            # 更新共享数据
            shared["error_handled"] = True
            shared["error_result"] = error_result.dict()
            shared["error_user_message"] = error_result.user_message
            shared["error_resolved"] = error_result.error_resolved
            shared["should_retry"] = error_result.should_retry
            shared["retry_count"] = error_result.retry_count
            
            if error_result.fallback_response:
                shared["fallback_response"] = error_result.fallback_response
            
            # 如果错误已解决或应该重试，继续流程
            if error_result.error_resolved or error_result.should_retry:
                return "default"
            else:
                # 否则终止流程
                return "error"
        
        return "default"
    
    async def _classify_error_async(self, error_info: Dict[str, Any], validation_errors: List[str], tool_call_error: str, filter_warnings: List[str]) -> ErrorType:
        """异步错误分类"""
        # 检查验证错误
        if validation_errors or error_info.get("validation_failed"):
            return ErrorType.VALIDATION_ERROR
        
        # 检查权限错误
        if "permission" in tool_call_error.lower() or "权限" in tool_call_error:
            return ErrorType.PERMISSION_ERROR
        
        # 检查速率限制错误
        if "rate limit" in tool_call_error.lower() or "频率限制" in tool_call_error:
            return ErrorType.RATE_LIMIT_ERROR
        
        # 检查工具错误
        if tool_call_error and "tool" in tool_call_error.lower():
            return ErrorType.TOOL_ERROR
        
        # 检查内容安全错误
        if filter_warnings or error_info.get("content_safety_failed"):
            return ErrorType.CONTENT_SAFETY_ERROR
        
        # 检查网络错误
        if "network" in tool_call_error.lower() or "连接" in tool_call_error:
            return ErrorType.NETWORK_ERROR
        
        # 检查超时错误
        if "timeout" in tool_call_error.lower() or "超时" in tool_call_error:
            return ErrorType.TIMEOUT_ERROR
        
        # 检查系统错误
        if "system" in tool_call_error.lower() or "系统" in tool_call_error:
            return ErrorType.SYSTEM_ERROR
        
        # 默认返回系统错误
        return ErrorType.SYSTEM_ERROR
    
    async def _attempt_recovery_async(self, error_type: ErrorType, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步尝试自动恢复"""
        if error_type in self.recovery_strategies:
            try:
                recovery_result = await self.recovery_strategies[error_type](error_info, retry_count)
                return recovery_result
            except Exception as e:
                # 如果恢复策略失败，返回失败结果
                return {"resolved": False, "action": f"recovery_failed: {str(e)}"}
        
        return {"resolved": False, "action": "no_recovery_strategy"}
    
    async def _handle_validation_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理验证错误"""
        # 验证错误通常不能通过重试解决
        return {"resolved": False, "action": "validation_error_cannot_retry"}
    
    async def _handle_permission_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理权限错误"""
        # 权限错误通常不能通过重试解决
        return {"resolved": False, "action": "permission_error_cannot_retry"}
    
    async def _handle_rate_limit_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理速率限制错误"""
        # 速率限制错误可以通过等待后重试
        if retry_count < self.max_retries:
            # 等待时间随着重试次数增加
            wait_time = self.retry_delay * (2 ** retry_count)
            await asyncio.sleep(wait_time)
            return {"resolved": True, "action": f"rate_limit_wait_{wait_time}s"}
        
        return {"resolved": False, "action": "rate_limit_max_retries_exceeded"}
    
    async def _handle_tool_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理工具错误"""
        # 工具错误可以通过重试解决（可能是临时问题）
        if retry_count < self.max_retries:
            # 等待一段时间后重试
            await asyncio.sleep(self.retry_delay)
            return {"resolved": True, "action": "tool_error_retry"}
        
        return {"resolved": False, "action": "tool_error_max_retries_exceeded"}
    
    async def _handle_content_safety_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理内容安全错误"""
        # 内容安全错误通常不能通过重试解决
        return {"resolved": False, "action": "content_safety_error_cannot_retry"}
    
    async def _handle_system_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理系统错误"""
        # 系统错误可以通过重试解决（可能是临时问题）
        if retry_count < self.max_retries:
            # 等待时间随着重试次数增加
            wait_time = self.retry_delay * (2 ** retry_count)
            await asyncio.sleep(wait_time)
            return {"resolved": True, "action": f"system_error_wait_{wait_time}s"}
        
        return {"resolved": False, "action": "system_error_max_retries_exceeded"}
    
    async def _handle_network_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理网络错误"""
        # 网络错误可以通过重试解决
        if retry_count < self.max_retries:
            # 等待时间随着重试次数增加
            wait_time = self.retry_delay * (2 ** retry_count)
            await asyncio.sleep(wait_time)
            return {"resolved": True, "action": f"network_error_wait_{wait_time}s"}
        
        return {"resolved": False, "action": "network_error_max_retries_exceeded"}
    
    async def _handle_timeout_error_async(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """异步处理超时错误"""
        # 超时错误可以通过重试解决
        if retry_count < self.max_retries:
            # 等待时间随着重试次数增加
            wait_time = self.retry_delay * (2 ** retry_count)
            await asyncio.sleep(wait_time)
            return {"resolved": True, "action": f"timeout_error_wait_{wait_time}s"}
        
        return {"resolved": False, "action": "timeout_error_max_retries_exceeded"}
    
    async def _generate_fallback_response_async(self, error_type: ErrorType, error_info: Dict[str, Any], user_info: Dict[str, Any]) -> str:
        """异步生成回退响应"""
        if error_type in self.fallback_responses:
            base_response = self.fallback_responses[error_type]
            
            # 根据用户信息个性化回退响应
            user_name = user_info.get("name", "")
            if user_name:
                return f"{user_name}，{base_response}"
            
            return base_response
        
        return "抱歉，发生了未知错误。请联系技术支持。"
    
    async def _generate_user_message_async(self, error_type: ErrorType, error_info: Dict[str, Any], validation_errors: List[str], tool_call_error: str) -> str:
        """异步生成用户友好的错误消息"""
        if error_type == ErrorType.VALIDATION_ERROR and validation_errors:
            return f"输入验证失败: {', '.join(validation_errors)}"
        elif error_type == ErrorType.TOOL_ERROR and tool_call_error:
            return f"工具调用失败: {tool_call_error}"
        elif error_type == ErrorType.CONTENT_SAFETY_ERROR:
            return "检测到不当内容，请修改您的输入"
        elif error_type in self.fallback_responses:
            return self.fallback_responses[error_type]
        
        return "发生未知错误，请稍后重试"
    
    async def _log_error_async(self, error_type: ErrorType, error_info: Dict[str, Any], validation_errors: List[str], tool_call_error: str, filter_warnings: List[str]):
        """异步记录错误日志"""
        log_entry = {
            "timestamp": time.time(),
            "error_type": error_type,
            "error_info": error_info,
            "validation_errors": validation_errors,
            "tool_call_error": tool_call_error,
            "filter_warnings": filter_warnings
        }
        
        # 这里可以集成到实际的日志系统
        print(f"[ERROR_LOG] {json.dumps(log_entry, ensure_ascii=False)}")
    
    async def _handle_custom_error_async(self, error_type: str, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """异步处理自定义错误"""
        if error_type in self.custom_handlers:
            try:
                # 调用自定义错误处理器
                result = await self.custom_handlers[error_type](error_info)
                return result
            except Exception as e:
                return {"resolved": False, "action": f"custom_handler_failed: {str(e)}"}
        
        return {"resolved": False, "action": "no_custom_handler"}