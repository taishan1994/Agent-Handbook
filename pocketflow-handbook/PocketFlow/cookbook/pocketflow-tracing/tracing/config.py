"""
Configuration module for PocketFlow tracing with Langfuse.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class TracingConfig:
    """Configuration class for PocketFlow tracing with Langfuse."""
    
    # Langfuse configuration
    langfuse_secret_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_host: Optional[str] = None
    
    # PocketFlow tracing configuration
    debug: bool = False
    trace_inputs: bool = True
    trace_outputs: bool = True
    trace_prep: bool = True
    trace_exec: bool = True
    trace_post: bool = True
    trace_errors: bool = True
    
    # Session configuration
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "TracingConfig":
        """
        Create TracingConfig from environment variables.
        
        Args:
            env_file: Optional path to .env file. If None, looks for .env in current directory.
            
        Returns:
            TracingConfig instance with values from environment variables.
        """
        # Load environment variables from .env file if it exists
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env file in current directory or parent directories
            load_dotenv()
        
        return cls(
            langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            langfuse_host=os.getenv("LANGFUSE_HOST"),
            debug=os.getenv("POCKETFLOW_TRACING_DEBUG", "false").lower() == "true",
            trace_inputs=os.getenv("POCKETFLOW_TRACE_INPUTS", "true").lower() == "true",
            trace_outputs=os.getenv("POCKETFLOW_TRACE_OUTPUTS", "true").lower() == "true",
            trace_prep=os.getenv("POCKETFLOW_TRACE_PREP", "true").lower() == "true",
            trace_exec=os.getenv("POCKETFLOW_TRACE_EXEC", "true").lower() == "true",
            trace_post=os.getenv("POCKETFLOW_TRACE_POST", "true").lower() == "true",
            trace_errors=os.getenv("POCKETFLOW_TRACE_ERRORS", "true").lower() == "true",
            session_id=os.getenv("POCKETFLOW_SESSION_ID"),
            user_id=os.getenv("POCKETFLOW_USER_ID"),
        )
    
    def validate(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        if not self.langfuse_secret_key:
            if self.debug:
                print("Warning: LANGFUSE_SECRET_KEY not set")
            return False
            
        if not self.langfuse_public_key:
            if self.debug:
                print("Warning: LANGFUSE_PUBLIC_KEY not set")
            return False
            
        if not self.langfuse_host:
            if self.debug:
                print("Warning: LANGFUSE_HOST not set")
            return False
            
        return True
    
    def to_langfuse_kwargs(self) -> dict:
        """
        Convert configuration to kwargs for Langfuse client initialization.
        
        Returns:
            Dictionary of kwargs for Langfuse client.
        """
        kwargs = {}
        
        if self.langfuse_secret_key:
            kwargs["secret_key"] = self.langfuse_secret_key
            
        if self.langfuse_public_key:
            kwargs["public_key"] = self.langfuse_public_key
            
        if self.langfuse_host:
            kwargs["host"] = self.langfuse_host
            
        if self.debug:
            kwargs["debug"] = True
            
        return kwargs
