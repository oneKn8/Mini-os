"""
Dynamic Tool Registry for semantic tool discovery and selection.

Replaces hardcoded tool lists with intelligent tool discovery based on
capabilities and task requirements.
"""

import logging
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class ToolMetadata(BaseModel):
    """Metadata about a tool for discovery and selection."""

    name: str
    description: str
    capabilities: List[str]
    priority: int = 50
    dependencies: List[str] = []
    parallel_safe: bool = True


class ToolRegistry:
    """
    Registry for dynamic tool discovery and selection.

    Features:
    - Semantic tool search based on capabilities
    - Dependency resolution
    - Parallel execution grouping
    - Priority-based selection
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._metadata: Dict[str, ToolMetadata] = {}

    def register_tool(self, tool: BaseTool, metadata: ToolMetadata):
        """
        Register a tool with metadata.

        Args:
            tool: The tool to register
            metadata: Metadata for discovery
        """
        self._tools[metadata.name] = tool
        self._metadata[metadata.name] = metadata
        logger.info(f"Registered tool: {metadata.name} with capabilities: {metadata.capabilities}")

    def register_tools_from_list(self, tools: List[BaseTool]):
        """
        Register tools from a list, inferring metadata from tool properties.

        Args:
            tools: List of tools to register
        """
        for tool in tools:
            if tool.name in self._metadata:
                continue

            capabilities = self._infer_capabilities(tool)

            metadata = ToolMetadata(name=tool.name, description=tool.description or "", capabilities=capabilities)

            self.register_tool(tool, metadata)

    def _infer_capabilities(self, tool: BaseTool) -> List[str]:
        """Infer capabilities from tool name and description."""
        name_lower = tool.name.lower()
        desc_lower = (tool.description or "").lower()
        capabilities = []

        if any(x in name_lower or x in desc_lower for x in ["email", "mail", "inbox"]):
            capabilities.append("email")

        if any(x in name_lower or x in desc_lower for x in ["calendar", "event", "meeting"]):
            capabilities.append("calendar")

        if any(x in name_lower or x in desc_lower for x in ["weather", "forecast", "temperature"]):
            capabilities.append("weather")

        if any(x in name_lower or x in desc_lower for x in ["plan", "organize", "priority"]):
            capabilities.append("planning")

        if any(x in name_lower or x in desc_lower for x in ["knowledge", "query", "search", "rag"]):
            capabilities.append("knowledge")

        if any(x in name_lower or x in desc_lower for x in ["action", "execute", "perform"]):
            capabilities.append("actions")

        if not capabilities:
            capabilities.append("general")

        return capabilities

    def find_tools_for_capabilities(
        self, capabilities: List[str], suggested_tools: Optional[List[str]] = None
    ) -> List[BaseTool]:
        """
        Find tools matching required capabilities.

        Args:
            capabilities: Required capabilities
            suggested_tools: Optional list of suggested tool names

        Returns:
            List of matching tools
        """
        if not capabilities:
            return list(self._tools.values())

        matching_tools = []
        selected_names = set()

        if suggested_tools:
            for tool_name in suggested_tools:
                if tool_name in self._tools:
                    matching_tools.append(self._tools[tool_name])
                    selected_names.add(tool_name)

        for capability in capabilities:
            for tool_name, metadata in self._metadata.items():
                if tool_name in selected_names:
                    continue

                if capability in metadata.capabilities:
                    matching_tools.append(self._tools[tool_name])
                    selected_names.add(tool_name)

        if not matching_tools:
            logger.warning(f"No tools found for capabilities: {capabilities}, returning all tools")
            matching_tools = list(self._tools.values())[:10]

        logger.info(
            f"Selected {len(matching_tools)} tools for capabilities {capabilities}: {[t.name for t in matching_tools]}"
        )

        return matching_tools

    def get_tool_chain(self, tool_names: List[str]) -> List[List[str]]:
        """
        Determine optimal execution order with parallel groups.

        Args:
            tool_names: List of tool names to execute

        Returns:
            List of groups, where each group can run in parallel
        """
        self._build_dependency_graph(tool_names)

        groups = []
        remaining = set(tool_names)
        completed = set()

        max_iterations = len(tool_names) + 1
        iteration = 0

        while remaining and iteration < max_iterations:
            iteration += 1

            current_group = []
            for tool_name in list(remaining):
                metadata = self._metadata.get(tool_name)
                if not metadata:
                    current_group.append(tool_name)
                    continue

                deps_satisfied = all(dep in completed for dep in metadata.dependencies)

                if deps_satisfied:
                    current_group.append(tool_name)

            if not current_group:
                logger.warning(f"Circular dependency detected in tools: {remaining}")
                current_group = list(remaining)

            groups.append(current_group)

            for tool_name in current_group:
                remaining.discard(tool_name)
                completed.add(tool_name)

        return groups

    def _build_dependency_graph(self, tool_names: List[str]) -> Dict[str, Set[str]]:
        """Build dependency graph for tools."""
        graph = {}
        for tool_name in tool_names:
            metadata = self._metadata.get(tool_name)
            if metadata:
                graph[tool_name] = set(metadata.dependencies)
            else:
                graph[tool_name] = set()
        return graph

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        return self._tools.get(name)

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        return self._metadata.get(name)

    def list_capabilities(self) -> List[str]:
        """List all available capabilities."""
        capabilities = set()
        for metadata in self._metadata.values():
            capabilities.update(metadata.capabilities)
        return sorted(capabilities)

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __repr__(self) -> str:
        """String representation."""
        return f"ToolRegistry({len(self._tools)} tools, {len(self.list_capabilities())} capabilities)"
