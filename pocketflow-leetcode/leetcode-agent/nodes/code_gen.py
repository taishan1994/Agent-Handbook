"""
Code Generation Node for LeetCode Agent

This node generates code implementations for LeetCode problems based on solution designs.
"""

import os
import sys
from typing import Dict, Any

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node
from utils.llm_client import LLMClient
from utils.validators import validate_code_data


class CodeGenNode(Node):
    """
    Node for generating code implementations.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the CodeGenNode.
        
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
        function_signature = shared.get("problem_function_signature", "")  # Use problem_function_signature to match parse_problem.py
        
        # Debug: Print function signature from shared state
        print(f"DEBUG PREP: Function signature from shared state: '{function_signature}'")
        
        # If function signature is provided but uses a different function name, replace it with 'solution'
        if function_signature and not function_signature.startswith("def solution("):
            # Extract the parameters from the original function signature
            import re
            match = re.match(r'def\s+\w+\s*\(([^)]*)\)', function_signature)
            if match:
                params = match.group(1)
                function_signature = f"def solution({params}):"
                print(f"DEBUG PREP: Modified function signature to: '{function_signature}'")
        
        language = shared.get("language", "python")
        optimize_for = shared.get("optimize_for", "time")
        
        # Get solution design from shared state
        solution_approach = shared.get("solution_approach", "")
        solution_time_complexity = shared.get("solution_time_complexity", "")
        solution_space_complexity = shared.get("solution_space_complexity", "")
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
            "language": language,
            "optimize_for": optimize_for,
            "solution_approach": solution_approach,
            "solution_time_complexity": solution_time_complexity,
            "solution_space_complexity": solution_space_complexity,
            "solution_algorithm_steps": steps_text
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate code implementation.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with code implementation data
        """
        # Read the code generation prompt
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "prompts", "code_generation.txt")
        
        with open(prompt_file, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt with the problem information and solution design
        # Ensure function_signature is not empty
        function_signature = inputs["function_signature"] if inputs["function_signature"] else "def solution(nums, target):"
        
        prompt = prompt_template.format(
            problem_title=inputs["problem_title"],
            problem_description=inputs["problem_description"],
            constraints=inputs["constraints"],
            examples=inputs["examples"],
            function_signature=function_signature,
            language=inputs["language"],
            optimize_for=inputs["optimize_for"],
            solution_approach=inputs["solution_approach"],
            time_complexity=inputs["solution_time_complexity"],
            space_complexity=inputs["solution_space_complexity"],
            algorithm_steps=inputs["solution_algorithm_steps"]
        )
        
        # Debug: Print function signature
        print(f"DEBUG: Original function signature: {inputs['function_signature']}")
        print(f"DEBUG: Used function signature: {function_signature}")
        print(f"DEBUG: Formatted prompt (first 500 chars): {prompt[:500]}")
        
        # Generate structured response using LLM
        try:
            response = self.llm_client.generate_structured_response(
                prompt=prompt,
                output_format="yaml"
            )
            
            # Validate code implementation
            if "implementation" in response:
                code_data = {
                    "language": response.get("language", inputs["language"]),
                    "implementation": response["implementation"]
                }
                validate_code_data(code_data)
            
            # Ensure required fields are present
            if "language" not in response:
                response["language"] = inputs["language"]
            
            if "implementation" not in response:
                response["implementation"] = f"# Implementation for {inputs['problem_title']}\n# TODO: Add implementation"
            
            if "explanation" not in response:
                response["explanation"] = "Code implementation based on the solution design."
            
            if "time_complexity" not in response:
                response["time_complexity"] = inputs["solution_time_complexity"]
            
            if "space_complexity" not in response:
                response["space_complexity"] = inputs["solution_space_complexity"]
            
            return response
            
        except Exception as e:
            # Fallback to basic code implementation
            # Use the full function signature if available, otherwise use a default signature
            if inputs["function_signature"]:
                function_sig = inputs["function_signature"]
            else:
                # Default function signature for common LeetCode problems
                function_sig = "def solution(nums, target):"
            
            return {
                "language": inputs["language"],
                "implementation": f"# Implementation for {inputs['problem_title']}\n\n{function_sig}\n    # TODO: Implement the solution\n    pass",
                "explanation": f"Basic implementation for {inputs['problem_title']}.",
                "time_complexity": "To be determined",
                "space_complexity": "To be determined"
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the code implementation.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with code implementation
        shared["code_language"] = exec_res.get("language", "")
        shared["code_implementation"] = exec_res.get("implementation", "")
        shared["code_explanation"] = exec_res.get("explanation", "")
        shared["code_time_complexity"] = exec_res.get("time_complexity", "")
        shared["code_space_complexity"] = exec_res.get("space_complexity", "")
        
        # Always proceed to test case generation
        return "default"
    
    def _extract_function_name(self, function_signature: str) -> str:
        """
        Extract function name from function signature.
        
        Args:
            function_signature: Function signature string
            
        Returns:
            Extracted function name
        """
        # Default function name if extraction fails
        default_name = "solution"
        
        if not function_signature:
            return default_name
        
        try:
            # Try to extract function name from signature
            # For Python: "def solution(...)" -> "solution"
            if "def " in function_signature:
                parts = function_signature.split("def ")[1].split("(")[0].strip()
                return parts
            # For Java: "public int solution(...)" -> "solution"
            elif "(" in function_signature:
                parts = function_signature.split("(")[0].strip().split()[-1]
                return parts
            # Default case
            else:
                return default_name
        except Exception:
            return default_name