"""
错误处理节点 - 使用PocketFlow实现优雅的错误处理和安全恢复
"""

import json
import time
import traceback
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel, Field
from pocketflow import BaseNode
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


class ErrorHandlingNode(BaseNode):
    """
    错误处理节点
    
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
        
        # 自动恢复策略
        self.recovery_strategies = {
            ErrorType.VALIDATION_ERROR: self._handle_validation_error,
            ErrorType.PERMISSION_ERROR: self._handle_permission_error,
            ErrorType.RATE_LIMIT_ERROR: self._handle_rate_limit_error,
            ErrorType.TOOL_ERROR: self._handle_tool_error,
            ErrorType.CONTENT_SAFETY_ERROR: self._handle_content_safety_error,
            ErrorType.SYSTEM_ERROR: self._handle_system_error,
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error
        }
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
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
        error_type = self._classify_error(error_info, validation_errors, tool_call_error, filter_warnings)
        
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
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
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
            self._log_error(error_type, error_info, validation_errors, tool_call_error, filter_warnings)
        
        # 尝试自动恢复
        if self.enable_auto_recovery and retry_count < self.max_retries:
            recovery_result = self._attempt_recovery(error_type, error_info, retry_count)
            
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
            fallback_response = self._generate_fallback_response(error_type, error_info, user_info)
        
        # 生成用户友好的错误消息
        user_message = self._generate_user_message(error_type, error_info, validation_errors, tool_call_error)
        
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
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        后处理：更新共享数据
        
        Args:
            exec_res: 执行结果
            shared: 共享数据字典
            
        Returns:
            更新后的共享数据
        """
        error_result = exec_res.get("error_result")
        
        if error_result.error_resolved:
            # 错误已解决，可以重试
            shared["error_resolved"] = True
            shared["should_retry"] = True
            shared["retry_count"] = error_result.retry_count
        else:
            # 错误未解决，使用回退响应
            shared["error_resolved"] = False
            shared["should_retry"] = error_result.should_retry
            shared["fallback_response"] = error_result.fallback_response
            shared["user_error_message"] = error_result.user_message
        
        shared["error_handling_metadata"] = {
            "error_type": error_result.error_details.get("error_type"),
            "recovery_action": error_result.recovery_action,
            "retry_count": error_result.retry_count,
            "timestamp": time.time()
        }
        
        return "default"
    
    def _classify_error(self, error_info: Dict[str, Any], validation_errors: List[str], 
                       tool_call_error: str, filter_warnings: List[str]) -> ErrorType:
        """错误分类"""
        # 检查显式验证错误列表
        if validation_errors:
            return ErrorType.VALIDATION_ERROR
        
        # 检查错误信息中的类型字段
        error_type_str = error_info.get("type", "").lower()
        if "validation" in error_type_str:
            return ErrorType.VALIDATION_ERROR
        elif "permission" in error_type_str or "unauthorized" in error_type_str:
            return ErrorType.PERMISSION_ERROR
        elif "rate" in error_type_str and "limit" in error_type_str:
            return ErrorType.RATE_LIMIT_ERROR
        elif "content" in error_type_str and "safety" in error_type_str:
            return ErrorType.CONTENT_SAFETY_ERROR
        elif "timeout" in error_type_str:
            return ErrorType.TIMEOUT_ERROR
        elif "network" in error_type_str or "connection" in error_type_str:
            return ErrorType.NETWORK_ERROR
        elif "tool" in error_type_str:
            return ErrorType.TOOL_ERROR
        
        # 检查工具调用错误
        if "permission" in tool_call_error.lower() or "unauthorized" in tool_call_error.lower():
            return ErrorType.PERMISSION_ERROR
        
        if "rate limit" in tool_call_error.lower() or "too many requests" in tool_call_error.lower():
            return ErrorType.RATE_LIMIT_ERROR
        
        if "content safety" in str(error_info).lower() or "inappropriate" in str(error_info).lower():
            return ErrorType.CONTENT_SAFETY_ERROR
        
        if "timeout" in str(error_info).lower():
            return ErrorType.TIMEOUT_ERROR
        
        if "network" in str(error_info).lower() or "connection" in str(error_info).lower():
            return ErrorType.NETWORK_ERROR
        
        if tool_call_error:
            return ErrorType.TOOL_ERROR
        
        return ErrorType.SYSTEM_ERROR
    
    def _attempt_recovery(self, error_type: ErrorType, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """尝试自动恢复"""
        # 使用自定义处理器（如果有）
        if error_type.value in self.custom_handlers:
            return self.custom_handlers[error_type.value](error_info, retry_count)
        
        # 使用默认恢复策略
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type](error_info, retry_count)
        
        return {"resolved": False, "action": "no_recovery_available"}
    
    def _handle_validation_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理验证错误"""
        # 验证错误不应该自动恢复，需要用户修正输入
        return {
            "resolved": False,
            "action": "user_input_correction_required",
            "suggestion": "请检查输入格式并确保所有必填字段都已提供"
        }
    
    def _handle_permission_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理权限错误"""
        # 权限错误通常无法自动恢复
        return {
            "resolved": False,
            "action": "escalate_to_admin",
            "suggestion": "请联系系统管理员获取相应权限"
        }
    
    def _handle_rate_limit_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理速率限制错误"""
        # 等待一段时间后重试
        import time
        wait_time = self.retry_delay * (retry_count + 1)
        time.sleep(wait_time)
        
        return {
            "resolved": True,
            "action": "rate_limit_wait_and_retry",
            "suggestion": f"等待 {wait_time} 秒后重试"
        }
    
    def _handle_tool_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理工具错误"""
        # 尝试使用备用工具或方法
        return {
            "resolved": True,
            "action": "fallback_tool_or_method",
            "suggestion": "尝试使用备用工具或方法"
        }
    
    def _handle_content_safety_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理内容安全错误"""
        # 尝试重新生成内容
        return {
            "resolved": True,
            "action": "content_regeneration",
            "suggestion": "正在重新生成安全的内容"
        }
    
    def _handle_system_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理系统错误"""
        # 系统错误可能需要等待更长时间
        if retry_count < 2:
            import time
            time.sleep(self.retry_delay * 2)
            return {
                "resolved": True,
                "action": "system_recovery_wait",
                "suggestion": "等待系统恢复后重试"
            }
        
        return {
            "resolved": False,
            "action": "system_error_persistent",
            "suggestion": "系统错误持续存在，请联系技术支持"
        }
    
    def _handle_network_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理网络错误"""
        # 网络错误通常可以通过重试解决
        import time
        wait_time = self.retry_delay * (retry_count + 1)
        time.sleep(wait_time)
        
        return {
            "resolved": True,
            "action": "network_retry",
            "suggestion": f"网络连接问题，等待 {wait_time} 秒后重试"
        }
    
    def _handle_timeout_error(self, error_info: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
        """处理超时错误"""
        # 超时错误可以通过增加超时时间或优化请求来解决
        return {
            "resolved": True,
            "action": "timeout_optimization",
            "suggestion": "优化请求参数或增加超时时间后重试"
        }
    
    def _generate_fallback_response(self, error_type: ErrorType, error_info: Dict[str, Any], user_info: Dict[str, Any]) -> str:
        """生成回退响应"""
        # 根据用户类型和错误类型生成个性化回退响应
        user_role = user_info.get("role", "user")
        
        if user_role == "admin":
            # 管理员用户获得更详细的信息
            base_response = self.fallback_responses.get(error_type, "发生未知错误，请联系技术支持。")
            return f"{base_response} 错误详情: {error_info.get('details', '无详细信息')}"
        else:
            # 普通用户获得简化的友好响应
            return self.fallback_responses.get(error_type, "抱歉，处理您的请求时出现问题。请稍后重试。")
    
    def _generate_user_message(self, error_type: ErrorType, error_info: Dict[str, Any], 
                              validation_errors: List[str], tool_call_error: str) -> str:
        """生成用户友好的错误消息"""
        if validation_errors:
            return f"输入验证失败: {'; '.join(validation_errors)}"
        
        if tool_call_error:
            return f"工具调用失败: {tool_call_error}"
        
        return self.fallback_responses.get(error_type, "抱歉，处理您的请求时出现问题。请稍后重试。")
    
    def _log_error(self, error_type: ErrorType, error_info: Dict[str, Any], 
                   validation_errors: List[str], tool_call_error: str, filter_warnings: List[str]) -> None:
        """记录错误日志"""
        log_entry = {
            "timestamp": time.time(),
            "error_type": error_type,
            "error_info": error_info,
            "validation_errors": validation_errors,
            "tool_call_error": tool_call_error,
            "filter_warnings": filter_warnings
        }
        
        # 在实际应用中，这里应该写入日志系统
        print(f"[ERROR_LOG] ❌ {error_type}: {error_info}")


# 测试函数
async def test_error_handling_node():
    """测试错误处理节点"""
    from pocketflow import Flow
    
    # 创建错误处理节点
    error_node = ErrorHandlingNode(
        enable_auto_recovery=True,
        enable_fallback_responses=True,
        max_retries=3,
        retry_delay=0.1  # 测试用短延迟
    )
    
    # 测试用例
    test_cases = [
        {
            "validation_errors": ["输入不能为空", "格式不正确"],
            "context": {}
        },
        {
            "tool_call_error": "权限不足，无法访问该工具",
            "context": {}
        },
        {
            "error_info": {"type": "rate_limit", "details": "超出速率限制"},
            "context": {}
        },
        {
            "error_info": {"type": "network", "details": "连接超时"},
            "context": {}
        },
        {
            "filter_warnings": ["检测到毒性内容"],
            "error_info": {"type": "content_safety"},
            "context": {}
        }
    ]
    
    print("=== 错误处理节点测试 ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print(f"错误信息: {test_case}")
        
        # 创建临时共享数据
        shared_data = test_case.copy()
        
        # 执行节点
        result = error_node(shared_data)
        
        error_result = result.get("error_result")
        
        if error_result.error_resolved:
            print("✅ 错误已自动解决")
            print(f"恢复操作: {error_result.recovery_action}")
            print(f"是否重试: {error_result.should_retry}")
        else:
            print("❌ 错误未解决")
            print(f"回退响应: {error_result.fallback_response}")
            print(f"用户消息: {error_result.user_message}")
            print(f"是否重试: {error_result.should_retry}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_error_handling_node())