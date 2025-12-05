"""
Test Run Node for LeetCode Agent

This node runs test cases against the generated code and reports the results.
"""

import os
import sys
import subprocess
import tempfile
from typing import Dict, Any

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node
from utils.code_executor import CodeExecutor


class TestRunNode(Node):
    """
    Node for running test cases.
    """
    
    def __init__(self, code_executor: CodeExecutor):
        """
        Initialize the TestRunNode.
        
        Args:
            code_executor: Code executor instance
        """
        super().__init__()
        self.code_executor = code_executor
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the input for processing.
        
        Args:
            shared: Shared state dictionary
            
        Returns:
            Dictionary with prepared input data
        """
        # Get code implementation from shared state
        code_implementation = shared.get("code_implementation", "")
        function_signature = shared.get("function_signature", "")
        language = shared.get("language", "python")
        test_cases = shared.get("test_cases", [])
        
        return {
            "code_implementation": code_implementation,
            "function_signature": function_signature,
            "language": language,
            "test_cases": test_cases
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run test cases against the code implementation.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with test results
        """
        # Initialize test results
        test_results = {
            "total_tests": len(inputs["test_cases"]),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "all_passed": False
        }
        
        # If there are no test cases, return empty results
        if not inputs["test_cases"]:
            return test_results
        
        # Run each test case
        for i, test_case in enumerate(inputs["test_cases"]):
            # Get input and expected output
            test_input = test_case.get("input", "")
            expected_output = test_case.get("output", "")
            description = test_case.get("description", f"Test case {i+1}")
            
            try:
                # Execute the code with the test input
                # Extract function name from signature
                function_name = "solution"
                if inputs["function_signature"]:
                    # Try to extract function name from signature
                    if "def " in inputs["function_signature"]:
                        function_name = inputs["function_signature"].split("def ")[1].split("(")[0].strip()
                
                # Create a temporary file for the code
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                    temp_file.write(inputs["code_implementation"])
                    temp_file_path = temp_file.name
                
                try:
                    # Create test runner code
                    # Handle different input formats
                    if isinstance(test_input, list) and len(test_input) >= 2:
                        # For two sum problem, input is [nums, target]
                        nums = test_input[0]
                        target = test_input[1]
                        test_runner = f"""
import sys
sys.path.insert(0, '{os.path.dirname(temp_file_path)}')
from {os.path.basename(temp_file_path)[:-3]} import {function_name}

# Test case {i+1}
nums = {nums}
target = {target}
try:
    result = {function_name}(nums, target)
    print(f"RESULT: {{result}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
"""
                    else:
                        # Default handling for other function signatures
                        test_runner = f"""
import sys
sys.path.insert(0, '{os.path.dirname(temp_file_path)}')
from {os.path.basename(temp_file_path)[:-3]} import {function_name}

# Test case {i+1}
test_input = {test_input}
try:
    result = {function_name}(*test_input)
    print(f"RESULT: {{result}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
"""
                    
                    # Execute the test
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as runner_file:
                        runner_file.write(test_runner)
                        runner_path = runner_file.name
                    
                    try:
                        process = subprocess.run(
                            [sys.executable, runner_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        # Parse the output
                        output_lines = process.stdout.strip().split('\n')
                        result_line = next((line for line in output_lines if line.startswith("RESULT:")), None)
                        error_line = next((line for line in output_lines if line.startswith("ERROR:")), None)
                        
                        if result_line:
                            actual_output = result_line[len("RESULT:"):].strip()
                        elif error_line:
                            actual_output = error_line[len("ERROR:"):].strip()
                        else:
                            actual_output = "No output"
                    finally:
                        if os.path.exists(runner_path):
                            os.unlink(runner_path)
                finally:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                
                # Compare actual and expected output
                passed = str(actual_output) == str(expected_output)
                
                # Update test results
                if passed:
                    test_results["passed_tests"] += 1
                else:
                    test_results["failed_tests"] += 1
                
                # Add test detail
                test_results["test_details"].append({
                    "test_case": i + 1,
                    "description": description,
                    "input": test_input,
                    "expected_output": expected_output,
                    "actual_output": actual_output,
                    "passed": passed
                })
                
            except Exception as e:
                # Handle execution errors
                test_results["failed_tests"] += 1
                test_results["test_details"].append({
                    "test_case": i + 1,
                    "description": description,
                    "input": test_input,
                    "expected_output": expected_output,
                    "actual_output": f"Error: {str(e)}",
                    "passed": False,
                    "error": str(e)
                })
        
        # Determine if all tests passed
        test_results["all_passed"] = test_results["failed_tests"] == 0
        
        return test_results
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the test results and determine the next action.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with test results
        shared["test_results"] = exec_res
        
        # Update iteration count
        current_iteration = shared.get("iteration", 0)
        shared["iteration"] = current_iteration + 1
        
        # Determine next action based on test results
        if exec_res["all_passed"]:
            # All tests passed, move to output
            shared["next_action"] = "output"
            return "output"
        else:
            # Some tests failed, check if we should continue with feedback loop
            max_iterations = shared.get("max_iterations", 3)
            if current_iteration < max_iterations:
                # Continue with feedback loop
                shared["next_action"] = "feedback_loop"
                return "feedback_loop"
            else:
                # Max iterations reached, move to output
                shared["next_action"] = "output"
                return "output"