# Chapter 1: Prompt Chaining with PocketFlow
"""
Prompt Chaining implementation using PocketFlow framework.
This module demonstrates the prompt chaining pattern for complex task decomposition.
"""

from .flow import (
    ExtractSpecificationsNode,
    TransformToJSONNode,
    ValidateJSONNode,
    extract_node,
    transform_node,
    validate_node,
    spec_flow
)

from .main import run_prompt_chaining_example

__all__ = [
    'ExtractSpecificationsNode',
    'TransformToJSONNode', 
    'ValidateJSONNode',
    'extract_node',
    'transform_node',
    'validate_node',
    'spec_flow',
    'run_prompt_chaining_example'
]