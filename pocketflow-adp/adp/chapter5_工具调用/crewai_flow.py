import sys
import os
import asyncio
import json
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
sys.path.append(os.path.dirname(__file__))  # 添加当前目录，以便导入 pocketflow

from utils import call_llm_async
from pocketflow import AsyncNode, AsyncFlow


class FinancialTool:
    """财务分析工具"""
    
    def __init__(self):
        self.name = "Stock Price Lookup Tool"
        self.description = "获取给定股票代码符号的最新模拟股票价格。以浮点数形式返回价格。"
    
    async def execute(self, ticker: str) -> float:
        """执行股票价格查询"""
        print(f"\n--- 🛠️ 工具调用：get_stock_price，代码为 '{ticker}' ---")
        
        simulated_prices = {
            "AAPL": 178.15,
            "GOOGL": 1750.30,
            "MSFT": 425.50,
        }
        
        price = simulated_prices.get(ticker.upper())
        if price is not None:
            print(f"--- 工具结果：{ticker.upper()} 的股票价格是 ${price} ---")
            return price
        else:
            error_msg = f"未找到代码 '{ticker.upper()}' 的模拟价格。"
            print(f"--- 工具错误：{error_msg} ---")
            raise ValueError(error_msg)


class FinancialAnalystNode(AsyncNode):
    """财务分析师节点"""
    
    def __init__(self, tool: FinancialTool):
        super().__init__(max_retries=1, wait=0)
        self.tool = tool
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备分析师节点的输入"""
        task_description = shared_state.get("task_description", "")
        
        prompt = f"""
        你是一位高级财务分析师，擅长使用数据源查找股票信息。你提供清晰、直接的答案。
        
        任务描述：{task_description}
        
        请分析任务并决定是否需要使用工具来获取股票价格信息。
        
        如果需要使用工具，请以JSON格式返回工具调用，格式如下：
        {{
            "tool_name": "Stock Price Lookup Tool",
            "parameters": {{
                "ticker": "股票代码"
            }}
        }}
        
        如果不需要使用工具，请直接提供你的分析结果。
        """
        
        return {"prompt": prompt}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析师节点"""
        prompt = prep_result.get("prompt", "")
        response = await call_llm_async(prompt)
        
        # 尝试解析JSON
        try:
            # 检查响应是否包含JSON格式的工具调用
            if "{" in response and "}" in response:
                # 尝试提取JSON部分
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                tool_call = json.loads(json_str)
                return {"tool_call": tool_call, "raw_response": response, "is_tool_call": True}
            else:
                # 不是JSON格式，直接回答
                return {"tool_call": None, "raw_response": response, "is_tool_call": False}
        except json.JSONDecodeError:
            # JSON解析失败，直接回答
            return {"tool_call": None, "raw_response": response, "is_tool_call": False}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理分析师节点结果"""
        shared_state["tool_call"] = exec_result.get("tool_call")
        shared_state["raw_response"] = exec_result.get("raw_response")
        shared_state["is_tool_call"] = exec_result.get("is_tool_call", False)
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        
        # 根据是否需要调用工具返回不同的action
        is_tool_call = shared_state.get("is_tool_call", False)
        return "use_tool" if is_tool_call else "direct_answer"


class ToolExecutorNode(AsyncNode):
    """工具执行节点"""
    
    def __init__(self, tool: FinancialTool):
        super().__init__(max_retries=1, wait=0)
        self.tool = tool
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备执行器节点的输入"""
        tool_call = shared_state.get("tool_call", {})
        parameters = tool_call.get("parameters", {})
        
        return {
            "ticker": parameters.get("ticker", "")
        }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        ticker = prep_result.get("ticker", "")
        
        try:
            # 执行工具
            result = await self.tool.execute(ticker)
            return {"result": result, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理执行器节点结果"""
        shared_state["tool_result"] = exec_result.get("result")
        shared_state["tool_error"] = exec_result.get("error")
        shared_state["tool_success"] = exec_result.get("success", False)
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        return "generate_response"


class ResponseGeneratorNode(AsyncNode):
    """响应生成节点"""
    
    def __init__(self):
        super().__init__(max_retries=1, wait=0)
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备生成器节点的输入"""
        task_description = shared_state.get("task_description", "")
        tool_result = shared_state.get("tool_result", "")
        tool_error = shared_state.get("tool_error", "")
        raw_response = shared_state.get("raw_response", "")
        is_tool_call = shared_state.get("is_tool_call", False)
        
        if is_tool_call:
            # 使用工具结果生成响应
            if tool_error:
                prompt = f"""
                任务描述：{task_description}
                
                工具调用出错：{tool_error}
                
                作为一名高级财务分析师，请向用户解释出现了什么问题，并提供一个有用的回答。
                """
            else:
                prompt = f"""
                任务描述：{task_description}
                
                工具调用结果：股票价格为 ${tool_result}
                
                作为一名高级财务分析师，请基于工具调用结果，提供一个清晰、有用的回答给用户。
                请确保回答符合预期的输出格式。
                """
        else:
            # 直接使用原始响应
            prompt = f"""
            任务描述：{task_description}
            
            作为一名高级财务分析师，请提供一个清晰、有用的回答给用户。
            
            参考回答：{raw_response}
            """
        
        return {"prompt": prompt}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行生成器节点"""
        prompt = prep_result.get("prompt", "")
        response = await call_llm_async(prompt)
        return {"response": response}
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理生成器节点结果"""
        shared_state["final_response"] = exec_result.get("response", "")
        return shared_state
    
    async def _run_async(self, shared_state):
        """重写_run_async方法以返回字符串action"""
        p = await self.prep_async(shared_state)
        e = await self._exec(p)
        await self.post_async(shared_state, p, e)
        return "end"


class FinancialAnalysisFlow(AsyncFlow):
    """财务分析流程"""
    
    def __init__(self, tool: FinancialTool):
        # 创建节点
        self.analyst = FinancialAnalystNode(tool)
        self.executor = ToolExecutorNode(tool)
        self.generator = ResponseGeneratorNode()
        
        # 设置流程
        super().__init__(start=self.analyst)
        
        # 定义节点之间的转换
        self.analyst.next(self.executor, action="use_tool")  # 如果需要使用工具
        self.analyst.next(self.generator, action="direct_answer")  # 如果直接回答
        self.executor.next(self.generator, action="generate_response")  # 工具执行后生成响应
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备流程输入"""
        return shared_state
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理流程结果"""
        return shared_state
    
    async def run(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """运行财务分析流程"""
        # 运行流程
        result = await self._run_async(shared_state)
        
        return result


# 创建工具实例
financial_tool = FinancialTool()

# 创建流程实例
financial_analysis_flow = FinancialAnalysisFlow(financial_tool)