"""
Code Execution Tool - Tool for executing code in multiple languages

Supports executing Python and JavaScript code snippets
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from .base import Tool, ToolResult


class CodeExecutionTool(Tool):
    """Tool to execute code in various languages"""

    def __init__(self):
        self.supported_languages = {
            "python": "python3",
            "javascript": "node",
            "js": "node",
        }

    @property
    def name(self) -> str:
        return "execute_code"

    @property
    def description(self) -> str:
        return "Execute code in specified language (python, javascript). Returns the output or error."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code to execute",
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "js"],
                    "description": "Programming language to use",
                },
            },
            "required": ["code", "language"],
        }

    async def execute(self, code: str, language: str = "python") -> ToolResult:
        """Execute code in specified language"""
        if language not in self.supported_languages:
            return ToolResult(
                success=False,
                content="",
                error=f"Unsupported language: {language}. Supported: {list(self.supported_languages.keys())}",
            )

        interpreter = self.supported_languages[language]

        try:
            result = subprocess.run(
                [interpreter, "-c", code],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return ToolResult(success=True, content=result.stdout)
            else:
                return ToolResult(
                    success=False,
                    content=result.stdout,
                    error=f"Execution failed (exit code {result.returncode}): {result.stderr}",
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                content="",
                error="Code execution timed out (30s limit)",
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                content="",
                error=f"Interpreter not found: {interpreter}. Please install {language}.",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Execution error: {str(e)}",
            )


class ExecuteScriptTool(Tool):
    """Tool to execute script files"""

    def __init__(self):
        self.supported_languages = {
            "python": "python3",
            "javascript": "node",
            "js": "node",
            "bash": "bash",
            "sh": "bash",
        }

    @property
    def name(self) -> str:
        return "execute_script"

    @property
    def description(self) -> str:
        return "Execute a script file (python, javascript, bash). Returns the output or error."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "script_path": {
                    "type": "string",
                    "description": "Absolute path to the script file to execute",
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "js", "bash", "sh"],
                    "description": "Programming language of the script",
                },
            },
            "required": ["script_path", "language"],
        }

    async def execute(self, script_path: str, language: str = "python") -> ToolResult:
        """Execute script file"""
        if language not in self.supported_languages:
            return ToolResult(
                success=False,
                content="",
                error=f"Unsupported language: {language}. Supported: {list(self.supported_languages.keys())}",
            )

        interpreter = self.supported_languages[language]
        script_file = Path(script_path)

        if not script_file.exists():
            return ToolResult(
                success=False,
                content="",
                error=f"Script file not found: {script_path}",
            )

        try:
            result = subprocess.run(
                [interpreter, str(script_file)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(script_file.parent),
            )

            if result.returncode == 0:
                return ToolResult(success=True, content=result.stdout)
            else:
                return ToolResult(
                    success=False,
                    content=result.stdout,
                    error=f"Execution failed (exit code {result.returncode}): {result.stderr}",
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                content="",
                error="Script execution timed out (60s limit)",
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                content="",
                error=f"Interpreter not found: {interpreter}. Please install {language}.",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Execution error: {str(e)}",
            )


def create_code_execution_tools() -> list:
    """Create code execution tools"""
    return [
        CodeExecutionTool(),
        ExecuteScriptTool(),
    ]
