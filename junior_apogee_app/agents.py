from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type


class Agent(ABC):
    """Base class for all agents participating in the evaluation."""

    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task and return result."""


_agent_registry: list[Type[Agent]] = []


def register_agent(cls: Type[Agent]) -> Type[Agent]:
    """Register an Agent implementation class."""
    _agent_registry.append(cls)
    return cls


def list_agents() -> list[str]:
    """Return the names of all registered agent types."""
    return [cls.__name__ for cls in _agent_registry]


from . import agents_example  # noqa: E402,F401
