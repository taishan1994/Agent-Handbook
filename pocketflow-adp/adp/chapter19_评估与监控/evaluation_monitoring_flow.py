import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from pocketflow import AsyncNode, AsyncFlow
from utils.utils import call_llm, call_llm_async, search_web_exa
import asyncio
import time
import json
from typing import Dict, List, Any, Optional

# 1. 评估响应准确度的节点
class ResponseAccuracyEvaluator(AsyncNode):
    async def prep_async(self, shared):
        return {
            "response": shared.get("response"),
            "expected": shared.get("expected"),
            "context": shared.get("context")
        }
    
    async def exec_async(self, prep_res):
        response = prep_res["response"]
        expected = prep_res["expected"]
        context = prep_res["context"]
        
        prompt = f"""
        请评估以下AI响应是否准确回答了问题。
        
        上下文: {context}
        预期内容: {expected}
        AI响应: {response}
        
        请给出1-5分的评分，并提供简短的评价理由。
        输出格式: {{"score": 评分, "reason": "评价理由"}}
        """
        
        try:
            result = await call_llm_async(prompt)
            return json.loads(result)
        except Exception as e:
            print(f"评估响应准确度时出错: {e}")
            return {"score": 0, "reason": "评估失败"}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["accuracy_result"] = exec_res
        return "accuracy_evaluated"

# 2. LLM交互监控器节点
class LLMInteractionMonitor(AsyncNode):
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.total_tokens = 0
        self.interactions = []
    
    async def prep_async(self, shared):
        return {
            "interaction_type": shared.get("interaction_type"),
            "prompt": shared.get("prompt"),
            "response": shared.get("response")
        }
    
    async def exec_async(self, prep_res):
        # 简单估算token数量（实际应用中应使用更准确的tokenizer）
        prompt_tokens = len(prep_res["prompt"].split()) // 4 * 3 if prep_res["prompt"] else 0  # 粗略估计
        response_tokens = len(prep_res["response"].split()) // 4 * 3 if prep_res["response"] else 0
        
        interaction_data = {
            "type": prep_res["interaction_type"],
            "timestamp": time.time(),
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": prompt_tokens + response_tokens
        }
        
        return interaction_data
    
    async def post_async(self, shared, prep_res, exec_res):
        # 更新监控数据
        self.total_tokens += exec_res["total_tokens"]
        self.interactions.append(exec_res)
        
        # 保存到shared中
        shared["monitoring_data"] = {
            "total_tokens": self.total_tokens,
            "interaction_count": len(self.interactions),
            "last_interaction": exec_res
        }
        
        return "monitored"

# 3. LLM-as-a-Judge法律调查评估节点
class LegalSurveyJudge(AsyncNode):
    # 法律调查质量的评分标准
    LEGAL_SURVEY_RUBRIC = {
        "relevance": "问题与法律主题的相关性（1-5分）",
        "precision": "问题表述的精确性和清晰度（1-5分）",
        "coverage": "问题对法律领域的覆盖程度（1-5分）",
        "neutrality": "问题的中立性和无偏见性（1-5分）",
        "specificity": "问题的具体性和可操作性（1-5分）"
    }
    
    async def prep_async(self, shared):
        return {
            "survey_question": shared.get("survey_question"),
            "legal_context": shared.get("legal_context")
        }
    
    async def exec_async(self, prep_res):
        survey_question = prep_res["survey_question"]
        legal_context = prep_res["legal_context"]
        
        prompt = f"""
        你是一位法律专家，请根据以下评分标准评估法律调查问题的质量。
        
        评分标准:
        {json.dumps(self.LEGAL_SURVEY_RUBRIC, ensure_ascii=False, indent=2)}
        
        法律背景: {legal_context}
        调查问题: {survey_question}
        
        请为每个标准给出1-5分的评分，并提供简短的评价理由。
        最后计算总分并给出综合评价。
        输出格式: {{"scores": {{标准1: 分数, ...}}, "reasons": {{标准1: "理由", ...}}, "total_score": 总分, "overall_evaluation": "综合评价"}}
        """
        
        try:
            result = await call_llm_async(prompt)
            return json.loads(result)
        except Exception as e:
            print(f"法律调查评估时出错: {e}")
            return {"scores": {}, "reasons": {}, "total_score": 0, "overall_evaluation": "评估失败"}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["legal_judge_result"] = exec_res
        # 根据总评分决定下一步操作
        if exec_res.get("total_score", 0) >= 20:
            return "high_quality"
        elif exec_res.get("total_score", 0) >= 15:
            return "medium_quality"
        else:
            return "low_quality"

