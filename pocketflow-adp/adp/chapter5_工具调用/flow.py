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


class Tool:
    """工具基类"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def to_dict(self) -> Dict[str, Any]:
        """将工具转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class SearchInformationTool(Tool):
    """信息搜索工具"""
    
    def __init__(self):
        parameters = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的信息查询"
                }
            },
            "required": ["query"]
        }
        super().__init__(
            name="search_information",
            description="提供有关给定主题的事实信息。使用此工具查找诸如'法国首都'或'伦敦的天气？'等短语的答案。",
            parameters=parameters
        )
    
    async def execute(self, query: str) -> str:
        """执行搜索操作"""
        print(f"\n--- 🛠️ 工具调用：search_information，查询：'{query}' ---")
        
        # 使用预定义结果字典模拟搜索工具
        simulated_results = {
            "weather in london": "伦敦目前多云，温度为 15°C。",
            "capital of france": "法国的首都是巴黎。",
            "population of earth": "地球的估计人口约为 80 亿人。",
            "tallest mountain": "珠穆朗玛峰是海拔最高的山峰。",
            "default": f"'{query}' 的模拟搜索结果：未找到特定信息，但该主题似乎很有趣。"
        }
        
        result = simulated_results.get(query.lower(), simulated_results["default"])
        print(f"--- 工具结果：{result} ---")
        return result


class StockPriceTool(Tool):
    """股票价格查询工具"""
    
    def __init__(self):
        parameters = {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "股票代码符号"
                }
            },
            "required": ["ticker"]
        }
        super().__init__(
            name="get_stock_price",
            description="获取给定股票代码符号的最新模拟股票价格。以浮点数形式返回价格。",
            parameters=parameters
        )
    
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


class ToolCallParserNode(AsyncNode):
    """工具调用解析节点"""
    
    def __init__(self, tools: List[Tool]):
        super().__init__(max_retries=1, wait=0)
        self.tools = tools
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备解析器节点的输入"""
        user_query = shared_state.get("user_input", shared_state.get("user_query", ""))
        
        # 构建工具描述
        tools_description = "\n".join([
            f"- {tool.name}: {tool.description}" 
            for tool in self.tools
        ])
        
        # 构建工具参数描述
        tools_parameters = {
            tool.name: tool.parameters 
            for tool in self.tools
        }
        
        prompt = f"""
        你是一个有用的助手。你需要分析用户的查询，并决定是否需要使用工具来回答。
        
        可用工具：
        {tools_description}
        
        如果查询需要使用工具，请以JSON格式返回工具调用，格式如下：
        {{
            "tool_name": "工具名称",
            "parameters": {{
                "参数名": "参数值"
            }}
        }}
        
        如果查询不需要使用工具，请直接回答用户的问题。
        
        用户查询：{user_query}
        """
        
        return {
            "prompt": prompt,
            "tools_parameters": json.dumps(tools_parameters, indent=2)
        }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行解析器节点"""
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
        """后处理解析器节点结果"""
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
    
    def __init__(self, tools: List[Tool]):
        super().__init__(max_retries=1, wait=0)
        self.tools = {tool.name: tool for tool in tools}
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备执行器节点的输入"""
        tool_call = shared_state.get("tool_call", {})
        tool_name = tool_call.get("tool_name", "")
        parameters = tool_call.get("parameters", {})
        
        return {
            "tool_name": tool_name,
            "parameters": parameters
        }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        tool_name = prep_result.get("tool_name", "")
        parameters = prep_result.get("parameters", {})
        
        if tool_name not in self.tools:
            return {"error": f"未知工具: {tool_name}"}
        
        tool = self.tools[tool_name]
        
        try:
            # 执行工具
            if tool_name == "search_information":
                result = await tool.execute(parameters.get("query", ""))
            elif tool_name == "get_stock_price":
                result = await tool.execute(parameters.get("ticker", ""))
            else:
                # 通用工具执行
                result = await tool.execute(**parameters)
            
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
        user_query = shared_state.get("user_input", shared_state.get("user_query", ""))
        tool_result = shared_state.get("tool_result", "")
        tool_error = shared_state.get("tool_error", "")
        raw_response = shared_state.get("raw_response", "")
        is_tool_call = shared_state.get("is_tool_call", False)
        
        if is_tool_call:
            # 使用工具结果生成响应
            if tool_error:
                prompt = f"""
                用户查询：{user_query}
                
                工具调用出错：{tool_error}
                
                请向用户解释出现了什么问题，并提供一个有用的回答。
                """
            else:
                prompt = f"""
                用户查询：{user_query}
                
                工具调用结果：{tool_result}
                
                请基于工具调用结果，提供一个清晰、有用的回答给用户。
                """
        else:
            # 直接使用原始响应
            prompt = f"""
            用户查询：{user_query}
            
            请提供一个清晰、有用的回答给用户。
            
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


class ToolUseFlow(AsyncFlow):
    """工具使用流程"""
    
    def __init__(self, tools: List[Tool]):
        # 创建节点
        self.parser = ToolCallParserNode(tools)
        self.executor = ToolExecutorNode(tools)
        self.generator = ResponseGeneratorNode()
        
        # 设置流程
        super().__init__(start=self.parser)
        
        # 定义节点之间的转换
        self.parser.next(self.executor, action="use_tool")  # 如果需要使用工具
        self.parser.next(self.generator, action="direct_answer")  # 如果直接回答
        self.executor.next(self.generator, action="generate_response")  # 工具执行后生成响应
    
    async def prep_async(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """准备流程输入"""
        return shared_state
    
    async def post_async(self, shared_state: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理流程结果"""
        return shared_state
    
    async def run(self, shared_state: Dict[str, Any]) -> Dict[str, Any]:
        """运行工具使用流程"""
        # 运行流程
        result = await self._run_async(shared_state)
        
        return result


# 创建工具实例
search_tool = SearchInformationTool()
stock_tool = StockPriceTool()
tools = [search_tool, stock_tool]

# 创建流程实例
tool_use_flow = ToolUseFlow(tools)