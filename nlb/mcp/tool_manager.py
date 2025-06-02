from typing import Any, Callable, Protocol


class ToolManager(Protocol):
    @property
    def tool_functions(self) -> list[Callable[..., Any]]:
        """Return a list of tool functions for this tool.

        A tool function must return a string output, but it can
        take on any number of (JSON schema-able) arguments.
        """
        ...
