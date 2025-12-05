"""
Code Executor for LeetCode Agent

This module provides utilities for executing generated code in a sandboxed environment.
"""

import subprocess
import sys
import os
import tempfile
import traceback
from typing import Dict, List, Any, Optional, Tuple


class CodeExecutor:
    """
    Executes code in a sandboxed environment.
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the code executor.
        
        Args:
            timeout: Maximum execution time in seconds
        """
        self.timeout = timeout
    
    def execute_python_code(
        self, 
        code: str, 
        test_cases: List[Dict[str, Any]], 
        function_name: str = "solution"
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Execute Python code with test cases.
        
        Args:
            code: The Python code to execute
            test_cases: List of test case dictionaries
            function_name: Name of the solution function
            
        Returns:
            Tuple of (all_passed, test_results)
        """
        test_results = []
        all_passed = True
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            for i, test_case in enumerate(test_cases):
                # Prepare test execution
                inputs = test_case.get('input', [])
                expected_output = test_case.get('output', None)
                
                # Create test runner code
                test_runner = f"""
import sys
sys.path.insert(0, '{os.path.dirname(temp_file_path)}')
from {os.path.basename(temp_file_path)[:-3]} import {function_name}

# Test case {i+1}
inputs = {inputs}
try:
    result = {function_name}(*inputs)
    print(f"RESULT: {{result}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    traceback.print_exc()
"""
                
                # Execute the test
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as runner_file:
                    runner_file.write(test_runner)
                    runner_path = runner_file.name
                
                try:
                    # Run the test
                    process = subprocess.run(
                        [sys.executable, runner_path],
                        capture_output=True,
                        text=True,
                        timeout=self.timeout
                    )
                    
                    # Parse the output
                    output_lines = process.stdout.strip().split('\n')
                    result_line = next((line for line in output_lines if line.startswith("RESULT:")), None)
                    error_line = next((line for line in output_lines if line.startswith("ERROR:")), None)
                    
                    if result_line:
                        # Extract the actual result
                        actual_output = result_line[len("RESULT:"):].strip()
                        
                        # Try to evaluate the result to get the actual Python object
                        try:
                            actual_output = eval(actual_output)
                        except:
                            pass  # Keep as string if evaluation fails
                        
                        # Compare with expected output
                        passed = actual_output == expected_output
                    elif error_line:
                        actual_output = error_line[len("ERROR:"):].strip()
                        passed = False
                    else:
                        actual_output = "No output"
                        passed = False
                    
                    # Record the test result
                    test_result = {
                        "test_case": i + 1,
                        "input": inputs,
                        "expected": expected_output,
                        "actual": actual_output,
                        "passed": passed,
                        "error": None if passed else actual_output,
                        "stdout": process.stdout,
                        "stderr": process.stderr
                    }
                    
                    test_results.append(test_result)
                    
                    if not passed:
                        all_passed = False
                
                except subprocess.TimeoutExpired:
                    test_result = {
                        "test_case": i + 1,
                        "input": inputs,
                        "expected": expected_output,
                        "actual": "Timeout",
                        "passed": False,
                        "error": f"Execution timed out after {self.timeout} seconds",
                        "stdout": "",
                        "stderr": ""
                    }
                    
                    test_results.append(test_result)
                    all_passed = False
                
                finally:
                    # Clean up the runner file
                    if os.path.exists(runner_path):
                        os.unlink(runner_path)
        
        finally:
            # Clean up the temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        return all_passed, test_results
    
    def execute_code_safely(
        self, 
        code: str, 
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Execute code safely and return the result.
        
        Args:
            code: The code to execute
            language: Programming language
            
        Returns:
            Dictionary with execution results
        """
        if language.lower() != "python":
            return {
                "success": False,
                "error": f"Language {language} not supported yet",
                "stdout": "",
                "stderr": ""
            }
        
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Execute the code
                process = subprocess.run(
                    [sys.executable, temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "error": None if process.returncode == 0 else process.stderr,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "returncode": process.returncode
                }
            
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Execution timed out after {self.timeout} seconds",
                    "stdout": "",
                    "stderr": ""
                }
        
        finally:
            # Clean up the temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)