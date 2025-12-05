import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

def execute_python(function_code, input):
    try:
        namespace = {"__builtins__": __builtins__}
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(function_code, namespace)
            
            if "run_code" not in namespace:
                return None, "Function 'run_code' not found"
            
            run_code = namespace["run_code"]
            
            if isinstance(input, dict):
                result = run_code(**input)
            elif isinstance(input, (list, tuple)):
                result = run_code(*input)
            else:
                result = run_code(input)
            
            return result, None
                
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)}"

if __name__ == "__main__":
    # Test 1: Working function
    function_code = """
def run_code(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    
    input = {"nums": [2, 7, 11, 15], "target": 9}
    output, error = execute_python(function_code, input)
    print(f"Output: {output}")
    print(f"Error: {error}")
    
    # Test 2: Function with error
    broken_function_code = """
def run_code(nums, target):
    return nums[100]  # Index error
"""
    
    output2, error2 = execute_python(broken_function_code, input)
    print(f"Output: {output2}")
    print(f"Error: {error2}") 