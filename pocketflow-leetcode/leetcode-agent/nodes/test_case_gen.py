"""
Test Case Generation Node for LeetCode Agent

This node generates test cases for LeetCode problems based on problem description and solution design.
"""

import os
import sys
from typing import Dict, Any

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node
from utils.llm_client import LLMClient
from utils.validators import validate_test_cases


class TestCaseGenNode(Node):
    """
    Node for generating test cases.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the TestCaseGenNode.
        
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
        problem_constraints = shared.get("problem_constraints", [])
        problem_examples = shared.get("problem_examples", [])
        function_signature = shared.get("problem_function_signature", "")  # Use problem_function_signature instead
        
        # Get solution design from shared state
        solution_approach = shared.get("solution_approach", "")
        solution_algorithm_steps = shared.get("solution_algorithm_steps", [])
        
        # Format constraints, examples, and algorithm steps for the prompt
        constraints_text = "\n".join([f"- {constraint}" for constraint in problem_constraints])
        examples_text = "\n".join([f"Example {i+1}: {example}" for i, example in enumerate(problem_examples)])
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(solution_algorithm_steps)])
        
        return {
            "problem_title": problem_title,
            "problem_description": problem_description,
            "constraints": constraints_text,
            "examples": examples_text,
            "function_signature": function_signature,
            "solution_approach": solution_approach,
            "solution_algorithm_steps": steps_text
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate test cases.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with test cases data
        """
        # Read the test case generation prompt
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "prompts", "test_generation.txt")
        
        with open(prompt_file, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt with the problem information and solution design
        prompt = prompt_template.format(
            problem_title=inputs["problem_title"],
            problem_description=inputs["problem_description"],
            constraints=inputs["constraints"],
            examples=inputs["examples"],
            function_signature=inputs["function_signature"],
            solution_approach=inputs["solution_approach"],
            solution_algorithm_steps=inputs["solution_algorithm_steps"]
        )
        
        # Generate structured response using LLM
        try:
            response = self.llm_client.generate_structured_response(
                prompt=prompt,
                output_format="yaml"
            )
            
            # Validate test cases
            if "test_cases" in response:
                validate_test_cases(response["test_cases"])
            
            # Ensure required fields are present
            if "test_cases" not in response:
                response["test_cases"] = []
            
            return response
            
        except Exception as e:
            # Fallback to basic test cases
            return {
                "test_cases": [
                    {
                        "input": self._extract_input_from_examples(inputs["examples"]),
                        "output": "Expected output",
                        "description": "Basic test case"
                    }
                ]
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the test cases.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with test cases
        shared["test_cases"] = exec_res.get("test_cases", [])
        
        # Always proceed to test run
        return "default"
    
    def _extract_input_from_examples(self, examples_text: str) -> str:
        """
        Extract input from examples text.
        
        Args:
            examples_text: Text containing examples
            
        Returns:
            Extracted input string
        """
        if not examples_text:
            return "Sample input"
        
        try:
            # Try to extract input from examples
            # This is a simple extraction - in a real implementation,
            # we might want to parse the examples more carefully
            lines = examples_text.split("\n")
            for line in lines:
                if "Input:" in line:
                    return line.split("Input:")[1].strip()
                elif "input:" in line:
                    return line.split("input:")[1].strip()
            
            # If no explicit input found, return the first line
            return lines[0].strip() if lines else "Sample input"
        except Exception:
            return "Sample input"