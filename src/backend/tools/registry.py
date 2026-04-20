"""Tool registry — loads tool definitions from config.yml and exposes them in OpenAI function-calling format."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Static tool registry loaded from config.yml at startup.

    Reads tool definitions (name, description, parameters in JSON Schema format)
    from a YAML config file, validates them, and converts to OpenAI
    function-calling format for use with ``LLMClient.tool_chat()``.

    Tool registration is static — definitions are loaded once at construction
    and do not change at runtime.  Dynamic loading is reserved for Skills
    (Phase 13).
    """

    def __init__(self, config_path: str = "config.yml") -> None:
        self._config_path = config_path
        self._definitions: list[dict] = self._load_definitions()
        self._name_map: dict[str, dict] = {d["name"]: d for d in self._definitions}
        logger.info("ToolRegistry loaded %d tool(s) from %s", len(self._definitions), config_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_openai_tools(self) -> list[dict]:
        """Return tool definitions in OpenAI function-calling format.

        Each entry is ``{"type": "function", "function": {...}}`` ready
        to pass directly as the ``tools`` parameter in a chat completion.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": d["name"],
                    "description": d["description"],
                    "parameters": d["parameters"],
                },
            }
            for d in self._definitions
        ]

    def get_tool_names(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._name_map.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered by name."""
        return name in self._name_map

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_definitions(self) -> list[dict]:
        """Read and parse YAML config, returning list of tool definition dicts."""
        path = Path(self._config_path)
        if not path.exists():
            logger.warning("Config file not found: %s — starting with empty tool list", self._config_path)
            return []

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "tools" not in data:
            logger.warning("No 'tools' key in %s — starting with empty tool list", self._config_path)
            return []

        definitions: list[dict] = data["tools"]
        for defn in definitions:
            self._validate_definition(defn)

        return definitions

    @staticmethod
    def _validate_definition(defn: dict) -> None:
        """Validate a single tool definition has required fields.

        Raises:
            ValueError: If the definition is missing required fields.
        """
        required_fields = ("name", "description", "parameters")
        missing = [f for f in required_fields if f not in defn]
        if missing:
            raise ValueError(f"Tool definition missing required fields: {missing}")

        params = defn["parameters"]
        if not isinstance(params, dict) or "type" not in params:
            raise ValueError(f"Tool '{defn.get('name', '?')}' parameters must be a JSON Schema dict with 'type' key")
