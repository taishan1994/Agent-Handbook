import sys
from flow import create_code_generator_flow

def main():
    """Runs the PocketFlow Code Generator application."""
    print("Starting PocketFlow Code Generator...")
    
    # Check if problem is provided as argument
    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])
    else:
        # Default Two Sum problem
        problem = """Two Sum

Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

Example 1:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]

Example 2:
Input: nums = [3,2,4], target = 6
Output: [1,2]

Example 3:
Input: nums = [3,3], target = 6
Output: [0,1]"""

    shared = {
        "problem": problem,
        "test_cases": [],  # Will be populated with [{name, input, expected}, ...]
        "function_code": "",
        "test_results": [],
        "iteration_count": 0,
        "max_iterations": 5
    }

    # Create and run the flow
    flow = create_code_generator_flow()
    flow.run(shared)
    
    print("\n=== Final Results ===")
    print(f"Problem: {shared['problem'][:50]}...")
    print(f"Iterations: {shared['iteration_count']}")
    print(f"Function:\n{shared['function_code']}")
    print(f"Test Results: {len([r for r in shared['test_results'] if r['passed']])}/{len(shared['test_results'])} passed")

if __name__ == "__main__":
    main() 