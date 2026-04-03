"""MCP tool registry — registers and discovers MCP-style tools.

Provides a central registry for tools that follow the Model Context Protocol
pattern: each tool declares a name, description, JSON-schema for its inputs,
and an invocation handler.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class McpTool(Protocol):
    """Protocol describing an MCP-compatible tool."""

    name: str
    description: str
    input_schema: dict

    def invoke(self, args: dict) -> dict:
        """Execute the tool with the given arguments."""
        ...


class McpToolRegistry:
    """In-memory registry for MCP-style tools.

    Tools are registered by name and can be discovered and invoked at
    runtime.  ``discover_tools`` accepts a *session_context* dict so that
    downstream callers can filter the advertised tool set based on
    collaboration mode, policy constraints, or role.
    """

    def __init__(self) -> None:
        self._tools: dict[str, _RegisteredTool] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable[[dict], dict],
    ) -> None:
        """Register a tool in the registry.

        Args:
            name: Unique tool name.
            description: Human-readable description of the tool.
            input_schema: JSON-schema describing the tool's input.
            handler: Callable that executes the tool and returns a result dict.
        """
        self._tools[name] = _RegisteredTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_tools(self, session_context: dict | None = None) -> list[dict]:
        """Return the list of registered tools as serialisable dicts.

        *session_context* is reserved for downstream filtering (e.g. by
        collaboration mode or policy scope).  By default all registered
        tools are returned.
        """
        tools: list[dict] = []
        for tool in self._tools.values():
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
            )
        return tools

    # ------------------------------------------------------------------
    # Invocation
    # ------------------------------------------------------------------

    def invoke_tool(
        self, name: str, args: dict, session_context: dict | None = None
    ) -> dict:
        """Invoke a registered tool by name.

        Args:
            name: The tool name.
            args: Arguments matching the tool's ``input_schema``.
            session_context: Optional context for audit/logging.

        Returns:
            The result dict from the tool handler.

        Raises:
            KeyError: If no tool with the given name is registered.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"MCP tool '{name}' is not registered")
        return tool.handler(args)


class _RegisteredTool:
    """Internal value object for a registered tool."""

    __slots__ = ("name", "description", "input_schema", "handler")

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable[[dict], dict],
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def invoke(self, args: dict) -> dict:
        return self.handler(args)


mcp_tool_registry = McpToolRegistry()
