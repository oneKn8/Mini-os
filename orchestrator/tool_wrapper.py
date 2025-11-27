"""
Universal Tool Calling Wrapper

Provides a unified interface for tool calling across any LLM,
with automatic fallback from native tool calling to structured output to text-based parsing.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from pydantic import BaseModel

from orchestrator.llm_capabilities import ModelCapabilityDetector

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    """Represents a single tool call."""

    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


class ToolCallResult(BaseModel):
    """Result of attempting to extract tool calls."""

    success: bool
    tool_calls: List[ToolCall]
    raw_response: Optional[str] = None
    error: Optional[str] = None
    method_used: str


class UniversalToolCaller:
    """
    Wraps tool calling to work with ANY LLM.

    Fallback chain:
    1. Native tool calling (OpenAI, Claude with tool binding)
    2. Structured output with tool schema
    3. Text-based tool calling with JSON parsing
    """

    def __init__(self, llm_client):
        """
        Initialize the universal tool caller.

        Args:
            llm_client: LLMClient instance
        """
        self.llm_client = llm_client
        self.capabilities = ModelCapabilityDetector.get_capabilities(llm_client._model_name)

    async def call_with_tools(
        self,
        messages: List[BaseMessage],
        tools: List[BaseTool],
        tool_choice: Optional[str] = None,
    ) -> ToolCallResult:
        """
        Call LLM with tools using best available method.

        Args:
            messages: Conversation messages
            tools: Available tools
            tool_choice: Optional tool selection strategy

        Returns:
            ToolCallResult with extracted tool calls
        """
        if not tools:
            return ToolCallResult(
                success=False,
                tool_calls=[],
                error="No tools provided",
                method_used="none",
            )

        if self.capabilities.supports_tool_calling:
            try:
                result = await self._native_tool_calling(messages, tools, tool_choice)
                if result.success:
                    return result
                logger.warning("Native tool calling failed, trying structured output")
            except Exception as e:
                logger.warning(f"Native tool calling error: {e}, falling back to structured output")

        if self.capabilities.supports_structured_output:
            try:
                result = await self._structured_output_calling(messages, tools)
                if result.success:
                    return result
                logger.warning("Structured output failed, trying text-based parsing")
            except Exception as e:
                logger.warning(f"Structured output error: {e}, falling back to text parsing")

        result = await self._text_based_calling(messages, tools)
        return result

    async def _native_tool_calling(
        self,
        messages: List[BaseMessage],
        tools: List[BaseTool],
        tool_choice: Optional[str] = None,
    ) -> ToolCallResult:
        """Native tool calling via LangChain's bind_tools."""
        try:
            bound_llm = self.llm_client.bind_tools(tools, tool_choice=tool_choice)
            response = await bound_llm.llm.ainvoke(messages)

            if not isinstance(response, AIMessage):
                return ToolCallResult(
                    success=False,
                    tool_calls=[],
                    error="Response is not an AIMessage",
                    method_used="native",
                )

            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            tool_name=tc.get("name", ""),
                            arguments=tc.get("args", {}),
                            call_id=tc.get("id"),
                        )
                    )

            return ToolCallResult(
                success=len(tool_calls) > 0,
                tool_calls=tool_calls,
                raw_response=response.content if hasattr(response, "content") else None,
                method_used="native",
            )

        except Exception as e:
            logger.error(f"Native tool calling failed: {e}")
            return ToolCallResult(
                success=False,
                tool_calls=[],
                error=str(e),
                method_used="native",
            )

    async def _structured_output_calling(self, messages: List[BaseMessage], tools: List[BaseTool]) -> ToolCallResult:
        """Structured output with tool schema."""
        try:
            tool_schemas = self._build_tool_schemas(tools)

            schema_prompt = SystemMessage(
                content=f"""You are a helpful assistant that can use tools.
Available tools: {json.dumps(tool_schemas, indent=2)}

To use a tool, respond with a JSON object in this format:
{{
  "tool_calls": [
    {{
      "tool_name": "tool_name_here",
      "arguments": {{
        "arg1": "value1",
        "arg2": "value2"
      }}
    }}
  ]
}}

If you don't need to use any tools, respond normally without the JSON structure.
"""
            )

            modified_messages = [schema_prompt] + list(messages)

            response = await self.llm_client.llm.ainvoke(modified_messages)
            content = response.content if hasattr(response, "content") else str(response)

            tool_calls = self._parse_json_tool_calls(content)

            return ToolCallResult(
                success=len(tool_calls) > 0,
                tool_calls=tool_calls,
                raw_response=content,
                method_used="structured",
            )

        except Exception as e:
            logger.error(f"Structured output calling failed: {e}")
            return ToolCallResult(
                success=False,
                tool_calls=[],
                error=str(e),
                method_used="structured",
            )

    async def _text_based_calling(self, messages: List[BaseMessage], tools: List[BaseTool]) -> ToolCallResult:
        """Text-based tool calling with explicit prompting and parsing."""
        try:
            tool_descriptions = self._build_tool_descriptions(tools)

            text_prompt = SystemMessage(
                content=f"""You are a helpful assistant that can use tools to help users.

Available tools:
{tool_descriptions}

To use a tool, write your response in this format:
TOOL_CALL: tool_name
ARGUMENTS:
{{
  "arg1": "value1",
  "arg2": "value2"
}}
END_TOOL_CALL

You can make multiple tool calls by repeating this format.
If you don't need any tools, just respond normally.
"""
            )

            modified_messages = [text_prompt] + list(messages)

            response = await self.llm_client.llm.ainvoke(modified_messages)
            content = response.content if hasattr(response, "content") else str(response)

            tool_calls = self._parse_text_tool_calls(content)

            return ToolCallResult(
                success=len(tool_calls) > 0,
                tool_calls=tool_calls,
                raw_response=content,
                method_used="text",
            )

        except Exception as e:
            logger.error(f"Text-based calling failed: {e}")
            return ToolCallResult(
                success=False,
                tool_calls=[],
                error=str(e),
                method_used="text",
            )

    def _build_tool_schemas(self, tools: List[BaseTool]) -> List[Dict[str, Any]]:
        """Build JSON schemas for tools."""
        schemas = []
        for tool in tools:
            schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {},
            }

            if hasattr(tool, "args_schema") and tool.args_schema:
                schema["parameters"] = tool.args_schema.model_json_schema()

            schemas.append(schema)

        return schemas

    def _build_tool_descriptions(self, tools: List[BaseTool]) -> str:
        """Build human-readable tool descriptions."""
        descriptions = []
        for tool in tools:
            desc = f"- {tool.name}: {tool.description}"

            if hasattr(tool, "args_schema") and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                if "properties" in schema:
                    args = ", ".join(schema["properties"].keys())
                    desc += f"\n  Arguments: {args}"

            descriptions.append(desc)

        return "\n".join(descriptions)

    def _parse_json_tool_calls(self, content: str) -> List[ToolCall]:
        """Parse tool calls from JSON response."""
        try:
            content_stripped = content.strip()

            if content_stripped.startswith("```json"):
                content_stripped = content_stripped[7:]
            if content_stripped.startswith("```"):
                content_stripped = content_stripped[3:]
            if content_stripped.endswith("```"):
                content_stripped = content_stripped[:-3]

            content_stripped = content_stripped.strip()

            parsed = json.loads(content_stripped)

            if isinstance(parsed, dict) and "tool_calls" in parsed:
                tool_calls = []
                for tc in parsed["tool_calls"]:
                    tool_calls.append(
                        ToolCall(
                            tool_name=tc.get("tool_name", ""),
                            arguments=tc.get("arguments", {}),
                        )
                    )
                return tool_calls

            return []

        except json.JSONDecodeError as e:
            logger.debug(f"Could not parse JSON tool calls: {e}")
            return []

    def _parse_text_tool_calls(self, content: str) -> List[ToolCall]:
        """Parse tool calls from text response with TOOL_CALL markers."""
        tool_calls = []

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("TOOL_CALL:"):
                tool_name = line.replace("TOOL_CALL:", "").strip()

                i += 1
                while i < len(lines) and not lines[i].strip().startswith("ARGUMENTS:"):
                    i += 1

                if i < len(lines):
                    i += 1
                    json_lines = []
                    while i < len(lines) and not lines[i].strip().startswith("END_TOOL_CALL"):
                        json_lines.append(lines[i])
                        i += 1

                    try:
                        args_json = "\n".join(json_lines).strip()
                        arguments = json.loads(args_json)

                        tool_calls.append(ToolCall(tool_name=tool_name, arguments=arguments))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Could not parse tool arguments: {e}")

            i += 1

        return tool_calls
