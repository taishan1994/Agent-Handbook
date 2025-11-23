"""
异步输入验证节点 - 使用PocketFlow实现异步输入验证和清理
"""

import json
import re
import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from pocketflow import AsyncNode


class InputValidationResult(BaseModel):
    """输入验证结果模型"""
    is_valid: bool = Field(description="输入是否有效")
    cleaned_input: str = Field(description="清理后的输入")
    validation_errors: List[str] = Field(description="验证错误列表")
    original_input: str = Field(description="原始输入")
    metadata: Dict[str, Any] = Field(description="验证元数据")


class AsyncInputValidationNode(AsyncNode):
    """
    异步输入验证节点
    
    功能：
    - 输入格式验证
    - 参数验证
    - 安全清理
    - 上下文一致性验证
    """
    
    def __init__(self, 
                 max_length: int = 1000,
                 allow_special_chars: bool = True,
                 required_fields: Optional[List[str]] = None,
                 forbidden_patterns: Optional[List[str]] = None):
        """
        初始化输入验证节点
        
        Args:
            max_length: 最大输入长度
            allow_special_chars: 是否允许特殊字符
            required_fields: 必填字段列表
            forbidden_patterns: 禁止的模式列表
        """
        super().__init__()
        self.max_length = max_length
        self.allow_special_chars = allow_special_chars
        self.required_fields = required_fields or []
        self.forbidden_patterns = forbidden_patterns or [
            r'<script.*?>.*?</script>',  # 脚本注入
            r'javascript:',               # JavaScript协议
            r'on\w+\s*=',                 # 事件处理器
            r'data:text/html',            # 数据URI
            r'vbscript:',                 # VBScript
            r'file://',                   # 文件协议
            r'\.\.\/',                    # 路径遍历
        ]
    
    async def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理：准备输入数据
        
        Args:
            shared: 共享数据字典
            
        Returns:
            处理后的数据
        """
        # 获取用户输入
        user_input = shared.get("user_input", "")
        context = shared.get("context", {})
        
        return {
            "user_input": user_input,
            "context": context,
            "original_shared": shared
        }
    
    async def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行：验证和清理输入
        
        Args:
            prep_res: 预处理结果
            
        Returns:
            验证结果
        """
        user_input = prep_res.get("user_input", "")
        context = prep_res.get("context", {})
        
        validation_errors = []
        cleaned_input = user_input
        
        # 1. 基本验证
        if not user_input or not user_input.strip():
            validation_errors.append("输入不能为空")
            return {
                "validation_result": InputValidationResult(
                    is_valid=False,
                    cleaned_input="",
                    validation_errors=validation_errors,
                    original_input=user_input,
                    metadata={"step": "basic_validation"}
                )
            }
        
        # 2. 长度验证
        if len(user_input) > self.max_length:
            validation_errors.append(f"输入长度超过最大限制 ({len(user_input)} > {self.max_length})")
            cleaned_input = user_input[:self.max_length]
        
        # 3. 必填字段验证
        # 检查user_info中的必填字段
        user_info = prep_res.get("original_shared", {}).get("user_info", {})
        missing_fields = []
        for field in self.required_fields:
            if field not in user_info or not user_info[field]:
                missing_fields.append(field)
        
        if missing_fields:
            validation_errors.append(f"缺少必填字段: {', '.join(missing_fields)}")
        
        # 如果user_input是字典，也检查其中的必填字段
        if isinstance(user_input, dict):
            missing_input_fields = []
            for field in self.required_fields:
                if field not in user_input or not user_input[field]:
                    missing_input_fields.append(field)
            
            if missing_input_fields:
                validation_errors.append(f"输入缺少必填字段: {', '.join(missing_input_fields)}")
        
        # 4. 安全模式验证
        if not self.allow_special_chars:
            # 移除特殊字符
            cleaned_input = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned_input)
        
        # 5. 危险模式检测
        for pattern in self.forbidden_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                validation_errors.append(f"检测到潜在危险模式: {pattern}")
        
        # 6. SQL注入检测（简化版）
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b.*?)',
            r'(\b(or|and)\b.*=.*)',
            r'(\bunion\b.*\bselect\b)',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                validation_errors.append("检测到潜在的SQL注入模式")
                break
        
        # 7. 上下文一致性验证
        if context:
            # 检查是否与之前的对话一致
            previous_topics = context.get("conversation_history", [])
            if previous_topics:
                # 简单的主题一致性检查
                current_topic = await self._extract_topic_async(cleaned_input)
                if current_topic and not await self._is_topic_consistent_async(current_topic, previous_topics):
                    validation_errors.append("输入与对话主题不一致")
        
        # 8. 清理输入
        cleaned_input = await self._clean_input_async(cleaned_input)
        
        # 9. 生成验证结果
        is_valid = len(validation_errors) == 0
        
        validation_result = InputValidationResult(
            is_valid=is_valid,
            cleaned_input=cleaned_input,
            validation_errors=validation_errors,
            original_input=user_input,
            metadata={
                "step": "complete_validation",
                "validation_steps": [
                    "basic_validation",
                    "length_check",
                    "required_fields_check",
                    "security_patterns_check",
                    "sql_injection_check",
                    "context_consistency_check",
                    "input_cleaning"
                ],
                "cleaning_applied": cleaned_input != user_input,
                "context_used": bool(context)
            }
        )
        
        return {"validation_result": validation_result}
    
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
        validation_result = exec_res.get("validation_result")
        
        if validation_result and validation_result.is_valid:
            # 验证通过，更新共享数据
            shared["validated_input"] = validation_result.cleaned_input
            shared["validation_metadata"] = validation_result.metadata
            shared["validation_passed"] = True
            return "default"
        else:
            # 验证失败，记录错误信息
            shared["validation_errors"] = validation_result.validation_errors if validation_result else []
            shared["validation_passed"] = False
            return "error"
    
    async def _extract_topic_async(self, text: str) -> Optional[str]:
        """异步提取主题"""
        # 简单的关键词提取
        keywords = ["天气", "新闻", "股票", "翻译", "计算", "时间", "日期"]
        for keyword in keywords:
            if keyword in text:
                return keyword
        return None
    
    async def _is_topic_consistent_async(self, current_topic: str, previous_topics: List[str]) -> bool:
        """异步检查主题一致性"""
        # 简单的主题一致性检查
        if not previous_topics:
            return True
        
        # 检查当前主题是否在之前的对话中出现过
        for topic in previous_topics[-3:]:  # 只检查最近3个话题
            if current_topic in topic or topic in current_topic:
                return True
        
        return False
    
    async def _clean_input_async(self, text: str) -> str:
        """异步清理输入"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除潜在的恶意内容
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除JavaScript代码
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除事件处理器
        text = re.sub(r'on\w+\s*=\s*["\']?[^"\']*["\']?', '', text, flags=re.IGNORECASE)
        
        return text