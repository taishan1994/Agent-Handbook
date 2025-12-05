"""
Validators for LeetCode Agent

This module provides validation utilities for various data structures.
"""

import re
import yaml
from typing import Dict, Any, List, Optional


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


def validate_problem_data(problem_data: Dict[str, Any]) -> bool:
    """
    Validate problem data structure.
    
    Args:
        problem_data: Dictionary containing problem information
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    required_fields = ['title', 'description']
    
    for field in required_fields:
        if field not in problem_data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate title
    if not problem_data['title'] or not isinstance(problem_data['title'], str):
        raise ValidationError("Title must be a non-empty string")
    
    # Validate description
    if not problem_data['description'] or not isinstance(problem_data['description'], str):
        raise ValidationError("Description must be a non-empty string")
    
    return True


def validate_solution_data(solution_data: Dict[str, Any]) -> bool:
    """
    Validate solution data structure.
    
    Args:
        solution_data: Dictionary containing solution information
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    required_fields = ['approach', 'time_complexity', 'space_complexity']
    
    for field in required_fields:
        if field not in solution_data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate approach
    if not solution_data['approach'] or not isinstance(solution_data['approach'], str):
        raise ValidationError("Approach must be a non-empty string")
    
    # Validate complexity fields
    for field in ['time_complexity', 'space_complexity']:
        if not solution_data[field] or not isinstance(solution_data[field], str):
            raise ValidationError(f"{field.replace('_', ' ').title()} must be a non-empty string")
    
    return True


def validate_code_data(code_data: Dict[str, Any]) -> bool:
    """
    Validate code data structure.
    
    Args:
        code_data: Dictionary containing code information
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    required_fields = ['language', 'implementation']
    
    for field in required_fields:
        if field not in code_data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate language
    if not code_data['language'] or not isinstance(code_data['language'], str):
        raise ValidationError("Language must be a non-empty string")
    
    # Validate implementation
    if not code_data['implementation'] or not isinstance(code_data['implementation'], str):
        raise ValidationError("Implementation must be a non-empty string")
    
    # Check if the implementation contains a function definition
    if code_data['language'].lower() == 'python':
        if not re.search(r'def\s+\w+\s*\(', code_data['implementation']):
            raise ValidationError("Python implementation must contain a function definition")
    
    return True


def validate_test_cases(test_cases: List[Dict[str, Any]]) -> bool:
    """
    Validate test cases structure.
    
    Args:
        test_cases: List of test case dictionaries
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if not test_cases or not isinstance(test_cases, list):
        raise ValidationError("Test cases must be a non-empty list")
    
    for i, test_case in enumerate(test_cases):
        if not isinstance(test_case, dict):
            raise ValidationError(f"Test case {i+1} must be a dictionary")
        
        # Check for required fields
        if 'input' not in test_case:
            raise ValidationError(f"Test case {i+1} missing 'input' field")
        
        if 'output' not in test_case:
            raise ValidationError(f"Test case {i+1} missing 'output' field")
    
    return True


def validate_yaml_response(yaml_str: str) -> Dict[str, Any]:
    """
    Validate and parse a YAML response.
    
    Args:
        yaml_str: YAML string to validate
        
    Returns:
        Parsed YAML dictionary
        
    Raises:
        ValidationError: If YAML is invalid
    """
    try:
        data = yaml.safe_load(yaml_str)
        
        if not isinstance(data, dict):
            raise ValidationError("YAML response must be a dictionary")
        
        return data
    
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML format: {e}")


def validate_leetcode_url(url: str) -> bool:
    """
    Validate if a URL is a valid LeetCode problem URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    # Check if it's a LeetCode URL
    leetcode_pattern = r'https?://(www\.)?leetcode\.com/problems/[^/]+/?'
    if not re.match(leetcode_pattern, url):
        raise ValidationError("URL must be a valid LeetCode problem URL")
    
    return True


def validate_language(language: str) -> bool:
    """
    Validate programming language.
    
    Args:
        language: Programming language string
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if not language or not isinstance(language, str):
        raise ValidationError("Language must be a non-empty string")
    
    supported_languages = ['python', 'cpp', 'java', 'javascript']
    if language.lower() not in supported_languages:
        raise ValidationError(f"Language must be one of: {', '.join(supported_languages)}")
    
    return True


def validate_optimization_target(target: str) -> bool:
    """
    Validate optimization target.
    
    Args:
        target: Optimization target string
        
    Returns:
        True if valid, raises ValidationError otherwise
    """
    if not target or not isinstance(target, str):
        raise ValidationError("Optimization target must be a non-empty string")
    
    valid_targets = ['time', 'space', 'readability']
    if target.lower() not in valid_targets:
        raise ValidationError(f"Optimization target must be one of: {', '.join(valid_targets)}")
    
    return True


def sanitize_code(code: str, language: str) -> str:
    """
    Sanitize code for safe execution.
    
    Args:
        code: Code string to sanitize
        language: Programming language
        
    Returns:
        Sanitized code string
    """
    if language.lower() != 'python':
        return code  # Only Python sanitization is implemented for now
    
    # Remove potentially dangerous imports and operations
    dangerous_patterns = [
        r'import\s+os',
        r'import\s+sys',
        r'import\s+subprocess',
        r'from\s+os\s+import',
        r'from\s+sys\s+import',
        r'from\s+subprocess\s+import',
        r'exec\s*\(',
        r'eval\s*\(',
        r'__import__\s*\(',
        r'open\s*\(',
        r'file\s*\(',
    ]
    
    sanitized_code = code
    
    for pattern in dangerous_patterns:
        sanitized_code = re.sub(pattern, '# REMOVED: ' + pattern, sanitized_code)
    
    return sanitized_code