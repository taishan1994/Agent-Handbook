"""
输入验证节点 - 使用PocketFlow实现输入验证和清理
"""

import json
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from pocketflow import BaseNode


class InputValidationResult(BaseModel):
    """输入验证结果模型"""
    is_valid: bool = Field(description="输入是否有效")
    cleaned_input: str = Field(description="清理后的输入")
    validation_errors: List[str] = Field(description="验证错误列表")
    original_input: str = Field(description="原始输入")
    metadata: Dict[str, Any] = Field(description="验证元数据")


class InputValidationNode(BaseNode):
    """
    输入验证节点
    
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
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
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
                current_topic = self._extract_topic(cleaned_input)
                if current_topic and not self._is_topic_consistent(current_topic, previous_topics):
                    validation_errors.append("输入与对话主题不一致")
        
        # 8. 清理输入
        cleaned_input = self._clean_input(cleaned_input)
        
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
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理：更新共享数据
        
        Args:
            exec_res: 执行结果
            shared: 共享数据字典
            
        Returns:
            下一步动作（始终返回"next"，验证结果在共享数据中）
        """
        validation_result = exec_res.get("validation_result")
        
        if validation_result.is_valid:
            # 更新共享数据，使用清理后的输入
            shared["validated_input"] = validation_result.cleaned_input
            shared["validation_passed"] = True
            shared["validation_metadata"] = validation_result.metadata
        else:
            # 验证失败，添加错误信息
            shared["validation_passed"] = False
            shared["validation_errors"] = validation_result.validation_errors
            shared["validation_result"] = validation_result
        
        return "default"
    
    def _clean_input(self, input_text: str) -> str:
        """
        清理输入文本
        
        Args:
            input_text: 输入文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', input_text.strip())
        
        # 移除控制字符
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        # 标准化引号
        cleaned = cleaned.replace('"', '"').replace('"', '"')
        cleaned = cleaned.replace(''', "'").replace(''', "'")
        
        # 移除零宽字符
        cleaned = re.sub(r'[\u200b-\u200d\ufeff]', '', cleaned)
        
        return cleaned
    
    def _extract_topic(self, text: str) -> Optional[str]:
        """
        提取文本主题（简化版）
        
        Args:
            text: 输入文本
            
        Returns:
            主题关键词
        """
        # 简单的关键词提取
        keywords = ["天气", "新闻", "体育", "科技", "娱乐", "政治", "经济", "健康"]
        for keyword in keywords:
            if keyword in text:
                return keyword
        return None
    
    def _is_topic_consistent(self, current_topic: str, previous_topics: List[str]) -> bool:
        """
        检查主题是否一致
        
        Args:
            current_topic: 当前主题
            previous_topics: 之前的主题列表
            
        Returns:
            是否一致
        """
        if not previous_topics:
            return True
        
        # 简单的主题一致性检查
        last_topic = previous_topics[-1]
        return current_topic == last_topic or current_topic in previous_topics


# 测试函数
async def test_input_validation_node():
    """测试输入验证节点"""
    from pocketflow import Flow
    
    # 创建验证节点
    validation_node = InputValidationNode(
        max_length=200,
        allow_special_chars=False,
        required_fields=["question", "context"],
        forbidden_patterns=[r'<script.*?>.*?</script>']
    )
    
    # 测试用例
    test_cases = [
        {
            "user_input": "今天天气怎么样？",
            "context": {}
        },
        {
            "user_input": "",  # 空输入
            "context": {}
        },
        {
            "user_input": "<script>alert('xss')</script>这是一个测试",
            "context": {}
        },
        {
            "user_input": "SELECT * FROM users WHERE id = 1 OR 1=1",
            "context": {}
        },
        {
            "user_input": "A" * 300,  # 超长输入
            "context": {}
        }
    ]
    
    print("=== 输入验证节点测试 ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print(f"原始输入: {test_case['user_input']}")
        
        # 创建临时共享数据
        shared_data = test_case.copy()
        
        # 执行节点
        result = validation_node(shared_data)
        
        if result.get("validation_passed"):
            print("✅ 验证通过")
            print(f"清理后输入: {result.get('validated_input')}")
        else:
            print("❌ 验证失败")
            print(f"错误: {result.get('validation_errors')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_input_validation_node())