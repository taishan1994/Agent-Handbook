"""
内容策略节点 - 使用PocketFlow实现内容策略检查
"""

import asyncio
from typing import Dict, Any, Optional
from pocketflow import BaseNode, AsyncNode
from content_policy_enforcer import ContentPolicyEnforcer, PolicyEvaluation


class ContentPolicyNode(BaseNode):
    """
    内容策略节点（同步版本）
    
    功能：
    - 内容安全检查
    - 策略违规检测
    - 违规类型分类
    - 处理建议生成
    """
    
    def __init__(self, policy_enforcer: Optional[ContentPolicyEnforcer] = None):
        """
        初始化内容策略节点
        
        Args:
            policy_enforcer: 内容策略执行器实例
        """
        super().__init__()
        self.policy_enforcer = policy_enforcer or ContentPolicyEnforcer()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理：准备内容数据
        
        Args:
            shared: 共享数据字典
            
        Returns:
            处理后的数据
        """
        # 获取用户输入和上下文
        user_input = shared.get("user_input", "")
        context = shared.get("context", {})
        
        return {
            "user_input": user_input,
            "context": context,
            "original_shared": shared
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行：检查内容策略
        
        Args:
            prep_res: 预处理结果
            
        Returns:
            检查结果
        """
        user_input = prep_res.get("user_input", "")
        context = prep_res.get("context", {})
        
        print(f"DEBUG: ContentPolicyNode.exec called with input: {user_input}")
        
        try:
            # 执行内容策略检查 - 使用异步版本但同步调用
            # 由于这是一个同步方法，我们需要使用 asyncio.run 来调用异步的 evaluate_content
            policy_result = asyncio.run(self.policy_enforcer.evaluate_content(user_input, context))
            
            print(f"DEBUG: Policy result: {policy_result}")
            print(f"DEBUG: Is safe: {policy_result.is_safe}")
            
            return {
                "policy_result": policy_result,
                "check_passed": policy_result.is_safe
            }
            
        except Exception as e:
            # 如果检查失败，默认拒绝（安全策略）
            print(f"DEBUG: Content policy check failed with error: {e}")
            from content_policy_enforcer import ViolationType
            error_result = PolicyEvaluation(
                is_safe=False,
                violation_types=[ViolationType.ILLEGAL_ACTIVITY],  # 使用有效的违规类型
                severity="high",
                confidence=1.0,
                explanation=f"内容策略检查失败: {str(e)}",
                recommended_action="block",
                metadata={"error": str(e)}
            )
            
            return {
                "policy_result": error_result,
                "check_passed": False,
                "error": str(e)
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理：更新共享数据
        
        Args:
            shared: 共享数据字典
            prep_res: 预处理结果
            exec_res: 执行结果
            
        Returns:
            下一个节点名称
        """
        policy_result = exec_res.get("policy_result")
        check_passed = exec_res.get("check_passed", True)
        error = exec_res.get("error")
        
        print(f"DEBUG: ContentPolicyNode.post called with exec_res: {exec_res}")
        
        # 更新共享数据
        shared["policy_result"] = policy_result
        shared["policy_check_passed"] = check_passed
        shared["policy_check_error"] = error
        
        # 如果检查未通过，标记验证失败
        if not check_passed:
            shared["validation_passed"] = False
            if "validation_errors" not in shared:
                shared["validation_errors"] = []
            shared["validation_errors"].append(f"内容策略检查失败: {policy_result.explanation}")
        
        print(f"DEBUG: ContentPolicyNode.post returning shared: {shared}")
        return "default"


class AsyncContentPolicyNode(AsyncNode):
    """
    内容策略节点（异步版本）
    
    功能：
    - 异步内容安全检查
    - 策略违规检测
    - 违规类型分类
    - 处理建议生成
    """
    
    def __init__(self, policy_enforcer: Optional[ContentPolicyEnforcer] = None):
        """
        初始化异步内容策略节点
        
        Args:
            policy_enforcer: 内容策略执行器实例
        """
        super().__init__()
        self.policy_enforcer = policy_enforcer or ContentPolicyEnforcer()
    
    async def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理：准备内容数据
        
        Args:
            shared: 共享数据字典
            
        Returns:
            处理后的数据
        """
        # 获取用户输入和上下文
        user_input = shared.get("user_input", "")
        context = shared.get("context", {})
        
        return {
            "user_input": user_input,
            "context": context,
            "original_shared": shared
        }
    
    async def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行：异步检查内容策略
        
        Args:
            prep_res: 预处理结果
            
        Returns:
            检查结果
        """
        user_input = prep_res.get("user_input", "")
        context = prep_res.get("context", {})
        
        print(f"DEBUG: AsyncContentPolicyNode.exec called with input: {user_input}")
        
        try:
            # 异步执行内容策略检查
            policy_result = await self.policy_enforcer.evaluate_content(user_input, context)
            
            print(f"DEBUG: Async policy result: {policy_result}")
            print(f"DEBUG: Async is safe: {policy_result.is_safe}")
            
            return {
                "policy_result": policy_result,
                "check_passed": policy_result.is_safe
            }
            
        except Exception as e:
            # 如果检查失败，默认拒绝（安全策略）
            print(f"DEBUG: Async content policy check failed with error: {e}")
            from content_policy_enforcer import ViolationType
            error_result = PolicyEvaluation(
                is_safe=False,
                violation_types=[ViolationType.ILLEGAL_ACTIVITY],  # 使用有效的违规类型
                severity="high",
                confidence=1.0,
                explanation=f"内容策略检查失败: {str(e)}",
                recommended_action="block",
                metadata={"error": str(e)}
            )
            
            return {
                "policy_result": error_result,
                "check_passed": False,
                "error": str(e)
            }
    
    async def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理：更新共享数据
        
        Args:
            shared: 共享数据字典
            prep_res: 预处理结果
            exec_res: 执行结果
            
        Returns:
            下一个节点名称
        """
        policy_result = exec_res.get("policy_result")
        check_passed = exec_res.get("check_passed", True)
        error = exec_res.get("error")
        
        print(f"DEBUG: AsyncContentPolicyNode.post called with exec_res: {exec_res}")
        
        # 更新共享数据
        shared["policy_result"] = policy_result
        shared["policy_check_passed"] = check_passed
        shared["policy_check_error"] = error
        
        # 如果检查未通过，标记验证失败
        if not check_passed:
            shared["validation_passed"] = False
            if "validation_errors" not in shared:
                shared["validation_errors"] = []
            shared["validation_errors"].append(f"内容策略检查失败: {policy_result.explanation}")
        
        print(f"DEBUG: AsyncContentPolicyNode.post returning shared: {shared}")
        return "default"