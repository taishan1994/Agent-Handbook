"""
LLM Client for LeetCode Agent

This module provides a client for interacting with LLM APIs (OpenAI).
"""

import os
from typing import Dict, List, Optional, Any

try:
    import openai
    from openai import OpenAI
except ImportError:
    raise ImportError("OpenAI package is required. Install with: pip install openai")


class LLMClient:
    """
    Client for interacting with LLM APIs.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            model: The model to use (default: gpt-3.5-turbo)
            api_key: OpenAI API key (if not provided, uses OPENAI_API_KEY env variable)
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            
        self.client = OpenAI(api_key="empty", base_url="http://192.168.16.2:18001/v1")
        self.model = self.client.models.list().data[0].id
        print(self.model)

    def chat_completion(
        self, 
        messages, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate
            response_format: Response format (e.g., {"type": "json_object"})
            
        Returns:
            The generated text response
        """
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        if response_format:
            params["response_format"] = response_format
        
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    def generate_structured_response(
        self, 
        prompt: str, 
        system_message: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        output_format: str = "yaml"
    ) -> Dict[str, Any]:
        """
        Generate a structured response in YAML or JSON format.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            output_format: "yaml" or "json"
            
        Returns:
            Parsed structured data as a dictionary
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        messages.append({"role": "user", "content": prompt})
        
        # Set response format based on output format
        response_format = None
        if output_format.lower() == "json":
            response_format = {"type": "json_object"}
        
        response_text = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )

        if output_format.lower() == "python3":
            start = response_text.find("```python3") + len("```python3")
            end = response_text.find("```", start)
            if end != -1:
                python3_code = response_text[start:end].strip()
                return {
                    "full_text": response_text,
                    "python3_code": python3_code,
                }
        # Parse the response
        try:
            if output_format.lower() == "json":
                import json
                return json.loads(response_text)
            else:  # Default to YAML
                import yaml
                
                # Try to parse as-is first
                try:
                    return yaml.safe_load(response_text)
                except:
                    # If that fails, try to extract YAML content from code blocks
                    if "```yaml" in response_text:
                        # Extract content between ```yaml and ```
                        start = response_text.find("```yaml") + 7
                        end = response_text.find("```", start)
                        if end != -1:
                            yaml_content = response_text[start:end].strip()
                            return yaml.safe_load(yaml_content)
                    elif "```" in response_text:
                        # Extract content between first ``` and next ```
                        start = response_text.find("```") + 3
                        end = response_text.find("```", start)
                        if end != -1:
                            content = response_text[start:end].strip()
                            return yaml.safe_load(content)
                    
                    # If all else fails, raise the original exception
                    raise
        except Exception as e:
            raise ValueError(f"Failed to parse structured response: {e}\nResponse text: {response_text}")