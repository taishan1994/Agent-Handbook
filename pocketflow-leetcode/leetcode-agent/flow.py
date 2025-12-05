"""
Main Flow for LeetCode Agent

This module defines the main workflow for the LeetCode problem solving agent.
"""

import os
import sys
import traceback

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Flow
from nodes.user_input import UserInputNode
from nodes.parse_problem import ParseProblemNode
from nodes.solution_design import SolutionDesignNode
from nodes.code_gen import CodeGenNode
from nodes.test_case_gen import TestCaseGenNode
from nodes.test_run import TestRunNode
from nodes.feedback_loop import FeedbackLoopNode
from nodes.output import OutputNode
from utils.llm_client import LLMClient
from utils.code_executor import CodeExecutor
from utils.logger import get_logger


def create_leetcode_flow(llm_client: LLMClient, code_executor: CodeExecutor) -> Flow:
    """
    Create the LeetCode problem solving workflow.
    
    Args:
        llm_client: LLM client instance
        code_executor: Code executor instance
        
    Returns:
        Configured workflow for LeetCode problem solving
    """
    # Initialize logger
    logger = get_logger("leetcode_flow")
    logger.info("Creating LeetCode workflow")
    
    try:
        # Create nodes
        logger.debug("Creating workflow nodes")
        user_input_node = UserInputNode()
        parse_problem_node = ParseProblemNode(llm_client)
        solution_design_node = SolutionDesignNode(llm_client)
        code_gen_node = CodeGenNode(llm_client)
        test_case_gen_node = TestCaseGenNode(llm_client)
        test_run_node = TestRunNode(code_executor)
        feedback_loop_node = FeedbackLoopNode(llm_client)
        output_node = OutputNode()
        
        # Define the main flow path using >> operator
        logger.debug("Defining main flow path")
        user_input_node >> parse_problem_node
        parse_problem_node >> solution_design_node
        solution_design_node >> code_gen_node
        code_gen_node >> test_case_gen_node
        test_case_gen_node >> test_run_node
        
        # Define conditional paths from test_run using - "action" >> operator
        logger.debug("Defining conditional paths")
        test_run_node - "output" >> output_node
        test_run_node - "feedback_loop" >> feedback_loop_node
        
        # Define feedback loop path
        feedback_loop_node - "code_gen" >> code_gen_node
        
        # Create the workflow with user_input_node as the starting point
        logger.debug("Creating Flow instance")
        flow = Flow(start=user_input_node)
        
        logger.info("LeetCode workflow created successfully")
        return flow
        
    except Exception as e:
        logger.error(f"Error creating LeetCode workflow: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise


def run_leetcode_flow(problem_input: str, language: str = "python", optimize_for: str = "time", 
                      max_iterations: int = 3) -> dict:
    """
    Run the LeetCode problem solving workflow.
    
    Args:
        problem_input: Problem URL or description
        language: Programming language for the solution
        optimize_for: Optimization target ("time" or "space")
        max_iterations: Maximum number of iterations for the feedback loop
        
    Returns:
        Dictionary with the results of the workflow
    """
    # Initialize logger
    logger = get_logger("leetcode_flow")
    logger.info(f"Running LeetCode flow with problem: {problem_input}")
    logger.info(f"Language: {language}, Optimization: {optimize_for}, Max iterations: {max_iterations}")
    
    try:
        # Initialize LLM client and code executor
        logger.debug("Initializing LLM client and code executor")
        llm_client = LLMClient()
        code_executor = CodeExecutor()
        
        # Create the workflow
        logger.debug("Creating workflow")
        flow = create_leetcode_flow(llm_client, code_executor)
        
        # Initialize shared state
        logger.debug("Initializing shared state")
        shared_state = {
            "problem_input": problem_input,
            "language": language,
            "optimize_for": optimize_for,
            "max_iterations": max_iterations,
            "iteration": 0
        }
        
        # Run the workflow
        logger.info("Starting workflow execution")
        result = flow.run(shared_state)
        logger.info("Workflow execution completed")
        
        # Extract the formatted output from the shared state
        formatted_output = shared_state.get("formatted_output", "")
        
        return {
            "output": formatted_output,
            "success": shared_state.get("success", False),
            "shared_state": shared_state
        }
        
    except Exception as e:
        logger.error(f"Error running LeetCode flow: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise