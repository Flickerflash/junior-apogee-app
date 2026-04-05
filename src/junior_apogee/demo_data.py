"""Reusable demo builders for dashboard routes and smoke tests."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import AgentName, AgentRun, EvalLayer, TaskCase, TaskStatus


def make_run(
    agent: AgentName = AgentName.APOGEE,
    output: str = "Task completed successfully.",
    tool_calls: list[dict[str, Any]] | None = None,
    latency_ms: float = 500.0,
    input_tokens: int = 1000,
    output_tokens: int = 500,
    status: TaskStatus = TaskStatus.PASSED,
    task_id: str = "test-task-001",
) -> AgentRun:
    return AgentRun(
        agent=agent,
        task_id=task_id,
        raw_output=output,
        tool_calls=tool_calls or [],
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        status=status,
        finished_at=datetime.utcnow(),
    )


def make_task(
    family_id: str = "C-AP-01",
    name: str = "Test Task",
    description: str = "A test task case",
    layer: EvalLayer = EvalLayer.C_OUTCOMES,
    input_data: dict[str, Any] | None = None,
    expected_output: Any = None,
    success_criteria: dict[str, Any] | None = None,
) -> TaskCase:
    return TaskCase(
        family_id=family_id,
        name=name,
        description=description,
        input_data=input_data or {},
        expected_output=expected_output,
        success_criteria=success_criteria
        or {
            "layer": layer.value,
            "pass_threshold": 0.70,
            "outcome": {"completion_markers": ["completed", "result"]},
        },
    )
