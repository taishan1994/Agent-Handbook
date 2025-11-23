"""
Chapter 12: Exception Handling and Recovery - Nodes Implementation
使用PocketFlow实现的异常处理和恢复模式节点
"""

import sys
import os
import random
import yaml
import time
from typing import Dict, Any, Optional

# 添加utils路径
utils_path = os.path.join(os.path.dirname(__file__), '..', '..', 'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)

# 添加PocketFlow路径
pocketflow_path = os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow')
if pocketflow_path not in sys.path:
    sys.path.append(pocketflow_path)

from pocketflow import Node

try:
    from call_llm import call_llm
    from exa_search_main import search_web_exa
except ImportError:
    # 如果无法导入，使用模拟函数
    def call_llm(prompt):
        return f"模拟LLM响应: 基于问题生成的回答"
    
    def search_web_exa(query):
        return f"模拟搜索结果: 关于 {query} 的搜索结果"


class PrimaryHandler(Node):
    """
    主要处理节点，负责执行核心任务
    有一定概率模拟失败，触发异常处理流程
    """
    
    def __init__(self, failure_rate=0.3):
        """
        初始化主要处理节点
        
        Args:
            failure_rate: 模拟失败的概率，默认为0.3
        """
        super().__init__()
        self.failure_rate = failure_rate
    
    def prep(self, shared):
        """准备处理所需的输入数据"""
        # 获取用户问题和上下文
        question = shared.get("question", "")
        context = shared.get("context", "")
        
        # 获取重试次数
        retry_count = shared.get("retry_count", 0)
        
        return question, context, retry_count
    
    def exec(self, inputs):
        """执行主要处理逻辑，可能模拟失败"""
        question, context, retry_count = inputs
        
        print(f"🔧 PrimaryHandler: 开始处理问题 (重试次数: {retry_count})")
        print(f"问题: {question}")
        
        # 模拟处理时间
        time.sleep(1)
        
        # 模拟随机失败
        if random.random() < self.failure_rate:
            error_type = random.choice([
                "network_timeout", 
                "api_error", 
                "data_corruption",
                "resource_exhausted"
            ])
            error_msg = f"模拟错误: {error_type}"
            print(f"❌ PrimaryHandler: 处理失败 - {error_msg}")
            
            # 返回错误信息
            return {
                "success": False,
                "error_type": error_type,
                "error_message": error_msg,
                "retry_count": retry_count
            }
        
        # 正常处理流程
        print("🔍 PrimaryHandler: 开始搜索相关信息...")
        
        # 构建搜索查询
        search_query = f"关于 {question} 的详细信息"
        
        try:
            # 调用搜索功能
            search_results = search_web_exa(search_query)
            
            # 使用LLM生成回答
            prompt = f"""
基于以下搜索结果，回答用户的问题。

问题: {question}
上下文: {context}

搜索结果:
{search_results}

请提供一个详细、准确的回答:
"""
            
            answer = call_llm(prompt)
            
            print("✅ PrimaryHandler: 处理成功")
            
            # 返回成功结果
            return {
                "success": True,
                "answer": answer,
                "search_results": search_results,
                "retry_count": retry_count
            }
            
        except Exception as e:
            error_msg = f"处理过程中发生异常: {str(e)}"
            print(f"❌ PrimaryHandler: {error_msg}")
            
            # 返回错误信息
            return {
                "success": False,
                "error_type": "processing_exception",
                "error_message": error_msg,
                "retry_count": retry_count
            }
    
    def post(self, shared, prep_res, exec_res):
        """处理执行结果，决定下一步流向"""
        if exec_res["success"]:
            # 成功，保存结果并转到响应代理
            shared["primary_result"] = exec_res["answer"]
            shared["search_results"] = exec_res.get("search_results", "")
            print("✅ PrimaryHandler: 流程完成，转到响应代理")
            return "response"
        else:
            # 失败，保存错误信息并转到回退处理器
            shared["last_error"] = exec_res
            shared["retry_count"] = exec_res["retry_count"] + 1
            print(f"⚠️ PrimaryHandler: 处理失败，转到回退处理器 (错误类型: {exec_res['error_type']})")
            return "fallback"


class FallbackHandler(Node):
    """
    回退处理节点，负责异常处理和恢复
    """
    
    def __init__(self, max_retries=3):
        """
        初始化回退处理节点
        
        Args:
            max_retries: 最大重试次数
        """
        super().__init__()
        self.max_retries = max_retries
    
    def prep(self, shared):
        """准备处理所需的输入数据"""
        # 获取用户问题
        question = shared.get("question", "")
        
        # 获取最后一次错误信息
        last_error = shared.get("last_error", {})
        
        # 获取重试次数
        retry_count = shared.get("retry_count", 0)
        
        return question, last_error, retry_count
    
    def exec(self, inputs):
        """执行回退处理逻辑"""
        question, last_error, retry_count = inputs
        
        print(f"🛠️ FallbackHandler: 开始处理错误 (重试次数: {retry_count}/{self.max_retries})")
        print(f"错误类型: {last_error.get('error_type', 'unknown')}")
        print(f"错误信息: {last_error.get('error_message', 'no message')}")
        
        # 检查是否达到最大重试次数
        if retry_count >= self.max_retries:
            print("❌ FallbackHandler: 达到最大重试次数，无法恢复")
            return {
                "success": False,
                "recovery_failed": True,
                "reason": "max_retries_exceeded",
                "error_message": f"已达到最大重试次数 {self.max_retries}，无法恢复"
            }
        
        # 根据错误类型选择恢复策略
        error_type = last_error.get("error_type", "unknown")
        
        if error_type == "network_timeout":
            # 网络超时 - 增加超时时间并重试
            recovery_strategy = "增加超时时间"
            recovery_success = random.random() < 0.7  # 70% 概率恢复成功
            
        elif error_type == "api_error":
            # API错误 - 使用备用API或重试
            recovery_strategy = "使用备用API"
            recovery_success = random.random() < 0.6  # 60% 概率恢复成功
            
        elif error_type == "data_corruption":
            # 数据损坏 - 清理数据并重试
            recovery_strategy = "清理损坏数据"
            recovery_success = random.random() < 0.8  # 80% 概率恢复成功
            
        elif error_type == "resource_exhausted":
            # 资源耗尽 - 释放资源并重试
            recovery_strategy = "释放资源"
            recovery_success = random.random() < 0.5  # 50% 概率恢复成功
            
        elif error_type == "processing_exception":
            # 处理异常 - 使用简化处理流程
            recovery_strategy = "使用简化处理流程"
            recovery_success = random.random() < 0.7  # 70% 概率恢复成功
            
        else:
            # 未知错误 - 通用恢复策略
            recovery_strategy = "通用恢复策略"
            recovery_success = random.random() < 0.4  # 40% 概率恢复成功
        
        print(f"🔧 FallbackHandler: 尝试恢复策略 - {recovery_strategy}")
        
        # 模拟恢复处理时间
        time.sleep(1)
        
        if recovery_success:
            print("✅ FallbackHandler: 恢复成功")
            return {
                "success": True,
                "recovery_strategy": recovery_strategy,
                "retry_count": retry_count,
                "can_retry": True
            }
        else:
            print("❌ FallbackHandler: 恢复失败")
            return {
                "success": False,
                "recovery_strategy": recovery_strategy,
                "retry_count": retry_count,
                "can_retry": retry_count < self.max_retries - 1
            }
    
    def post(self, shared, prep_res, exec_res):
        """处理执行结果，决定下一步流向"""
        if exec_res["success"]:
            # 恢复成功，更新重试次数并回到主要处理器
            shared["retry_count"] = exec_res["retry_count"]
            shared["last_recovery"] = exec_res["recovery_strategy"]
            print("🔄 FallbackHandler: 恢复成功，重新尝试主要处理")
            return "retry"
        elif exec_res.get("recovery_failed"):
            # 恢复彻底失败，转到响应代理生成错误响应
            shared["final_error"] = exec_res["error_message"]
            print("❌ FallbackHandler: 恢复彻底失败，转到响应代理生成错误响应")
            return "response"
        elif exec_res.get("can_retry"):
            # 可以继续重试，更新重试次数并回到主要处理器
            shared["retry_count"] = exec_res["retry_count"] + 1
            print(f"🔄 FallbackHandler: 准备第 {shared['retry_count']} 次重试")
            return "retry"
        else:
            # 无法重试，转到响应代理生成错误响应
            shared["final_error"] = f"无法从错误中恢复: {exec_res.get('recovery_strategy', 'unknown')}"
            print("❌ FallbackHandler: 无法恢复，转到响应代理生成错误响应")
            return "response"


class ResponseAgent(Node):
    """
    响应代理节点，负责生成最终响应
    """
    
    def prep(self, shared):
        """准备处理所需的输入数据"""
        # 获取用户问题
        question = shared.get("question", "")
        
        # 获取主要处理结果
        primary_result = shared.get("primary_result", "")
        
        # 获取最终错误（如果有）
        final_error = shared.get("final_error", "")
        
        # 获取处理历史
        retry_count = shared.get("retry_count", 0)
        last_recovery = shared.get("last_recovery", "")
        
        return question, primary_result, final_error, retry_count, last_recovery
    
    def exec(self, inputs):
        """生成最终响应"""
        question, primary_result, final_error, retry_count, last_recovery = inputs
        
        print("📝 ResponseAgent: 生成最终响应")
        
        if final_error:
            # 有最终错误，生成错误响应
            print("❌ ResponseAgent: 生成错误响应")
            
            prompt = f"""
用户提出了一个问题，但系统在处理过程中遇到了无法恢复的错误。

用户问题: {question}
错误信息: {final_error}
重试次数: {retry_count}
最后一次恢复尝试: {last_recovery}

请生成一个礼貌、诚实的错误响应，解释发生了什么，并提供一些可能的替代方案或建议。
"""
            
            response = call_llm(prompt)
            
            return {
                "success": False,
                "response": response,
                "error": final_error,
                "retry_count": retry_count
            }
        else:
            # 有主要处理结果，生成成功响应
            print("✅ ResponseAgent: 生成成功响应")
            
            # 添加处理历史信息
            processing_info = ""
            if retry_count > 0:
                processing_info = f"\n\n处理信息: 此回答经过了 {retry_count} 次重试"
                if last_recovery:
                    processing_info += f"，最后使用了 '{last_recovery}' 恢复策略"
            
            response = primary_result + processing_info
            
            return {
                "success": True,
                "response": response,
                "retry_count": retry_count
            }
    
    def post(self, shared, prep_res, exec_res):
        """保存最终响应并完成流程"""
        # 保存最终响应
        shared["final_response"] = exec_res["response"]
        shared["processing_success"] = exec_res["success"]
        
        if exec_res["success"]:
            print("✅ ResponseAgent: 成功生成最终响应")
        else:
            print("❌ ResponseAgent: 生成错误响应")
        
        # 流程结束
        return "end"