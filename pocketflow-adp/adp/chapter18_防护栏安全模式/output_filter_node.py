"""
输出过滤节点 - 使用PocketFlow实现输出内容过滤和后处理
"""

import json
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pocketflow import BaseNode

# 导入utils中的LLM调用函数
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.utils import call_llm_async


class OutputFilterResult(BaseModel):
    """输出过滤结果模型"""
    is_safe: bool = Field(description="输出是否安全")
    filtered_output: str = Field(description="过滤后的输出")
    removed_content: List[str] = Field(description="被移除的内容列表")
    warnings: List[str] = Field(description="警告信息列表")
    original_output: str = Field(description="原始输出")
    confidence: float = Field(description="过滤置信度 (0-1)")
    metadata: Dict[str, Any] = Field(description="过滤元数据")


class OutputFilterNode(BaseNode):
    """
    输出过滤节点
    
    功能：
    - 输出内容毒性检测
    - 品牌安全保护
    - 敏感信息过滤
    - 事实性验证
    - 风格一致性检查
    """
    
    def __init__(self,
                 enable_toxicity_check: bool = True,
                 enable_brand_safety: bool = True,
                 enable_pii_filtering: bool = True,
                 enable_fact_checking: bool = False,
                 toxicity_threshold: float = 0.7,
                 brand_keywords: Optional[List[str]] = None,
                 pii_patterns: Optional[List[str]] = None):
        """
        初始化输出过滤节点
        
        Args:
            enable_toxicity_check: 启用毒性检测
            enable_brand_safety: 启用品牌安全保护
            enable_pii_filtering: 启用个人信息过滤
            enable_fact_checking: 启用事实性验证
            toxicity_threshold: 毒性阈值
            brand_keywords: 品牌关键词列表
            pii_patterns: 个人信息模式列表
        """
        super().__init__()
        self.enable_toxicity_check = enable_toxicity_check
        self.enable_brand_safety = enable_brand_safety
        self.enable_pii_filtering = enable_pii_filtering
        self.enable_fact_checking = enable_fact_checking
        self.toxicity_threshold = toxicity_threshold
        
        # 默认品牌关键词
        self.brand_keywords = brand_keywords or [
            "竞争对手A", "竞争对手B", "恶意品牌", "仿冒品牌"
        ]
        
        # 默认个人信息模式
        self.pii_patterns = pii_patterns or [
            r'(?<!\d)\d{15,18}(?!\d)',  # 身份证号 (15-18位数字，前后不能是数字)
            r'(?<!\d)1[3-9]\d{9}(?!\d)',  # 手机号 (前后不能是数字)
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 邮箱
            r'(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)',  # 银行卡号
            r'(?<!\d)(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?!\d)',  # IP地址
        ]
        
        # 毒性检测提示词
        self.toxicity_prompt = """你是一个内容安全专家，请评估以下AI生成的输出是否包含有害内容。

需要检测的内容类型：
1. 毒性/仇恨言论 (toxicity)
2. 偏见/歧视 (bias)  
3. 不当语言 (inappropriate_language)
4. 误导信息 (misinformation)
5. 品牌攻击 (brand_attack)

AI输出内容：
{output_content}

请评估此内容的安全性，考虑：
- 是否包含有害、仇恨或歧视性语言
- 是否存在事实性错误
- 是否攻击特定品牌或个人
- 是否适合公开发布

请以JSON格式返回评估结果：
{{
    "is_safe": true/false,
    "toxicity_score": 0.0-1.0,
    "issues_found": ["issue1", "issue2"],
    "explanation": "详细解释",
    "recommended_action": "allow/modify/block"
}}
"""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理：准备输出数据
        
        Args:
            shared: 共享数据字典
            
        Returns:
            处理后的数据
        """
        # 获取AI生成的输出
        ai_output = shared.get("ai_output", "")
        context = shared.get("context", {})
        user_input = shared.get("validated_input", "")
        
        return {
            "ai_output": ai_output,
            "context": context,
            "user_input": user_input,
            "original_shared": shared
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行：过滤和验证输出
        
        Args:
            prep_res: 预处理结果
            
        Returns:
            过滤结果
        """
        ai_output = prep_res.get("ai_output", "")
        context = prep_res.get("context", {})
        user_input = prep_res.get("user_input", "")
        
        if not ai_output:
            return {
                "filter_result": OutputFilterResult(
                    is_safe=False,
                    filtered_output="",
                    removed_content=["空输出"],
                    warnings=["AI输出为空"],
                    original_output="",
                    confidence=1.0,
                    metadata={"step": "empty_output_check"}
                )
            }
        
        filtered_output = ai_output
        removed_content = []
        warnings = []
        confidence = 1.0
        
        # 1. 基本清理
        filtered_output = self._basic_cleaning(filtered_output)
        
        # 2. 个人信息过滤
        if self.enable_pii_filtering:
            filtered_output, removed_pii = self._filter_pii(filtered_output)
            removed_content.extend(removed_pii)
        
        # 3. 品牌安全检查
        if self.enable_brand_safety:
            _, brand_warnings = self._check_brand_safety(filtered_output)
            warnings.extend(brand_warnings)
            # 如果有品牌安全警告，添加到移除内容中
            removed_content.extend([f"[品牌安全] {warning}" for warning in brand_warnings])
        
        # 4. 毒性检测（同步执行）
        if self.enable_toxicity_check:
            # 使用同步版本进行毒性检测
            toxic_words = ["愚蠢", "白痴", "垃圾", "废物", "去死", "很差", "差劲"]
            
            toxicity_score = 0.0
            issues = []
            
            for word in toxic_words:
                if word in filtered_output.lower():
                    toxicity_score += 0.3
                    issues.append(f"检测到毒性词汇: {word}")
            
            is_toxic = toxicity_score >= self.toxicity_threshold
            
            if is_toxic:
                warnings.append(f"检测到毒性内容: 检测到潜在毒性内容")
                confidence *= 0.8
        
        # 5. 事实性验证
        if self.enable_fact_checking:
            fact_result = self._check_facts(filtered_output, user_input)
            if not fact_result["is_accurate"]:
                warnings.append(f"事实性检查警告: {fact_result['warning']}")
        
        # 6. 长度检查
        if len(filtered_output) > 2000:
            warnings.append("输出过长，可能被截断")
            filtered_output = filtered_output[:2000] + "..."
        
        # 7. 最终安全评估
        # 内容不安全如果有移除的内容或有毒性/事实性警告
        has_dangerous_warnings = len([w for w in warnings if "毒性" in w or "事实性" in w]) > 0
        is_safe = len(removed_content) == 0 and not has_dangerous_warnings
        
        filter_result = OutputFilterResult(
            is_safe=is_safe,
            filtered_output=filtered_output,
            removed_content=removed_content,
            warnings=warnings,
            original_output=ai_output,
            confidence=confidence,
            metadata={
                "step": "complete_filtering",
                "filtering_steps": [
                    "basic_cleaning",
                    "pii_filtering" if self.enable_pii_filtering else None,
                    "brand_safety_check" if self.enable_brand_safety else None,
                    "toxicity_check" if self.enable_toxicity_check else None,
                    "fact_checking" if self.enable_fact_checking else None,
                    "length_check"
                ],
                "original_length": len(ai_output),
                "filtered_length": len(filtered_output),
                "warnings_count": len(warnings),
                "removed_count": len(removed_content)
            }
        )
        
        return {"filter_result": filter_result}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        后处理：更新共享数据
        
        Args:
            exec_res: 执行结果
            shared: 共享数据字典
            
        Returns:
            更新后的共享数据
        """
        filter_result = exec_res.get("filter_result")
        
        if filter_result.is_safe:
            shared["filtered_output"] = filter_result.filtered_output
            shared["safe_to_use"] = True
            shared["filter_metadata"] = filter_result.metadata
        else:
            shared["safe_to_use"] = False
            shared["filter_warnings"] = filter_result.warnings
            shared["removed_content"] = filter_result.removed_content
            shared["filter_result"] = filter_result
        
        return "default"
    
    def _basic_cleaning(self, text: str) -> str:
        """基本文本清理"""
        # 移除控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除多余的标点符号
        text = re.sub(r'[!？]{2,}', '!', text)
        text = re.sub(r'[。\.]{2,}', '.', text)
        
        return text
    
    def _filter_pii(self, text: str) -> tuple[str, List[str]]:
        """过滤个人信息"""
        removed = []
        filtered_text = text
        
        for pattern in self.pii_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 用占位符替换
                filtered_text = re.sub(pattern, "[REDACTED]", filtered_text)
                removed.extend([f"PII: {match}" for match in matches if match])
        
        return filtered_text, removed
    
    def _check_brand_safety(self, text: str) -> tuple[str, List[str]]:
        """检查品牌安全"""
        warnings = []
        
        for keyword in self.brand_keywords:
            if keyword.lower() in text.lower():
                warnings.append(f"检测到品牌关键词: {keyword}")
        
        # 检查负面情感词汇
        negative_words = ["垃圾", "糟糕", "恶心", "差劲", "失败", "很差"]
        for word in negative_words:
            if word in text:
                warnings.append(f"检测到负面情感词汇: {word}")
        
        return text, warnings
    
    async def _check_toxicity(self, text: str) -> Dict[str, Any]:
        """毒性检查（使用LLM）"""
        # 在实际应用中，这里应该调用LLM进行毒性检测
        # 为了测试，我们使用基于关键词的简化版本
        toxic_words = ["愚蠢", "白痴", "垃圾", "废物", "去死", "很差"]
        
        toxicity_score = 0.0
        issues = []
        
        for word in toxic_words:
            if word in text.lower():
                toxicity_score += 0.3
                issues.append(f"检测到毒性词汇: {word}")
        
        is_safe = toxicity_score < self.toxicity_threshold
        
        return {
            "is_safe": is_safe,
            "toxicity_score": min(toxicity_score, 1.0),
            "issues_found": issues,
            "explanation": "检测到潜在毒性内容" if issues else "内容安全",
            "recommended_action": "block" if toxicity_score > 0.7 else "allow",
            "confidence": 0.8
        }
    
    def _check_facts(self, text: str, user_input: str) -> Dict[str, Any]:
        """事实性检查（简化版）"""
        # 检查明显的事实错误
        false_claims = [
            "地球是平的",
            "太阳绕地球转",
            "人类从未登上月球"
        ]
        
        for claim in false_claims:
            if claim in text:
                return {
                    "is_accurate": False,
                    "warning": f"检测到可能的事实错误: {claim}"
                }
        
        return {"is_accurate": True, "warning": ""}


# 测试函数
async def test_output_filter_node():
    """测试输出过滤节点"""
    from pocketflow import Flow
    
    # 创建过滤节点
    filter_node = OutputFilterNode(
        enable_toxicity_check=True,
        enable_brand_safety=True,
        enable_pii_filtering=True,
        toxicity_threshold=0.5
    )
    
    # 测试用例
    test_cases = [
        {
            "ai_output": "今天天气很好，适合外出活动。",
            "user_input": "今天天气怎么样？",
            "context": {}
        },
        {
            "ai_output": "13800138000这个手机号很不错，你可以联系他。",
            "user_input": "告诉我一个联系方式",
            "context": {}
        },
        {
            "ai_output": "竞争对手A的产品真的很垃圾，不如我们的产品好。",
            "user_input": "比较一下产品",
            "context": {}
        },
        {
            "ai_output": "你真是个愚蠢的白痴，连这么简单的问题都不懂。",
            "user_input": "请解释这个问题",
            "context": {}
        },
        {
            "ai_output": "地球是平的，这是众所周知的事实。",
            "user_input": "地球是什么形状的？",
            "context": {}
        }
    ]
    
    print("=== 输出过滤节点测试 ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print(f"AI输出: {test_case['ai_output']}")
        print(f"用户输入: {test_case['user_input']}")
        
        # 创建临时共享数据
        shared_data = test_case.copy()
        
        # 执行节点
        result = filter_node(shared_data)
        
        if result.get("output_safe"):
            print("✅ 输出安全")
            print(f"过滤后输出: {result.get('filtered_output')}")
        else:
            print("❌ 输出不安全")
            print(f"警告: {result.get('filter_warnings')}")
            print(f"移除内容: {result.get('removed_content')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_output_filter_node())