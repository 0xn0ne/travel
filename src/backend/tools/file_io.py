"""File I/O tool — sandboxed read/write in data/agent_memory/ (TOOL-03).

Per D-19, D-20, D-21, D-22:
- Sandboxed to data/agent_memory/{user_id}/ directory
- Path traversal protection via resolve() + is_relative_to()
- UTF-8 text only
- Operations: list files, read file, write file
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from agents import RunContextWrapper, function_tool

from backend.agent.context import AgentContext

logger = logging.getLogger(__name__)

# Sandbox root — all file operations confined here
SANDBOX_ROOT = Path("data/agent_memory").resolve()


def _validate_path(user_id: str, filename: str) -> Path:
    """Resolve and validate path is within sandbox (D-20).

    Protects against:
    - Path traversal via ../ sequences
    - Symlinks pointing outside sandbox
    - Absolute paths

    Args:
        user_id: User identifier for subdirectory.
        filename: Relative filename within user's sandbox.

    Returns:
        Resolved absolute Path within sandbox.

    Raises:
        ValueError: If path escapes sandbox boundaries.
    """
    target = (SANDBOX_ROOT / user_id / filename).resolve()
    if not target.is_relative_to(SANDBOX_ROOT):
        raise ValueError(f"路径超出安全范围: {filename}")
    return target


def _ensure_sandbox(user_id: str) -> Path:
    """Create user sandbox directory if needed (D-19).

    Args:
        user_id: User identifier for subdirectory.

    Returns:
        Path to user's sandbox directory.
    """
    user_dir = SANDBOX_ROOT / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


@function_tool
async def list_files(
    ctx: RunContextWrapper[AgentContext],
) -> str:
    """列出用户存储目录中的所有文件。无需参数。"""
    user_id = ctx.context.user_id
    if not user_id:
        return "请先登录以使用文件功能"

    user_dir = SANDBOX_ROOT / user_id
    if not user_dir.exists():
        return "存储目录为空，暂无文件。"

    files = sorted(user_dir.iterdir())
    # Filter to files only (skip subdirectories)
    files = [f for f in files if f.is_file()]

    if not files:
        return "存储目录为空，暂无文件。"

    lines: list[str] = []
    for f in files:
        stat = f.stat()
        size_kb = stat.st_size / 1024
        mod_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        time_str = mod_time.strftime("%Y-%m-%d %H:%M")
        lines.append(f"- {f.name} ({size_kb:.1f}KB, {time_str})")

    header = f"共 {len(lines)} 个文件:"
    return header + "\n" + "\n".join(lines)


@function_tool
async def read_file(
    ctx: RunContextWrapper[AgentContext],
    filename: str,
) -> str:
    """读取用户存储目录中的文件内容。仅支持文本文件。

    Args:
        filename: 文件名，如"travel_notes.txt"
    """
    user_id = ctx.context.user_id
    if not user_id:
        return "请先登录以使用文件功能"

    try:
        target = _validate_path(user_id, filename)
    except ValueError as e:
        return str(e)

    if not target.exists():
        return f"文件不存在: {filename}"

    if not target.is_file():
        return f"不是文件: {filename}"

    try:
        content = target.read_text(encoding="utf-8")
        return content
    except UnicodeDecodeError:
        return f"文件编码错误，仅支持UTF-8文本文件: {filename}"
    except Exception as e:
        logger.warning("read_file failed: %s", e)
        return f"读取文件时出错: {type(e).__name__}"


@function_tool
async def write_file(
    ctx: RunContextWrapper[AgentContext],
    filename: str,
    content: str,
) -> str:
    """写入文件到用户存储目录。如果文件已存在则覆盖。仅支持文本文件。

    Args:
        filename: 文件名，如"travel_notes.txt"
        content: 要写入的文本内容
    """
    user_id = ctx.context.user_id
    if not user_id:
        return "请先登录以使用文件功能"

    try:
        target = _validate_path(user_id, filename)
    except ValueError as e:
        return str(e)

    # Ensure sandbox directory exists (D-19)
    _ensure_sandbox(user_id)

    try:
        target.write_text(content, encoding="utf-8")
        size_kb = len(content.encode("utf-8")) / 1024
        return f"文件已保存: {filename} ({size_kb:.1f}KB)"
    except Exception as e:
        logger.warning("write_file failed: %s", e)
        return f"写入文件时出错: {type(e).__name__}"
