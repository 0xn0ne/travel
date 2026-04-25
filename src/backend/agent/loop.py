"""Agent loop: send tools + messages to LLM, execute tool calls, return final text."""

import json
import logging
from typing import TYPE_CHECKING, Callable, Awaitable

from backend.llm.client import LLMClient
from backend.pipeline.events import EventBus, PipelineEvent
from backend.tools.registry import ToolRegistry
from backend.tools.result import ToolResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type for tool executor function: takes tool name + JSON args string, returns ToolResult
ToolExecutor = Callable[[str, str], Awaitable[ToolResult]]

MAX_ITERATIONS = 8  # Per D-17


class AgentLoop:
    """Orchestrates tool-call cycle for AI agent (per D-04, D-05).

    Generic/reusable — works for both pipeline Stage integration (Phase 14)
    and chat endpoint (Phase 15).
    """

    def __init__(
        self,
        llm: LLMClient,
        tool_registry: ToolRegistry,
        event_bus: EventBus | None = None,
        tool_executor: ToolExecutor | None = None,
        max_iterations: int = MAX_ITERATIONS,
    ):
        self.llm = llm
        self.registry = tool_registry
        self.event_bus = event_bus  # Optional per D-23
        self._tool_executor = tool_executor  # Custom executor override
        self.max_iterations = max_iterations

    async def run(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        tools: list[dict] | None = None,
    ) -> str:
        """Core loop: run messages through LLM with tools until final text response (per D-06).

        Args:
            messages: Conversation messages (role/content dicts)
            system_prompt: Optional system prompt to prepend
            tools: Tool schemas in OpenAI format. If None, uses registry's tools.

        Returns:
            Final text response from the LLM.
        """
        if tools is None:
            tools = self.registry.get_openai_tools()

        working_messages = list(messages)
        if system_prompt:
            working_messages = [{"role": "system", "content": system_prompt}] + working_messages

        for iteration in range(self.max_iterations):
            # Emit agent_thinking event (per D-19)
            await self._emit("agent_thinking", "thinking", "AI 正在思考...")

            # Non-streaming tool call decision (per D-07)
            result = await self.llm.tool_chat(
                messages=working_messages,
                tools=tools,
            )

            content = result.get("content")
            tool_calls = result.get("tool_calls")

            # If no tool calls, LLM gave final text response
            if not tool_calls:
                if content:
                    return content
                else:
                    return "抱歉，我无法生成回答。"

            # Process tool calls
            # Append assistant message with tool_calls to working messages
            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            working_messages.append(assistant_msg)

            # Execute each tool call
            for tc in tool_calls:
                fn = tc["function"]
                tool_name = fn["name"]
                tool_args_str = fn["arguments"]
                tool_call_id = tc["id"]

                # Emit tool_executing event (per D-19, D-20)
                await self._emit(
                    "tool_executing",
                    "executing",
                    f"正在执行：{tool_name}...",
                    data={"tool": tool_name},
                )

                # Execute tool (per D-15)
                tool_result = await self._execute_tool(tool_name, tool_args_str)

                # Emit tool_completed event (per D-19)
                await self._emit(
                    "tool_completed",
                    "completed",
                    tool_result.summary,
                    data={"tool": tool_name, "success": tool_result.success},
                )

                # Append tool result as message (per D-15 — errors are fed back as context)
                result_content = json.dumps(tool_result.to_dict(), ensure_ascii=False)
                working_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result_content,
                })

        # Max iterations reached (per D-17)
        logger.warning(f"Agent reached max iterations ({self.max_iterations})")
        await self._emit("agent_thinking", "max_iterations", "已达到最大工具调用次数，正在生成最终回答...")

        # Force one final call with no tools
        working_messages.append({
            "role": "system",
            "content": "已达到最大工具调用次数，请基于已有信息生成最终回答。",
        })

        # Use stream_chat for final text response (per D-08)
        # Collect the full response from stream
        chunks = []
        async for chunk in self.llm.stream_chat(
            messages=working_messages,
            temperature=0.7,
            max_tokens=4096,
        ):
            chunks.append(chunk)

        return "".join(chunks) if chunks else "抱歉，我暂时无法完成这个请求。"

    async def run_streaming(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        tools: list[dict] | None = None,
    ):
        """Streaming variant: tool calls are non-streaming, but final text streams token-by-token (per D-08).

        Yields: str chunks of the final text response.
        """
        if tools is None:
            tools = self.registry.get_openai_tools()

        working_messages = list(messages)
        if system_prompt:
            working_messages = [{"role": "system", "content": system_prompt}] + working_messages

        for iteration in range(self.max_iterations):
            await self._emit("agent_thinking", "thinking", "AI 正在思考...")

            result = await self.llm.tool_chat(
                messages=working_messages,
                tools=tools,
            )

            content = result.get("content")
            tool_calls = result.get("tool_calls")

            if not tool_calls:
                # Stream the final text response token by token (per D-08)
                if content:
                    yield content
                return

            assistant_msg = {"role": "assistant", "content": content, "tool_calls": tool_calls}
            working_messages.append(assistant_msg)

            for tc in tool_calls:
                fn = tc["function"]
                tool_name = fn["name"]
                tool_args_str = fn["arguments"]
                tool_call_id = tc["id"]

                await self._emit(
                    "tool_executing", "executing",
                    f"正在执行：{tool_name}...",
                    data={"tool": tool_name},
                )

                tool_result = await self._execute_tool(tool_name, tool_args_str)

                await self._emit(
                    "tool_completed", "completed",
                    tool_result.summary,
                    data={"tool": tool_name, "success": tool_result.success},
                )

                result_content = json.dumps(tool_result.to_dict(), ensure_ascii=False)
                working_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result_content,
                })

        # Max iterations — force final streaming response
        working_messages.append({
            "role": "system",
            "content": "已达到最大工具调用次数，请基于已有信息生成最终回答。",
        })
        async for chunk in self.llm.stream_chat(
            messages=working_messages,
            temperature=0.7,
            max_tokens=4096,
        ):
            yield chunk

    async def _execute_tool(self, name: str, arguments_json: str) -> ToolResult:
        """Execute a single tool call. Returns ToolResult with error context on failure (per D-15, D-16)."""
        try:
            if self._tool_executor:
                return await self._tool_executor(name, arguments_json)
            # Phase 11: no real tools yet — return a placeholder
            # Real tool implementations come in Phase 12
            return ToolResult(
                data=None,
                error=f"工具 '{name}' 尚未实现（Phase 12 将添加具体工具）",
                summary=f"工具 {name} 暂未实现",
            )
        except Exception as e:
            logger.error(f"Tool '{name}' execution failed: {e}")
            # Per D-15: error is caught and returned as error context to LLM
            return ToolResult(
                data=None,
                error=f"工具执行失败: {str(e)}",
                summary=f"工具 {name} 执行失败",
            )

    async def _emit(self, event_type: str, status: str, message: str, data: dict | None = None):
        """Emit SSE event via EventBus if available (per D-19, D-21)."""
        if self.event_bus:
            await self.event_bus.emit(PipelineEvent(
                stage="agent",  # Per D-21
                status=status,
                event_type=event_type,  # Per D-19
                message=message,  # Per D-20: human-readable Chinese only
                data=data,
            ))
