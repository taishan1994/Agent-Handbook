"""
Parse Problem Node for LeetCode Agent

This node parses problem content from URLs or direct descriptions.
"""

import os
import sys
import traceback
from typing import Dict, Any

from pocketflow import Node
from Leetcode_Agent.utils.llm_client import LLMClient
from Leetcode_Agent.utils.logger import get_logger


class ParseProblemNode(Node):
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
        problem_desc = shared.get("problem_desc", "")
        function_desc = shared.get("function_desc", "")
        
        return {
            "problem_desc": problem_desc,
            "function_desc": function_desc
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the problem content.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with parsed problem data
        """
        problem_desc = inputs.get("problem_desc", "")
        function_desc = inputs.get("function_desc", "")

        output = self._parse_direct_description(problem_desc, function_desc)
                
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
        shared["full_text"] = exec_res.get("full_text", "")
        shared["python3_code"] = exec_res.get("python3_code", "")
        
        # Always proceed to solution design
        return "default"
    
    def _parse_direct_description(self, description: str, function_desc: str) -> Dict[str, Any]:
        """
        Parse a direct problem description using LLM.
        
        Args:
            description: Direct problem description
            
        Returns:
            Dictionary with parsed problem data
        """
        # Read the problem analysis prompt
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "prompts", "problem_analysis.txt")
        
        with open(prompt_file, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt with the problem description
        prompt = prompt_template.format(description, function_desc)
        
        self.logger.info(f"代码解题师使用的prompt: {prompt}")

        # Generate structured response using LLM
        response = self.llm_client.generate_structured_response(
            prompt=prompt,
            output_format="python3"
        )
        
        self.logger.info(f"代码：{response["python3_code"]}")
        
        return response
