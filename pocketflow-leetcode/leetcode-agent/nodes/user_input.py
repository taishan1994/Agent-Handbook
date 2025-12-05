"""
User Input Node for LeetCode Agent

This node handles user input, including problem URLs or direct problem descriptions.
"""

import os
import sys
from typing import Dict, Any, Optional

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node
from utils.validators import validate_leetcode_url, validate_language, validate_optimization_target


class UserInputNode(Node):
    """
    Node for handling user input.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the UserInputNode.
        
        Args:
            llm_client: LLM client instance (not used in this node)
        """
        super().__init__()
        self.llm_client = llm_client
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the input for processing.
        
        Args:
            shared: Shared state dictionary
            
        Returns:
            Dictionary with prepared input data
        """
        # Get user input from shared state
        problem_input = shared.get("problem_input", "")
        language_preference = shared.get("language_preference", "python")
        optimize_for = shared.get("optimize_for", "time")
        max_iterations = shared.get("max_iterations", 3)
        
        return {
            "problem_input": problem_input,
            "language_preference": language_preference,
            "optimize_for": optimize_for,
            "max_iterations": max_iterations
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the user input.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with processed input data
        """
        problem_input = inputs["problem_input"]
        language_preference = inputs["language_preference"]
        optimize_for = inputs["optimize_for"]
        max_iterations = inputs["max_iterations"]
        
        # Validate language preference
        try:
            validate_language(language_preference)
        except Exception as e:
            raise ValueError(f"Invalid language preference: {e}")
        
        # Validate optimization target
        try:
            validate_optimization_target(optimize_for)
        except Exception as e:
            raise ValueError(f"Invalid optimization target: {e}")
        
        # Determine input type (URL or direct description)
        input_type = "url" if self._is_url(problem_input) else "description"
        
        # Validate URL if it's a URL
        if input_type == "url":
            try:
                validate_leetcode_url(problem_input)
            except Exception as e:
                raise ValueError(f"Invalid LeetCode URL: {e}")
        
        # Validate max_iterations
        if not isinstance(max_iterations, int) or max_iterations < 1:
            raise ValueError("max_iterations must be a positive integer")
        
        return {
            "problem_input": problem_input,
            "input_type": input_type,
            "language_preference": language_preference,
            "optimize_for": optimize_for,
            "max_iterations": max_iterations
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the processed input.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with processed input
        shared["problem_input"] = exec_res["problem_input"]
        shared["input_type"] = exec_res["input_type"]
        shared["language_preference"] = exec_res["language_preference"]
        shared["optimize_for"] = exec_res["optimize_for"]
        shared["max_iterations"] = exec_res["max_iterations"]
        
        # Initialize iteration count
        shared["iteration_count"] = 0
        
        # Always proceed to parse problem
        return "default"
    
    def _is_url(self, text: str) -> bool:
        """
        Check if the input text is a URL.
        
        Args:
            text: Input text to check
            
        Returns:
            True if the text is a URL, False otherwise
        """
        return text.startswith("http://") or text.startswith("https://")