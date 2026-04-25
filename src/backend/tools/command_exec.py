"""Command execution tool — reserved stub, currently disabled (TOOL-04).

Per D-23, D-24:
- Stub only, always returns disabled message
- No actual command execution
- The tool signature exists so the agent knows the capability exists
- Can be enabled via config flag in future phases
"""

from agents import RunContextWrapper, function_tool

from backend.agent.context import AgentContext


@function_tool
async def execute_command(
    ctx: RunContextWrapper[AgentContext],
    command: str,
) -> str:
    """执行系统命令。（功能暂未开放）

    Args:
        command: 要执行的命令
    """
    return "⚠️ 命令执行功能暂未开放，敬请期待后续版本。"
