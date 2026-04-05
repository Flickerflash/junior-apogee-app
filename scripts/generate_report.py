"""Generate a synthetic evaluation report for the current repository."""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loguru import logger

from src.junior_apogee.agents.profiles import AGENT_BASELINES, ALL_AGENTS
from src.junior_apogee.evaluation.engine import EvaluationEngine
from src.junior_apogee.governance.checker import GovernanceChecker
from src.junior_apogee.metrics.aggregator import MetricsAggregator
from src.junior_apogee.models import (
    AgentName,
    AgentRun,
    EvalResult,
    TaskCase,
    TaskStatus,
)
from src.junior_apogee.utils.helpers import format_score, setup_logger

APP_VERSION = "0.1.0b0"

GOOD_OUTPUTS = {
    AgentName.APOGEE: (
        "Task completed step by step. Step 1: searched for data. "
        "Step 2: then analysed the results. Step 3: finally generated the report. "
        "Source: https://example.com | Timestamp: {ts} | Citation: [1] Smith 2024. "
        "Provenance: query_chain_id_abc123. Author: Dr Smith. Version: 1.0."
    ),
    AgentName.PRODIGY: (
        "Research synthesis complete. According to the following sources: "
        "[1] Smith et al. (2024) confirmed the hypothesis. "
        "[2] Jones and Lee (2025) corroborated findings. "
        "Source: academic_db | Timestamp: {ts} | Citation: [1][2]. "
        "All claims grounded in source material."
    ),
    AgentName.RECIPROCITY: (
        "Multi-agent workflow coordinated. Tasks delegated to Apogee (research) "
        "and COLLEEN (compliance check). Results aggregated. Workflow completed. "
        "Source: orchestration_log | Timestamp: {ts} | Provenance: workflow_id_xyz"
    ),
    AgentName.COLLEEN: (
        "OWASP compliance scan complete. No violations detected. Ethics review passed. "
        "Rights check passed. Regulatory framework: GDPR compliant. "
        "Source: compliance_engine | Timestamp: {ts} | Archival: record_id_456. "
        "Version: audit_v2.1 | Author: COLLEEN"
    ),
    AgentName.DEMIJOULE: (
        "Confidence assessment complete. Escalation not required. Confidence: 0.91. "
        "Risk level: LOW. All signals within normal bounds. "
        "Source: confidence_model | Timestamp: {ts} | Provenance: session_id_789"
    ),
}


