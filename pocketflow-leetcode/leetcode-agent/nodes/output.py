"""
Output Node for LeetCode Agent

This node formats and outputs the final results of the LeetCode problem solving process.
"""

import os
import sys
from typing import Dict, Any

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node


class OutputNode(Node):
    """
    Node for formatting and outputting the final results.
    """
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the input for processing.
        
        Args:
            shared: Shared state dictionary
            
        Returns:
            Dictionary with prepared input data
        """
        # Get all relevant data from shared state
        problem_title = shared.get("problem_title", "")
        problem_description = shared.get("problem_description", "")
        problem_difficulty = shared.get("problem_difficulty", "")
        problem_constraints = shared.get("problem_constraints", [])
        problem_examples = shared.get("problem_examples", [])
        function_signature = shared.get("function_signature", "")
        language = shared.get("language", "python")
        
        # Get solution design from shared state
        solution_approach = shared.get("solution_approach", "")
        solution_time_complexity = shared.get("solution_time_complexity", "")
        solution_space_complexity = shared.get("solution_space_complexity", "")
        solution_algorithm_steps = shared.get("solution_algorithm_steps", [])
        solution_edge_cases = shared.get("solution_edge_cases", [])
        
        # Get code implementation from shared state
        code_implementation = shared.get("code_implementation", "")
        code_explanation = shared.get("code_explanation", "")
        
        # Get test results from shared state
        test_results = shared.get("test_results", {})
        
        # Get feedback information from shared state
        feedback_analysis = shared.get("feedback_analysis", "")
        issues_found = shared.get("issues_found", [])
        fix_suggestions = shared.get("fix_suggestions", [])
        
        # Get iteration count
        iteration = shared.get("iteration", 0)
        
        return {
            "problem_title": problem_title,
            "problem_description": problem_description,
            "problem_difficulty": problem_difficulty,
            "problem_constraints": problem_constraints,
            "problem_examples": problem_examples,
            "function_signature": function_signature,
            "language": language,
            "solution_approach": solution_approach,
            "solution_time_complexity": solution_time_complexity,
            "solution_space_complexity": solution_space_complexity,
            "solution_algorithm_steps": solution_algorithm_steps,
            "solution_edge_cases": solution_edge_cases,
            "code_implementation": code_implementation,
            "code_explanation": code_explanation,
            "test_results": test_results,
            "feedback_analysis": feedback_analysis,
            "issues_found": issues_found,
            "fix_suggestions": fix_suggestions,
            "iteration": iteration
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format and output the final results.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with formatted output
        """
        # Create the formatted output
        output = []
        
        # Add problem information
        output.append("=" * 80)
        output.append(f"PROBLEM: {inputs['problem_title']}")
        output.append(f"Difficulty: {inputs['problem_difficulty']}")
        output.append(f"Language: {inputs['language']}")
        output.append("=" * 80)
        output.append("")
        
        # Add problem description
        if inputs["problem_description"]:
            output.append("PROBLEM DESCRIPTION:")
            output.append(inputs["problem_description"])
            output.append("")
        
        # Add constraints
        if inputs["problem_constraints"]:
            output.append("CONSTRAINTS:")
            for constraint in inputs["problem_constraints"]:
                output.append(f"- {constraint}")
            output.append("")
        
        # Add examples
        if inputs["problem_examples"]:
            output.append("EXAMPLES:")
            for i, example in enumerate(inputs["problem_examples"]):
                output.append(f"Example {i+1}: {example}")
            output.append("")
        
        # Add solution approach
        if inputs["solution_approach"]:
            output.append("SOLUTION APPROACH:")
            output.append(inputs["solution_approach"])
            output.append("")
        
        # Add algorithm steps
        if inputs["solution_algorithm_steps"]:
            output.append("ALGORITHM STEPS:")
            for i, step in enumerate(inputs["solution_algorithm_steps"]):
                output.append(f"{i+1}. {step}")
            output.append("")
        
        # Add complexity analysis
        output.append("COMPLEXITY ANALYSIS:")
        output.append(f"Time Complexity: {inputs['solution_time_complexity']}")
        output.append(f"Space Complexity: {inputs['solution_space_complexity']}")
        output.append("")
        
        # Add edge cases
        if inputs["solution_edge_cases"]:
            output.append("EDGE CASES:")
            for edge_case in inputs["solution_edge_cases"]:
                output.append(f"- {edge_case}")
            output.append("")
        
        # Add code implementation
        if inputs["code_implementation"]:
            output.append("CODE IMPLEMENTATION:")
            output.append("```" + inputs["language"])
            output.append(inputs["code_implementation"])
            output.append("```")
            output.append("")
        
        # Add code explanation
        if inputs["code_explanation"]:
            output.append("CODE EXPLANATION:")
            output.append(inputs["code_explanation"])
            output.append("")
        
        # Add test results
        if inputs["test_results"]:
            output.append("TEST RESULTS:")
            test_results = inputs["test_results"]
            output.append(f"Total Tests: {test_results.get('total_tests', 0)}")
            output.append(f"Passed: {test_results.get('passed_tests', 0)}")
            output.append(f"Failed: {test_results.get('failed_tests', 0)}")
            output.append(f"All Passed: {test_results.get('all_passed', False)}")
            output.append("")
            
            # Add failed test details
            if "test_details" in test_results:
                failed_tests = [t for t in test_results["test_details"] if not t.get("passed", True)]
                if failed_tests:
                    output.append("FAILED TEST CASES:")
                    for test in failed_tests:
                        output.append(f"Test {test.get('test_case', 'N/A')}: {test.get('description', '')}")
                        output.append(f"  Input: {test.get('input', '')}")
                        output.append(f"  Expected: {test.get('expected_output', '')}")
                        output.append(f"  Actual: {test.get('actual_output', '')}")
                        output.append("")
        
        # Add feedback information if available
        if inputs["feedback_analysis"]:
            output.append("FEEDBACK ANALYSIS:")
            output.append(inputs["feedback_analysis"])
            output.append("")
        
        if inputs["issues_found"]:
            output.append("ISSUES FOUND:")
            for issue in inputs["issues_found"]:
                output.append(f"- {issue}")
            output.append("")
        
        if inputs["fix_suggestions"]:
            output.append("FIX SUGGESTIONS:")
            for suggestion in inputs["fix_suggestions"]:
                output.append(f"- {suggestion}")
            output.append("")
        
        # Add iteration count
        output.append(f"Iterations: {inputs['iteration']}")
        output.append("")
        
        # Join all parts into a single string
        formatted_output = "\n".join(output)
        
        # Print the output
        print(formatted_output)
        
        return {
            "formatted_output": formatted_output,
            "success": inputs["test_results"].get("all_passed", False)
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the formatted output.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with formatted output
        shared["formatted_output"] = exec_res.get("formatted_output", "")
        shared["success"] = exec_res.get("success", False)
        
        # This is the end of the flow
        return "end"