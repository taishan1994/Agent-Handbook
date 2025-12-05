"""
Feedback Loop Node for LeetCode Agent

This node processes feedback from failed test cases and generates optimization suggestions.
"""

import os
import sys
from typing import Dict, Any

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node
from utils.llm_client import LLMClient


class FeedbackLoopNode(Node):
    """
    Node for processing feedback and generating optimization suggestions.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the FeedbackLoopNode.
        
        Args:
            llm_client: LLM client instance
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
        # Get problem information from shared state
        problem_title = shared.get("problem_title", "")
        problem_description = shared.get("problem_description", "")
        
        # Get solution design from shared state
        solution_approach = shared.get("solution_approach", "")
        
        # Get code implementation from shared state
        code_implementation = shared.get("code_implementation", "")
        
        # Get test results from shared state
        test_results = shared.get("test_results", {})
        failed_test_cases = []
        
        # Extract failed test cases
        if "test_details" in test_results:
            for test_detail in test_results["test_details"]:
                if not test_detail.get("passed", True):
                    failed_test_cases.append(test_detail)
        
        return {
            "problem_title": problem_title,
            "problem_description": problem_description,
            "solution_approach": solution_approach,
            "code_implementation": code_implementation,
            "failed_test_cases": failed_test_cases
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process feedback and generate optimization suggestions.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with feedback and optimization suggestions
        """
        # If there are no failed test cases, return empty feedback
        if not inputs["failed_test_cases"]:
            return {
                "analysis": "All tests passed successfully.",
                "issues_found": [],
                "fix_suggestions": [],
                "optimization_suggestions": []
            }
        
        # Read the optimization prompt
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "prompts", "optimization.txt")
        
        with open(prompt_file, 'r') as f:
            prompt_template = f.read()
        
        # Format failed test cases for the prompt
        failed_cases_text = "\n".join([
            f"Test Case {case['test_case']}: {case['description']}\n"
            f"Input: {case['input']}\n"
            f"Expected: {case['expected_output']}\n"
            f"Actual: {case['actual_output']}\n"
            for case in inputs["failed_test_cases"]
        ])
        
        # Format the prompt with the problem information and failed test cases
        prompt = prompt_template.format(
            problem_title=inputs["problem_title"],
            problem_description=inputs["problem_description"],
            solution_approach=inputs["solution_approach"],
            current_code=inputs["code_implementation"],
            failed_test_cases=failed_cases_text,
            optimize_for="time"  # Default optimization target
        )
        
        # Generate structured response using LLM
        try:
            response = self.llm_client.generate_structured_response(
                prompt=prompt,
                output_format="yaml"
            )
            
            # Ensure required fields are present
            if "analysis" not in response:
                response["analysis"] = "Analysis of the failed test cases."
            
            if "issues_found" not in response:
                response["issues_found"] = []
            
            if "fix_suggestions" not in response:
                response["fix_suggestions"] = []
            
            if "optimization_suggestions" not in response:
                response["optimization_suggestions"] = []
            
            return response
            
        except Exception as e:
            # Fallback to basic feedback
            return {
                "analysis": f"Analysis of the failed test cases. Error: {str(e)}",
                "issues_found": [
                    "Code implementation does not pass all test cases"
                ],
                "fix_suggestions": [
                    "Review the failed test cases and adjust the implementation"
                ],
                "optimization_suggestions": [
                    "Consider edge cases and boundary conditions"
                ]
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the feedback and optimization suggestions.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with feedback and optimization suggestions
        shared["feedback_analysis"] = exec_res.get("analysis", "")
        shared["issues_found"] = exec_res.get("issues_found", [])
        shared["fix_suggestions"] = exec_res.get("fix_suggestions", [])
        shared["optimization_suggestions"] = exec_res.get("optimization_suggestions", [])
        
        # Go back to code generation for another iteration
        return "code_gen"