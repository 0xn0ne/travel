"""Agent module — orchestrates tool-call cycle via AgentLoop."""

from backend.agent.loop import AgentLoop, MAX_ITERATIONS

__all__ = ["AgentLoop", "MAX_ITERATIONS"]
