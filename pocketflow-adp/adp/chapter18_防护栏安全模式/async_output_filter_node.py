"""
异步输出过滤节点 - 使用PocketFlow实现异步输出内容过滤和后处理
"""

import json
import re
import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pocketflow import AsyncNode

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


class AsyncOutputFilterNode(AsyncNode):
    """
    异步输出过滤节点
    
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
    
    async def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
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
    
    async def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
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
        filtered_output = await self._basic_cleaning_async(filtered_output)
        
        # 2. 个人信息过滤
        if self.enable_pii_filtering:
            filtered_output, removed_pii = await self._filter_pii_async(filtered_output)
            removed_content.extend(removed_pii)
        
        # 3. 品牌安全检查
        if self.enable_brand_safety:
            _, brand_warnings = await self._check_brand_safety_async(filtered_output)
            warnings.extend(brand_warnings)
            # 如果有品牌安全警告，添加到移除内容中
            removed_content.extend([f"[品牌安全] {warning}" for warning in brand_warnings])
        
        # 4. 毒性检测（异步执行）
        if self.enable_toxicity_check:
            # 使用异步LLM调用进行毒性检测
            try:
                toxicity_result = await self._check_toxicity_async(filtered_output)
                if not toxicity_result.get("is_safe", True):
                    warnings.extend(toxicity_result.get("issues_found", []))
                    confidence *= 0.8
            except Exception as e:
                warnings.append(f"毒性检测失败: {str(e)}")
        
        # 5. 事实性验证
        if self.enable_fact_checking:
            # 异步事实检查
            try:
                fact_result = await self._check_facts_async(filtered_output, context)
                if not fact_result.get("is_factual", True):
                    warnings.extend(fact_result.get("issues", []))
            except Exception as e:
                warnings.append(f"事实验证失败: {str(e)}")
        
        # 6. 风格一致性检查
        style_check = await self._check_style_consistency_async(filtered_output, context)
        if not style_check.get("is_consistent", True):
            warnings.extend(style_check.get("issues", []))
        
        # 7. 最终安全评估
        is_safe = len(warnings) == 0 or all("品牌安全" in warning for warning in warnings)
        
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
                    "style_consistency_check"
                ],
                "toxicity_check_enabled": self.enable_toxicity_check,
                "brand_safety_enabled": self.enable_brand_safety,
                "pii_filtering_enabled": self.enable_pii_filtering,
                "fact_checking_enabled": self.enable_fact_checking
            }
        )
        
        return {"filter_result": filter_result}
    
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
        filter_result = exec_res.get("filter_result")
        
        if filter_result and filter_result.is_safe:
            # 过滤通过，更新共享数据
            shared["filtered_output"] = filter_result.filtered_output
            shared["output_filter_metadata"] = filter_result.metadata
            shared["output_filter_passed"] = True
            return "default"
        else:
            # 过滤失败，记录错误信息
            shared["output_filter_errors"] = filter_result.warnings if filter_result else []
            shared["output_filter_passed"] = False
            return "error"
    
    async def _basic_cleaning_async(self, text: str) -> str:
        """异步基本清理"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除脚本标签
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除样式标签
        text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text
    
    async def _filter_pii_async(self, text: str) -> tuple[str, List[str]]:
        """异步过滤个人信息"""
        removed_content = []
        
        for pattern in self.pii_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 用占位符替换匹配的内容
                text = re.sub(pattern, '[PII_REMOVED]', text)
                removed_content.extend(matches)
        
        return text, removed_content
    
    async def _check_brand_safety_async(self, text: str) -> tuple[bool, List[str]]:
        """异步品牌安全检查"""
        warnings = []
        
        for keyword in self.brand_keywords:
            if keyword.lower() in text.lower():
                warnings.append(f"检测到品牌敏感词: {keyword}")
        
        # 检查负面品牌提及
        negative_patterns = [
            r'垃圾品牌',
            r'差劲的产品',
            r'不要买',
            r'骗局',
            r'欺诈'
        ]
        
        for pattern in negative_patterns:
            if re.search(pattern, text):
                warnings.append(f"检测到负面品牌内容: {pattern}")
        
        return len(warnings) == 0, warnings
    
    async def _check_toxicity_async(self, text: str) -> Dict[str, Any]:
        """异步毒性检测"""
        try:
            # 使用LLM进行毒性检测
            prompt = self.toxicity_prompt.format(output_content=text)
            
            response = await call_llm_async(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=500,
                temperature=0.1
            )
            
            # 解析LLM响应
            if response:
                try:
                    # 尝试解析JSON响应
                    result = json.loads(response)
                    return result
                except json.JSONDecodeError:
                    # 如果解析失败，使用简单的关键词检测
                    toxic_words = ["愚蠢", "白痴", "垃圾", "废物", "去死", "很差", "差劲"]
                    issues = []
                    for word in toxic_words:
                        if word in text.lower():
                            issues.append(f"检测到毒性词汇: {word}")
                    
                    return {
                        "is_safe": len(issues) == 0,
                        "toxicity_score": len(issues) * 0.3,
                        "issues_found": issues,
                        "explanation": "基于关键词的毒性检测",
                        "recommended_action": "allow" if len(issues) == 0 else "modify"
                    }
            
            # 如果LLM调用失败，使用备用检测
            return await self._fallback_toxicity_check_async(text)
            
        except Exception as e:
            # 如果所有方法都失败，使用备用检测
            return await self._fallback_toxicity_check_async(text)
    
    async def _fallback_toxicity_check_async(self, text: str) -> Dict[str, Any]:
        """异步备用毒性检测"""
        toxic_words = ["愚蠢", "白痴", "垃圾", "废物", "去死", "很差", "差劲"]
        issues = []
        toxicity_score = 0.0
        
        for word in toxic_words:
            if word in text.lower():
                toxicity_score += 0.3
                issues.append(f"检测到毒性词汇: {word}")
        
        return {
            "is_safe": toxicity_score < self.toxicity_threshold,
            "toxicity_score": min(toxicity_score, 1.0),
            "issues_found": issues,
            "explanation": "基于关键词的毒性检测",
            "recommended_action": "allow" if toxicity_score < self.toxicity_threshold else "modify"
        }
    
    async def _check_facts_async(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """异步事实检查"""
        # 简化的异步事实检查
        # 这里可以集成更复杂的事实检查服务
        
        # 检查明显的虚假声明
        suspicious_patterns = [
            r'地球是平的',
            r'疫苗会导致自闭症',
            r'5G会传播病毒'
        ]
        
        issues = []
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"检测到可疑声明: {pattern}")
        
        return {
            "is_factual": len(issues) == 0,
            "issues": issues,
            "confidence": 0.8 if len(issues) == 0 else 0.3
        }
    
    async def _check_style_consistency_async(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """异步风格一致性检查"""
        # 简化的风格一致性检查
        issues = []
        
        # 检查语气是否一致
        if "专业" in str(context.get("style", "")):
            # 检查是否使用了过于随意的语言
            casual_words = ["哈哈", "嘿嘿", "哎呀", "哇"]
            for word in casual_words:
                if word in text:
                    issues.append(f"检测到非专业用语: {word}")
        
        return {
            "is_consistent": len(issues) == 0,
            "issues": issues
        }