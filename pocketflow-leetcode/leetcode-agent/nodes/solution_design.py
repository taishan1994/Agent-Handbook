"""
Solution Design Node for LeetCode Agent

This node generates solution approaches and algorithm designs for LeetCode problems.
"""

import os
import sys
from typing import Dict, Any

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node
from utils.llm_client import LLMClient
from utils.validators import validate_solution_data


class SolutionDesignNode(Node):
    """
    Node for designing solution approaches.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the SolutionDesignNode.
        
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
        optimize_for = shared.get("optimize_for", "time")
        
        # Format constraints and examples for the prompt
        constraints_text = "\n".join([f"- {constraint}" for constraint in problem_constraints])
        examples_text = "\n".join([f"Example {i+1}: {example}" for i, example in enumerate(problem_examples)])
        
        return {
            "problem_title": problem_title,
            "problem_description": problem_description,
            "constraints": constraints_text,
            "examples": examples_text,
            "optimize_for": optimize_for
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Design a solution approach.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with solution design data
        """
        # Read the solution design prompt
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "prompts", "solution_design.txt")
        
        with open(prompt_file, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt with the problem information
        prompt = prompt_template.format(
            problem_description=inputs["problem_description"],
            constraints=inputs["constraints"],
            examples=inputs["examples"],
            optimize_for=inputs["optimize_for"]
        )
        
        # Generate structured response using LLM
        try:
            response = self.llm_client.generate_structured_response(
                prompt=prompt,
                output_format="yaml"
            )
            
            # Validate solution data
            validate_solution_data(response)
            
            # Ensure required fields are present
            if "algorithm_steps" not in response:
                response["algorithm_steps"] = []
            
            if "edge_cases" not in response:
                response["edge_cases"] = []
            
            if "optimization_opportunities" not in response:
                response["optimization_opportunities"] = []
            
            if "alternative_approaches" not in response:
                response["alternative_approaches"] = []
            
            return response
            
        except Exception as e:
            # Fallback to basic solution design
            return {
                "approach": f"Analyze the problem requirements and constraints to develop an optimized solution for {inputs['optimize_for']}.",
                "time_complexity": "To be determined after implementation",
                "space_complexity": "To be determined after implementation",
                "algorithm_steps": [
                    "Analyze the problem requirements",
                    "Design an algorithm based on the constraints",
                    "Implement the solution",
                    "Test with various test cases"
                ],
                "edge_cases": [
                    "Handle empty input cases",
                    "Consider boundary conditions"
                ],
                "optimization_opportunities": [
                    "Optimize for " + inputs["optimize_for"]
                ],
                "alternative_approaches": []
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the solution design.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with solution design
        shared["solution_approach"] = exec_res.get("approach", "")
        shared["solution_time_complexity"] = exec_res.get("time_complexity", "")
        shared["solution_space_complexity"] = exec_res.get("space_complexity", "")
        shared["solution_algorithm_steps"] = exec_res.get("algorithm_steps", [])
        shared["solution_edge_cases"] = exec_res.get("edge_cases", [])
        shared["solution_optimization_opportunities"] = exec_res.get("optimization_opportunities", [])
        shared["solution_alternative_approaches"] = exec_res.get("alternative_approaches", [])
        
        # Always proceed to code generation
        return "default"