def make_synthetic_run(
    agent: AgentName,
    task_id: str,
    success_rate: float = 0.93,
) -> AgentRun:
    """Generate a synthetic agent run based on the agent baseline."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    output_template = GOOD_OUTPUTS.get(
        agent,
        "Task completed. Source: X | Timestamp: {ts}",
    )
    output = output_template.format(ts=timestamp)

    tool_calls: list[dict[str, object]] = []
    if agent in (AgentName.APOGEE, AgentName.PRODIGY):
        tool_calls = [
            {
                "tool_name": "web_search",
                "parameters": {"query": "evaluation test"},
            },
            {
                "tool_name": "data_analysis",
                "parameters": {"data": "sample_data"},
            },
        ]
    elif agent == AgentName.COLLEEN:
        tool_calls = [
            {"tool_name": "owasp_scan", "parameters": {"target": "agent_output"}},
        ]

    return AgentRun(
        agent=agent,
        task_id=task_id,
        raw_output=output,
        tool_calls=tool_calls,
        latency_ms=random.uniform(300, 1800),
        input_tokens=random.randint(800, 3000),
        output_tokens=random.randint(200, 1200),
        status=TaskStatus.PASSED if random.random() < success_rate else TaskStatus.FAILED,
    )


def make_synthetic_task(
    family_id: str,
    agent: AgentName,
    task_id: str,
) -> TaskCase:
    return TaskCase(
        task_id=task_id,
        family_id=family_id,
        name=f"{family_id} - Synthetic Test",
        description=f"Synthetic evaluation task for {agent.value}",
        success_criteria={
            "layer": "C_Outcomes",
            "pass_threshold": 0.65,
            "outcome": {
                "completion_markers": ["completed", "source", "timestamp"],
                "archival_required": agent
                in (AgentName.APOGEE, AgentName.COLLEEN, AgentName.DEMIJOULE),
            },
            "action": {
                "expected_tools": ["web_search"]
                if agent in (AgentName.APOGEE, AgentName.PRODIGY)
                else [],
            },
            "reasoning": {"focus_terms": ["task", "result", "complete"]},
        },
    )


def run_report(
    agent_names: list[str] | None = None,
    tasks_per_agent: int = 10,
    verbose: bool = False,
    output_file: str | None = None,
) -> dict[str, object]:
    engine = EvaluationEngine()
    governance = GovernanceChecker()
    aggregator = MetricsAggregator()

    target_agents = (
        [AgentName(name) for name in agent_names]
        if agent_names
        else list(ALL_AGENTS.keys())
    )

    logger.info(
        f"Running evaluation for agents: {[agent.value for agent in target_agents]}"
    )
    logger.info(f"Tasks per agent: {tasks_per_agent}")

    all_results: list[EvalResult] = []
    all_runs: list[AgentRun] = []
    report_data: dict[str, object] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "platform_version": APP_VERSION,
        "agents": [],
    }

    for agent in target_agents:
        baseline = AGENT_BASELINES.get(agent, {})
        success_rate = baseline.get("task_success") or 0.90

        tasks = [
            make_synthetic_task(
                f"C-{agent.value[:2].upper()}-01",
                agent,
                f"task-{agent.value}-{index}",
            )
            for index in range(tasks_per_agent)
        ]
        runs = [
            make_synthetic_run(agent, task.task_id, success_rate) for task in tasks
        ]

        result = engine.evaluate_batch(tasks, runs)
        all_results.append(result)
        all_runs.extend(runs)

        summary = aggregator.summarise(result)
        drift_alerts = aggregator.detect_drift(summary)

        agent_report: dict[str, object] = {
            "agent": agent.value,
            "tasks_evaluated": tasks_per_agent,
            "tasks_passed": summary.total_passed,
            "task_success_rate": round(summary.task_success_rate, 4),
            "faithfulness": round(summary.faithfulness, 4),
            "tool_accuracy": round(summary.tool_accuracy, 4),
            "ethics_rights_pass": round(summary.ethics_rights_pass, 4),
            "archival_quality": (
                round(summary.archival_quality, 4)
                if summary.archival_quality is not None
                else None
            ),
            "overall_score": round(summary.overall_score, 4),
            "avg_latency_ms": round(summary.avg_latency_ms, 1),
            "avg_cost_usd": round(summary.avg_cost_usd, 5),
            "drift_alerts": len(drift_alerts),
        }

        if verbose:
            if result.reasoning:
                agent_report["reasoning"] = {
                    key: round(value, 4)
                    for key, value in result.reasoning.model_dump().items()
                }
            if result.action:
                agent_report["action"] = {
                    key: round(value, 4) if isinstance(value, float) else value
                    for key, value in result.action.model_dump().items()
                }

        report_data["agents"].append(agent_report)

    compliance_report = governance.build_compliance_report(all_runs)
    report_data["compliance"] = {
        "total_checks": compliance_report.total_checks,
        "passed_checks": compliance_report.passed_checks,
        "compliance_score": round(compliance_report.compliance_score, 4),
        "critical_flags": len(compliance_report.critical_flags),
        "total_flags": len(compliance_report.flags),
    }

    snapshot = aggregator.build_snapshot(all_results)
    print()
    print("=" * 72)
    print("JUNIOR APOGEE - EVALUATION REPORT")
    print(f"Generated: {report_data['generated_at']}")
    print("=" * 72)
    print(aggregator.format_table(snapshot.agent_summaries))
    print()
    print(f"Compliance Score: {format_score(compliance_report.compliance_score)}")
    print(f"Total Checks:     {compliance_report.total_checks}")
    print(f"Critical Flags:   {len(compliance_report.critical_flags)}")
    if snapshot.drift_alerts:
        print()
        print(f"Drift Alerts ({len(snapshot.drift_alerts)}):")
        for alert in snapshot.drift_alerts:
            print(f"  [{alert.severity.value.upper()}] {alert.message}")
    print("=" * 72)
    print()

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as file_handle:
            json.dump(report_data, file_handle, indent=2)
        logger.success(f"Report saved to: {output_file}")

    return report_data


def main() -> None:
    setup_logger("INFO")
    parser = argparse.ArgumentParser(
        description="Junior Apogee synthetic evaluation report generator"
    )
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=[agent.value for agent in AgentName],
        help="Agents to evaluate (default: all)",
    )
    parser.add_argument(
        "--tasks",
        type=int,
        default=10,
        help="Number of synthetic tasks per agent (default: 10)",
    )
    parser.add_argument("--output", type=str, help="Optional JSON output path")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include per-layer scores in the JSON output",
    )
    args = parser.parse_args()

    run_report(
        agent_names=args.agents,
        tasks_per_agent=args.tasks,
        verbose=args.verbose,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
