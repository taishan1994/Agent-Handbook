"""
Parse Problem Node for LeetCode Agent

This node parses problem content from URLs or direct descriptions.
"""

import os
import sys
import traceback
from typing import Dict, Any

# Add the parent directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node
from nodes.parse_problem import ParseProblemNode
from utils.llm_client import LLMClient

client = LLMClient()
parse_problem_node = ParseProblemNode(llm_client=client)
parse_problem_node.run({"problem_input": "https://leetcode.com/problems/two-sum/"})
