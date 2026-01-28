"""简化版的 TodoListMiddleware，减少系统提示词长度"""

from typing import Any, Annotated

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.agents.middleware.todo import Todo, WRITE_TODOS_TOOL_DESCRIPTION
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.runtime import Runtime
from langgraph.types import Command
from typing_extensions import NotRequired, TypedDict, override

from langchain.agents.middleware.types import OmitFromInput
from langchain.tools import InjectedToolCallId


class PlanningState(AgentState[Any]):
    """State schema for the todo middleware."""

    todos: NotRequired[list[Todo]]


SIMPLIFIED_WRITE_TODOS_SYSTEM_PROMPT = """
You have access to the `write_todos` tool to help you manage and plan complex objectives.
Use this tool for complex objectives to ensure that you are tracking each necessary step.

## When to Use
- Complex multi-step tasks (3+ steps)
- User explicitly requests todo list
- User provides multiple tasks

## How to Use
- Mark task as in_progress BEFORE starting work
- Mark task as completed IMMEDIATELY after finishing
- Update todo list in real-time as you work

## When NOT to Use
- Single, straightforward task
- Task can be completed in less than 3 steps
- Purely conversational or informational task
"""


@tool(description=WRITE_TODOS_TOOL_DESCRIPTION)
def write_todos(
    todos: list[Todo], tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command[Any]:
    """Create and manage a structured task list for your current work session."""
    return Command(
        update={
            "todos": todos,
            "messages": [ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)],
        }
    )


class SimplifiedTodoListMiddleware(AgentMiddleware):
    """简化版的 TodoListMiddleware，减少系统提示词长度"""

    state_schema = PlanningState

    def __init__(
        self,
        *,
        system_prompt: str = SIMPLIFIED_WRITE_TODOS_SYSTEM_PROMPT,
        tool_description: str = WRITE_TODOS_TOOL_DESCRIPTION,
    ) -> None:
        super().__init__()
        self.system_prompt = system_prompt
        self.tool_description = tool_description

        @tool(description=self.tool_description)
        def write_todos(
            todos: list[Todo], tool_call_id: Annotated[str, InjectedToolCallId]
        ) -> Command[Any]:
            """Create and manage a structured task list for your current work session."""
            return Command(
                update={
                    "todos": todos,
                    "messages": [
                        ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)
                    ],
                }
            )

        self.tools = [write_todos]

    def wrap_model_call(
        self,
        request,
        handler,
    ):
        """Update the system message to include the todo system prompt."""
        if request.system_message is not None:
            new_system_content = [
                *request.system_message.content_blocks,
                {"type": "text", "text": f"\n\n{self.system_prompt}"},
            ]
        else:
            new_system_content = [{"type": "text", "text": self.system_prompt}]
        new_system_message = SystemMessage(content=new_system_content)
        return handler(request.override(system_message=new_system_message))

    async def awrap_model_call(
        self,
        request,
        handler,
    ):
        """Update the system message to include the todo system prompt."""
        if request.system_message is not None:
            new_system_content = [
                *request.system_message.content_blocks,
                {"type": "text", "text": f"\n\n{self.system_prompt}"},
            ]
        else:
            new_system_content = [{"type": "text", "text": self.system_prompt}]
        new_system_message = SystemMessage(content=new_system_content)
        return await handler(request.override(system_message=new_system_message))

    @override
    def after_model(self, state: AgentState[Any], runtime: Runtime) -> dict[str, Any] | None:
        """Check for parallel write_todos tool calls and return errors if detected."""
        messages = state["messages"]
        if not messages:
            return None

        last_ai_msg = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
        if not last_ai_msg or not last_ai_msg.tool_calls:
            return None

        write_todos_calls = [tc for tc in last_ai_msg.tool_calls if tc["name"] == "write_todos"]

        if len(write_todos_calls) > 1:
            error_messages = [
                ToolMessage(
                    content=(
                        "Error: The `write_todos` tool should never be called multiple times "
                        "in parallel. Please call it only once per model invocation to update "
                        "the todo list."
                    ),
                    tool_call_id=tc["id"],
                    status="error",
                )
                for tc in write_todos_calls
            ]
            return {"messages": error_messages}

        return None

    @override
    async def aafter_model(self, state: AgentState[Any], runtime: Runtime) -> dict[str, Any] | None:
        """Check for parallel write_todos tool calls and return errors if detected."""
        return self.after_model(state, runtime)
