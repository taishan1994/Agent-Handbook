"""
Parse Problem Node for LeetCode Agent

This node parses problem content from URLs or direct descriptions.
"""

import os
import sys
import traceback
import tempfile
import subprocess
from typing import Dict, Any

from pocketflow import Node
from Leetcode_Agent.utils.llm_client import LLMClient
from Leetcode_Agent.utils.logger import get_logger


class ExecPython3Node(Node):
    """
    Node for parsing problem content.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the ParseProblemNode.
        
        Args:
            llm_client: LLM client instance
        """
        super().__init__()
        self.llm_client = llm_client
        self.logger = get_logger(self.__class__.__name__)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the input for processing.
        
        Args:
            shared: Shared state dictionary
            
        Returns:
            Dictionary with prepared input data
        """
        # Get problem input and input type from shared state
        return shared
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the problem content.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with parsed problem data
        """

        # 构造临时脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(inputs["python3_code"])
            temp_path = f.name

        output = inputs

        try:
            # 使用 subprocess 在 shell 中执行 python3
            result = subprocess.run(
                ["python3", temp_path],
                capture_output=True,
                text=True,
                timeout=30  # 设置超时，防止死循环
            )

            output["test_result"] = result.stdout.strip()

        except Exception as e:
            output["test_result"] = traceback.format_exc()
        finally:
            # 清理临时文件
            os.remove(temp_path)
        
        self.logger.info(f"执行结果：{output["test_result"]}")
        analyse_ = self.analyse_result(output)
        output["analyse_result"] = analyse_

        return output

    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the parsed problem data.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """

        # Update shared state with parsed problem data
        shared["test_result"] = exec_res.get("test_result", "")
        
        # Always proceed to solution design
        return "default"
    
    def analyse_result(self,shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a direct problem description using LLM.
        
        Args:
            description: Direct problem description
            
        Returns:
            Dictionary with parsed problem data
        """
        # Read the problem analysis prompt
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "prompts", "result_analysis.txt")
        
        with open(prompt_file, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt with the problem description
        python3_code = shared["python3_code"]
        problem_desc = shared["problem_desc"]
        test_result = shared["test_result"]

        shared["iteration_count"] += 1

        prompt = prompt_template.format(problem_desc, python3_code, test_result)
        
        self.logger.info(f"代码分析师使用的prompt: {prompt}")

        # Generate structured response using LLM
        response = self.llm_client.chat_completion(
            prompt,
        )
        
        self.logger.info(f"代码分析师：{response}")
        return response
