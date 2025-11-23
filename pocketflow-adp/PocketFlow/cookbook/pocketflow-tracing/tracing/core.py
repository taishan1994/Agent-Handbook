"""
Core tracing functionality for PocketFlow with Langfuse integration.
"""

import json
import time
import uuid
from typing import Any, Dict, Optional, Union
from datetime import datetime

try:
    from langfuse import Langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    print("Warning: langfuse package not installed. Install with: pip install langfuse")

from .config import TracingConfig


class LangfuseTracer:
    """
    Core tracer class that handles Langfuse integration for PocketFlow.
    """

    def __init__(self, config: TracingConfig):
        """
        Initialize the LangfuseTracer.

        Args:
            config: TracingConfig instance with Langfuse settings.
        """
        self.config = config
        self.client = None
        self.current_trace = None
        self.spans = {}  # Store spans by node ID

        if LANGFUSE_AVAILABLE and config.validate():
            try:
                # Initialize Langfuse client with proper parameters
                kwargs = {}
                if config.langfuse_secret_key:
                    kwargs["secret_key"] = config.langfuse_secret_key
                if config.langfuse_public_key:
                    kwargs["public_key"] = config.langfuse_public_key
                if config.langfuse_host:
                    kwargs["host"] = config.langfuse_host
                if config.debug:
                    kwargs["debug"] = True

                self.client = Langfuse(**kwargs)
                if config.debug:
                    print(
                        f"✓ Langfuse client initialized with host: {config.langfuse_host}"
                    )
            except Exception as e:
                if config.debug:
                    print(f"✗ Failed to initialize Langfuse client: {e}")
                self.client = None
        else:
            if config.debug:
                print("✗ Langfuse not available or configuration invalid")

    def start_trace(self, flow_name: str, input_data: Dict[str, Any]) -> Optional[str]:
        """
        Start a new trace for a flow execution.

        Args:
            flow_name: Name of the flow being traced.
            input_data: Input data for the flow.

        Returns:
            Trace ID if successful, None otherwise.
        """
        if not self.client:
            return None

        try:
            # Serialize input data safely
            serialized_input = self._serialize_data(input_data)

            # Use Langfuse v2 API to create a trace
            self.current_trace = self.client.trace(
                name=flow_name,
                input=serialized_input,
                metadata={
                    "framework": "PocketFlow",
                    "trace_type": "flow_execution",
                    "timestamp": datetime.now().isoformat(),
                },
                session_id=self.config.session_id,
                user_id=self.config.user_id,
            )

            # Get the trace ID
            trace_id = self.current_trace.id

            if self.config.debug:
                print(f"✓ Started trace: {trace_id} for flow: {flow_name}")

            return trace_id

        except Exception as e:
            if self.config.debug:
                print(f"✗ Failed to start trace: {e}")
            return None

    def end_trace(self, output_data: Dict[str, Any], status: str = "success") -> None:
        """
        End the current trace.

        Args:
            output_data: Output data from the flow.
            status: Status of the trace execution.
        """
        if not self.current_trace:
            return

        try:
            # Serialize output data safely
            serialized_output = self._serialize_data(output_data)

            # Update the trace with output data using v2 API
            self.current_trace.update(
                output=serialized_output,
                metadata={
                    "status": status,
                    "end_timestamp": datetime.now().isoformat(),
                },
            )

            if self.config.debug:
                print(f"✓ Ended trace with status: {status}")

        except Exception as e:
            if self.config.debug:
                print(f"✗ Failed to end trace: {e}")
        finally:
            self.current_trace = None
            self.spans.clear()

    def start_node_span(
        self, node_name: str, node_id: str, phase: str
    ) -> Optional[str]:
        """
        Start a span for a node execution phase.

        Args:
            node_name: Name/type of the node.
            node_id: Unique identifier for the node instance.
            phase: Execution phase (prep, exec, post).

        Returns:
            Span ID if successful, None otherwise.
        """
        if not self.current_trace:
            return None

        try:
            span_id = f"{node_id}_{phase}"

            # Create a child span using v2 API
            span = self.current_trace.span(
                name=f"{node_name}.{phase}",
                metadata={
                    "node_type": node_name,
                    "node_id": node_id,
                    "phase": phase,
                    "start_timestamp": datetime.now().isoformat(),
                },
            )

            self.spans[span_id] = span

            if self.config.debug:
                print(f"✓ Started span: {span_id}")

            return span_id

        except Exception as e:
            if self.config.debug:
                print(f"✗ Failed to start span: {e}")
            return None

    def end_node_span(
        self,
        span_id: str,
        input_data: Any = None,
        output_data: Any = None,
        error: Exception = None,
    ) -> None:
        """
        End a node execution span.

        Args:
            span_id: ID of the span to end.
            input_data: Input data for the phase.
            output_data: Output data from the phase.
            error: Exception if the phase failed.
        """
        if span_id not in self.spans:
            return

        try:
            span = self.spans[span_id]

            # Prepare update data
            update_data = {}

            if input_data is not None and self.config.trace_inputs:
                update_data["input"] = self._serialize_data(input_data)
            if output_data is not None and self.config.trace_outputs:
                update_data["output"] = self._serialize_data(output_data)

            if error and self.config.trace_errors:
                update_data.update(
                    {
                        "level": "ERROR",
                        "status_message": str(error),
                        "metadata": {
                            "error_type": type(error).__name__,
                            "error_message": str(error),
                            "end_timestamp": datetime.now().isoformat(),
                        },
                    }
                )
            else:
                update_data.update(
                    {
                        "level": "DEFAULT",
                        "metadata": {"end_timestamp": datetime.now().isoformat()},
                    }
                )

            # Update the span with all data at once
            span.update(**update_data)

            # End the span
            span.end()

            if self.config.debug:
                status = "ERROR" if error else "SUCCESS"
                print(f"✓ Ended span: {span_id} with status: {status}")

        except Exception as e:
            if self.config.debug:
                print(f"✗ Failed to end span: {e}")
        finally:
            if span_id in self.spans:
                del self.spans[span_id]

    def _serialize_data(self, data: Any) -> Any:
        """
        Safely serialize data for Langfuse.

        Args:
            data: Data to serialize.

        Returns:
            Serialized data that can be sent to Langfuse.
        """
        try:
            # Handle common PocketFlow data types
            if hasattr(data, "__dict__"):
                # Convert objects to dict representation
                return {"_type": type(data).__name__, "_data": str(data)}
            elif isinstance(data, (dict, list, str, int, float, bool, type(None))):
                # JSON-serializable types
                return data
            else:
                # Fallback to string representation
                return {"_type": type(data).__name__, "_data": str(data)}
        except Exception:
            # Ultimate fallback
            return {"_type": "unknown", "_data": "<serialization_failed>"}

    def flush(self) -> None:
        """Flush any pending traces to Langfuse."""
        if self.client:
            try:
                self.client.flush()
                if self.config.debug:
                    print("✓ Flushed traces to Langfuse")
            except Exception as e:
                if self.config.debug:
                    print(f"✗ Failed to flush traces: {e}")