# 4. 质量改进建议节点
class QualityImprovementAdvisor(AsyncNode):
    async def prep_async(self, shared):
        return {
            "legal_judge_result": shared.get("legal_judge_result"),
            "survey_question": shared.get("survey_question"),
            "legal_context": shared.get("legal_context")
        }
    
    async def exec_async(self, prep_res):
        judge_result = prep_res["legal_judge_result"]
        survey_question = prep_res["survey_question"]
        legal_context = prep_res["legal_context"]
        
        prompt = f"""
        根据以下法律调查问题的评估结果，请提供具体的改进建议。
        
        当前调查问题: {survey_question}
        法律背景: {legal_context}
        评估结果: {json.dumps(judge_result, ensure_ascii=False, indent=2)}
        
        请提供:
        1. 问题的主要不足
        2. 具体的改进建议
        3. 改进后的问题示例
        
        输出格式: {{"weaknesses": ["不足1", ...], "suggestions": ["建议1", ...], "improved_question": "改进后的问题"}}
        """
        
        try:
            result = await call_llm_async(prompt)
            return json.loads(result)
        except Exception as e:
            print(f"生成改进建议时出错: {e}")
            return {"weaknesses": [], "suggestions": [], "improved_question": survey_question}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["improvement_suggestions"] = exec_res
        return "improved"

# 评估与监控的完整流程
class EvaluationMonitoringFlow(AsyncFlow):
    def __init__(self):
        super().__init__()
        # 创建各个节点
        self.accuracy_evaluator = ResponseAccuracyEvaluator()
        self.interaction_monitor = LLMInteractionMonitor()
        self.legal_judge = LegalSurveyJudge()
        self.improvement_advisor = QualityImprovementAdvisor()
        
        # 构建流程
        self.start(self.legal_judge)  # 从法律调查评估开始
        self.legal_judge - "low_quality" >> self.improvement_advisor  # 低质量时进行改进
        self.legal_judge - "medium_quality" >> self.improvement_advisor  # 中等质量时也可以改进
        self.legal_judge - "high_quality" >> self.interaction_monitor  # 高质量时直接监控
        self.improvement_advisor >> self.interaction_monitor  # 改进后进行监控
    
    async def run_evaluation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行评估与监控流程
        
        Args:
            inputs: 包含评估所需的输入数据
                    - survey_question: 调查问题
                    - legal_context: 法律背景
                    - response: AI响应（可选）
                    - expected: 预期内容（可选）
                    - context: 上下文（可选）
                    - interaction_type: 交互类型
        
        Returns:
            包含所有评估结果的字典
        """
        shared = inputs.copy()
        
        # 确保交互类型被设置
        if "interaction_type" not in shared:
            shared["interaction_type"] = "legal_survey_evaluation"
        
        # 运行流程
        await self.run_async(shared)
        
        return shared

# 示例使用函数
async def example_usage():
    # 创建流程
    flow = EvaluationMonitoringFlow()
    
    # 准备输入数据
    inputs = {
        "survey_question": "在知识产权侵权案件中，如何确定损害赔偿金额？",
        "legal_context": "知识产权法，特别是专利法和商标法领域，涉及侵权赔偿计算方法",
        "interaction_type": "legal_research"
    }
    
    # 运行评估
    results = await flow.run_evaluation(inputs)
    
    # 打印结果
    print("\n评估结果摘要:")
    if "legal_judge_result" in results:
        judge_result = results["legal_judge_result"]
        print(f"法律调查评分: {judge_result.get('total_score', 0)}/25")
        print(f"综合评价: {judge_result.get('overall_evaluation', 'N/A')}")
    
    if "improvement_suggestions" in results:
        print("\n改进建议:")
        suggestions = results["improvement_suggestions"]
        print(f"主要不足: {', '.join(suggestions.get('weaknesses', []))}")
        print(f"改进后的问题: {suggestions.get('improved_question', 'N/A')}")
    
    if "monitoring_data" in results:
        monitoring = results["monitoring_data"]
        print("\n监控数据:")
        print(f"总token数: {monitoring.get('total_tokens', 0)}")
        print(f"交互次数: {monitoring.get('interaction_count', 0)}")

# 直接运行示例
if __name__ == "__main__":
    asyncio.run(example_usage())
