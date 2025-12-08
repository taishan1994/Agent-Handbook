"""
Parse Problem Node for LeetCode Agent

This node parses problem content from URLs or direct descriptions.
"""

import os
import re
import sys
import traceback
import tempfile
import subprocess
from typing import Dict, Any

from pocketflow import Node
from Leetcode_Agent.utils.llm_client import LLMClient
from Leetcode_Agent.utils.logger import get_logger


class CodeRegenNode(Node):
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

        if re.search("\\\\box{是}", inputs["analyse_result"]):
            return inputs

        # 构造临时脚本文件
        gen_result= self.regen_python3_code(inputs)
        for k,v in gen_result.items():
            inputs[k] = v
        return inputs

    
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

        if not re.search("\\\\box{是}", exec_res["analyse_result"]):
            self.logger.info(f"解题错误，正在进行代码重构！！！")
            return "regen"

        if shared["iteration_count"] == shared["max_iterations"]:
            self.logger.info(f"已达到最大迭代次数{shared['max_iterations']}，未生成符合要求的代码")
            return "default"

        # Update shared state with parsed problem data
        for k,v in exec_res.items():
            if k not in shared:
                shared[k] = v
        
        # Always proceed to solution design
        return "default"
    
    def regen_python3_code(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a direct problem description using LLM.
        
        Args:
            description: Direct problem description
            
        Returns:
            Dictionary with parsed problem data
        """
        # Read the problem analysis prompt
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "prompts", "code_regen.txt")
        
        with open(prompt_file, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt with the problem description
        problem_desc = shared["problem_desc"]
        python3_code = shared["python3_code"]

        test_result = shared["test_result"]
        analyse = shared["analyse_result"]
        prompt = prompt_template.format(problem_desc, python3_code, test_result, analyse)
        
        # Generate structured response using LLM
        self.logger.info(f"代码重构师使用的prompt: {prompt}")

        response = self.llm_client.generate_structured_response(
            prompt,
            output_format="python3"
        )
        
        self.logger.info(f"代码重构师：{response}")
        return response
