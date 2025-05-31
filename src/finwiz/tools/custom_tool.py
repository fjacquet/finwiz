"""
Provide a template for creating custom tools for CrewAI agents.

This file defines a sample custom tool `MyCustomTool` with an input schema
`MyCustomToolInput`. It serves as a starting point for developing new tools
tailored to specific project needs.
"""


from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""

    argument: str = Field(..., description="Description of the argument.")


class MyCustomTool(BaseTool):
    """
    An example custom tool for CrewAI.

    This tool demonstrates the basic structure of a custom tool,
    including defining a name, description, input schema, and the
    core `_run` method. It's intended to be a template for
    creating new, specific tools.
    """

    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, "
        "your agent will need this information to use it."
    )
    args_schema: type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        """
        Execute the custom tool's logic.

        This method contains the core implementation of the tool. It
        takes an argument as defined in the `args_schema` and returns
        a string result. The current implementation is a placeholder.

        Args:
            argument: The input argument for the tool, as described
                in MyCustomToolInput.

        Returns:
            A string representing the output of the tool's execution.

        """
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."
