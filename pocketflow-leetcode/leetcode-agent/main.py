#!/usr/bin/env python3
"""
LeetCode Agent - Main Entry Point

This is the main entry point for the LeetCode problem solving agent.
"""

import os
import sys
import argparse
import traceback
from pathlib import Path

# Add the current directory to the path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow import run_leetcode_flow
from utils.logger import get_logger


def main():
    """Main function to run the LeetCode agent."""
    # Initialize logger
    logger = get_logger("leetcode_main")
    logger.info("Starting LeetCode Agent")
    
    parser = argparse.ArgumentParser(description="LeetCode Problem Solving Agent")
    
    parser.add_argument(
        "problem_input",
        help="LeetCode problem URL or problem description"
    )
    
    parser.add_argument(
        "--language", "-l",
        default="python",
        choices=["python", "java", "cpp", "javascript"],
        help="Programming language for the solution (default: python)"
    )
    
    parser.add_argument(
        "--optimize", "-o",
        default="time",
        choices=["time", "space"],
        help="Optimization target: time or space (default: time)"
    )
    
    parser.add_argument(
        "--max-iterations", "-m",
        type=int,
        default=3,
        help="Maximum number of iterations for the feedback loop (default: 3)"
    )
    
    parser.add_argument(
        "--output", "-out",
        help="Output file to save the result (optional)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Problem input: {args.problem_input}")
    logger.info(f"Language: {args.language}, Optimization: {args.optimize}")
    
    # Run the LeetCode flow
    print(f"Starting LeetCode agent for problem: {args.problem_input}")
    print(f"Language: {args.language}, Optimization: {args.optimize}")
    print("-" * 50)
    
    try:
        logger.info("Running LeetCode flow")
        result = run_leetcode_flow(
            problem_input=args.problem_input,
            language=args.language,
            optimize_for=args.optimize,
            max_iterations=args.max_iterations,
        )
        
        logger.info("LeetCode flow completed successfully")
        
        # Print the result
        print("\n" + "=" * 50)
        print("SOLUTION RESULT")
        print("=" * 50)
        
        if "output" in result and result["output"]:
            print(result["output"])
        else:
            print("No solution was generated.")
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                if "output" in result and result["output"]:
                    f.write(result["output"])
                else:
                    f.write("No solution was generated.")
            
            print(f"\nResult saved to: {output_path}")
            logger.info(f"Result saved to: {output_path}")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        
        # Log detailed error with traceback
        logger.error(error_msg)
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()