"""
Decorator for tracing PocketFlow workflows with Langfuse.
"""

import functools
import inspect
import uuid
from typing import Any, Callable, Dict, Optional, Union

from .config import TracingConfig
from .core import LangfuseTracer


def trace_flow(
    config: Optional[TracingConfig] = None,
    flow_name: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Decorator to add Langfuse tracing to PocketFlow flows.
    
    This decorator automatically traces:
    - Flow execution start/end
    - Each node's prep, exec, and post phases
    - Input and output data for each phase
    - Errors and exceptions
    
    Args:
        config: TracingConfig instance. If None, loads from environment.
        flow_name: Custom name for the flow. If None, uses the flow class name.
        session_id: Session ID for grouping related traces.
        user_id: User ID for the trace.
        
    Returns:
        Decorated flow class or function.
        
    Example:
        ```python
        from tracing import trace_flow
        
        @trace_flow()
        class MyFlow(Flow):
            def __init__(self):
                super().__init__(start=MyNode())
        
        # Or with custom configuration
        config = TracingConfig.from_env()
        
        @trace_flow(config=config, flow_name="CustomFlow")
        class MyFlow(Flow):
            pass
        ```
    """
    def decorator(flow_class_or_func):
        # Handle both class and function decoration
        if inspect.isclass(flow_class_or_func):
            return _trace_flow_class(flow_class_or_func, config, flow_name, session_id, user_id)
        else:
            return _trace_flow_function(flow_class_or_func, config, flow_name, session_id, user_id)
    
    return decorator


def _trace_flow_class(flow_class, config, flow_name, session_id, user_id):
    """Trace a Flow class by wrapping its methods."""
    
    # Get or create config
    if config is None:
        config = TracingConfig.from_env()
    
    # Override session/user if provided
    if session_id:
        config.session_id = session_id
    if user_id:
        config.user_id = user_id
    
    # Get flow name
    if flow_name is None:
        flow_name = flow_class.__name__
    
    # Store original methods
    original_init = flow_class.__init__
    original_run = getattr(flow_class, 'run', None)
    original_run_async = getattr(flow_class, 'run_async', None)
    
    def traced_init(self, *args, **kwargs):
        """Initialize the flow with tracing capabilities."""
        # Call original init
        original_init(self, *args, **kwargs)
        
        # Add tracing attributes
        self._tracer = LangfuseTracer(config)
        self._flow_name = flow_name
        self._trace_id = None
        
        # Patch all nodes in the flow
        self._patch_nodes()
    
    def traced_run(self, shared):
        """Traced version of the run method."""
        if not hasattr(self, '_tracer'):
            # Fallback if not properly initialized
            return original_run(self, shared) if original_run else None
            
        # Start trace
        self._trace_id = self._tracer.start_trace(self._flow_name, shared)
        
        try:
            # Run the original flow
            result = original_run(self, shared) if original_run else None
            
            # End trace successfully
            self._tracer.end_trace(shared, "success")
            
            return result
            
        except Exception as e:
            # End trace with error
            self._tracer.end_trace(shared, "error")
            raise
        finally:
            # Ensure cleanup
            self._tracer.flush()
    
    async def traced_run_async(self, shared):
        """Traced version of the async run method."""
        if not hasattr(self, '_tracer'):
            # Fallback if not properly initialized
            return await original_run_async(self, shared) if original_run_async else None
            
        # Start trace
        self._trace_id = self._tracer.start_trace(self._flow_name, shared)
        
        try:
            # Run the original flow
            result = await original_run_async(self, shared) if original_run_async else None
            
            # End trace successfully
            self._tracer.end_trace(shared, "success")
            
            return result
            
        except Exception as e:
            # End trace with error
            self._tracer.end_trace(shared, "error")
            raise
        finally:
            # Ensure cleanup
            self._tracer.flush()
    
    def patch_nodes(self):
        """Patch all nodes in the flow to add tracing."""
        if not hasattr(self, 'start_node') or not self.start_node:
            return
            
        visited = set()
        nodes_to_patch = [self.start_node]
        
        while nodes_to_patch:
            node = nodes_to_patch.pop(0)
            if id(node) in visited:
                continue
                
            visited.add(id(node))
            
            # Patch this node
            self._patch_node(node)
            
            # Add successors to patch list
            if hasattr(node, 'successors'):
                for successor in node.successors.values():
                    if successor and id(successor) not in visited:
                        nodes_to_patch.append(successor)
    
    def patch_node(self, node):
        """Patch a single node to add tracing."""
        if hasattr(node, '_pocketflow_traced'):
            return  # Already patched
            
        node_id = str(uuid.uuid4())
        node_name = type(node).__name__
        
        # Store original methods
        original_prep = getattr(node, 'prep', None)
        original_exec = getattr(node, 'exec', None)
        original_post = getattr(node, 'post', None)
        original_prep_async = getattr(node, 'prep_async', None)
        original_exec_async = getattr(node, 'exec_async', None)
        original_post_async = getattr(node, 'post_async', None)
        
        # Create traced versions
        if original_prep:
            node.prep = self._create_traced_method(original_prep, node_id, node_name, 'prep')
        if original_exec:
            node.exec = self._create_traced_method(original_exec, node_id, node_name, 'exec')
        if original_post:
            node.post = self._create_traced_method(original_post, node_id, node_name, 'post')
        if original_prep_async:
            node.prep_async = self._create_traced_async_method(original_prep_async, node_id, node_name, 'prep')
        if original_exec_async:
            node.exec_async = self._create_traced_async_method(original_exec_async, node_id, node_name, 'exec')
        if original_post_async:
            node.post_async = self._create_traced_async_method(original_post_async, node_id, node_name, 'post')
        
        # Mark as traced
        node._pocketflow_traced = True
    
    def create_traced_method(self, original_method, node_id, node_name, phase):
        """Create a traced version of a synchronous method."""
        @functools.wraps(original_method)
        def traced_method(*args, **kwargs):
            span_id = self._tracer.start_node_span(node_name, node_id, phase)
            
            try:
                result = original_method(*args, **kwargs)
                self._tracer.end_node_span(span_id, input_data=args, output_data=result)
                return result
            except Exception as e:
                self._tracer.end_node_span(span_id, input_data=args, error=e)
                raise
                
        return traced_method
    
    def create_traced_async_method(self, original_method, node_id, node_name, phase):
        """Create a traced version of an asynchronous method."""
        @functools.wraps(original_method)
        async def traced_async_method(*args, **kwargs):
            span_id = self._tracer.start_node_span(node_name, node_id, phase)
            
            try:
                result = await original_method(*args, **kwargs)
                self._tracer.end_node_span(span_id, input_data=args, output_data=result)
                return result
            except Exception as e:
                self._tracer.end_node_span(span_id, input_data=args, error=e)
                raise
                
        return traced_async_method
    
    # Replace methods on the class
    flow_class.__init__ = traced_init
    flow_class._patch_nodes = patch_nodes
    flow_class._patch_node = patch_node
    flow_class._create_traced_method = create_traced_method
    flow_class._create_traced_async_method = create_traced_async_method
    
    if original_run:
        flow_class.run = traced_run
    if original_run_async:
        flow_class.run_async = traced_run_async
    
    return flow_class


def _trace_flow_function(flow_func, config, flow_name, session_id, user_id):
    """Trace a flow function (for functional-style flows)."""
    
    # Get or create config
    if config is None:
        config = TracingConfig.from_env()
    
    # Override session/user if provided
    if session_id:
        config.session_id = session_id
    if user_id:
        config.user_id = user_id
    
    # Get flow name
    if flow_name is None:
        flow_name = flow_func.__name__
    
    tracer = LangfuseTracer(config)
    
    @functools.wraps(flow_func)
    def traced_flow_func(*args, **kwargs):
        # Assume first argument is shared data
        shared = args[0] if args else {}
        
        # Start trace
        trace_id = tracer.start_trace(flow_name, shared)
        
        try:
            result = flow_func(*args, **kwargs)
            tracer.end_trace(shared, "success")
            return result
        except Exception as e:
            tracer.end_trace(shared, "error")
            raise
        finally:
            tracer.flush()
    
    return traced_flow_func
