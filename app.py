"""Flask dashboard backend for Junior Apogee."""

from __future__ import annotations

import json
import random
import time
from typing import Any

from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS
from loguru import logger

from src.junior_apogee.agents.profiles import AGENT_BASELINES
from src.junior_apogee.config import DEBUG, FLASK_HOST, FLASK_PORT
from src.junior_apogee.demo_data import make_run, make_task
from src.junior_apogee.evaluation.engine import EvaluationEngine
from src.junior_apogee.governance.checker import GovernanceChecker
from src.junior_apogee.metrics.aggregator import MetricsAggregator
from src.junior_apogee.models import (
    AgentName,
    AgentSummary,
    DashboardSnapshot,
    DriftAlert,
    EvalLayer,
    SeverityLevel,
    TaskStatus,
)
from src.junior_apogee.utils.helpers import setup_logger, utcnow_iso

APP_VERSION = "0.1.0b0"

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
setup_logger("INFO")

engine = EvaluationEngine()
gov = GovernanceChecker()
aggregator = MetricsAggregator()


def _jitter(base: float, spread: float = 0.03) -> float:
    """Add small noise to a metric for realistic-looking demo data."""
    value = base + random.uniform(-spread, spread)
    return max(0.0, min(1.0, value))


def generate_demo_summaries() -> list[AgentSummary]:
    summaries: list[AgentSummary] = []
    for agent, baseline in AGENT_BASELINES.items():
        task_success = _jitter(baseline.get("task_success") or 0.0)
        faithfulness = _jitter(baseline.get("faithfulness") or 0.0)
        tool_accuracy = _jitter(baseline.get("tool_accuracy") or 0.0)
        ethics_rights = _jitter(baseline.get("ethics_rights") or 0.0)
        archival = baseline.get("archival")
        archival_quality = _jitter(archival) if archival is not None else None

        total_tasks = 50
        total_passed = int(total_tasks * task_success)
        summaries.append(
            AgentSummary(
                agent=agent,
                task_success_rate=task_success,
                faithfulness=faithfulness,
                tool_accuracy=tool_accuracy,
                ethics_rights_pass=ethics_rights,
                archival_quality=archival_quality,
                overall_score=_jitter(
                    (task_success + faithfulness + tool_accuracy + ethics_rights)
                    / 4
                ),
                total_tasks=total_tasks,
                total_passed=total_passed,
                avg_latency_ms=random.uniform(400, 1800),
                avg_cost_usd=random.uniform(0.001, 0.010),
            )
        )
    return summaries


def generate_demo_drift_alerts(
    summaries: list[AgentSummary],
) -> list[DriftAlert]:
    alerts: list[DriftAlert] = []
    for summary in summaries:
        baseline = AGENT_BASELINES.get(summary.agent, {})
        baseline_ethics = baseline.get("ethics_rights") or 1.0
        if summary.ethics_rights_pass < baseline_ethics - 0.01:
            alerts.append(
                DriftAlert(
                    agent=summary.agent,
                    metric_name="ethics_rights_pass",
                    baseline_value=baseline_ethics,
                    current_value=summary.ethics_rights_pass,
                    delta=summary.ethics_rights_pass - baseline_ethics,
                    threshold=0.01,
                    severity=SeverityLevel.CRITICAL,
                    message=(
                        f"{summary.agent.value}: ethics/rights dropped below baseline"
                    ),
                )
            )
    return alerts


def generate_demo_snapshot() -> DashboardSnapshot:
    summaries = generate_demo_summaries()
    alerts = generate_demo_drift_alerts(summaries)
    return DashboardSnapshot(
        agent_summaries=summaries,
        drift_alerts=alerts,
        total_evals_run=random.randint(140, 175),
        platform_version=APP_VERSION,
    )


def generate_demo_task_results() -> list[dict[str, Any]]:
    families = [
        (
            "A-AP-01",
            "Multi-Step Research Planning",
            AgentName.APOGEE,
            EvalLayer.A_REASONING,
        ),
        (
            "B-AP-01",
            "Web Search Tool Selection",
            AgentName.APOGEE,
            EvalLayer.B_ACTION,
        ),
        (
            "C-PR-02",
            "Prodigy Perfect Faithfulness",
            AgentName.PRODIGY,
            EvalLayer.C_OUTCOMES,
        ),
        (
            "B-DJ-01",
            "DemiJoule Escalation",
            AgentName.DEMIJOULE,
            EvalLayer.B_ACTION,
        ),
        (
            "GOV-OWASP-A01",
            "Prompt Injection",
            AgentName.COLLEEN,
            EvalLayer.B_ACTION,
        ),
        (
            "C-AP-06",
            "Archival Quality",
            AgentName.APOGEE,
            EvalLayer.C_OUTCOMES,
        ),
        (
            "B-CL-01",
            "OWASP Scan",
            AgentName.COLLEEN,
            EvalLayer.B_ACTION,
        ),
        (
            "C-RC-01",
            "Workflow Completion",
            AgentName.RECIPROCITY,
            EvalLayer.C_OUTCOMES,
        ),
    ]
    results: list[dict[str, Any]] = []
    for family_id, name, agent, layer in families:
        score = random.uniform(0.75, 1.0)
        status = TaskStatus.PASSED if score >= 0.70 else TaskStatus.FAILED
        results.append(
            {
                "family_id": family_id,
                "name": name,
                "agent": agent.value,
                "layer": layer.value,
                "score": round(score, 3),
                "status": status.value,
                "latency_ms": round(random.uniform(200, 2000), 0),
            }
        )
    return results


def generate_history(points: int = 20) -> dict[str, list[float]]:
    """Synthetic time-series for the sparkline charts."""
    history = {agent.value: [] for agent in AgentName}
    for _ in range(points):
        for agent in AgentName:
            base = AGENT_BASELINES.get(agent, {}).get("task_success") or 0.90
            history[agent.value].append(round(_jitter(base, 0.04), 3))
    return history


@app.route("/")
def index() -> str:
    return render_template("dashboard.html")


@app.route("/api/v1/snapshot")
def api_snapshot() -> Response:
    snapshot = generate_demo_snapshot()
    return jsonify(
        {
            "snapshot_id": snapshot.snapshot_id,
            "taken_at": snapshot.taken_at.isoformat() + "Z",
            "total_evals": snapshot.total_evals_run,
            "platform_version": snapshot.platform_version,
            "agent_summaries": [
                {
                    "agent": summary.agent.value,
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
                    "total_tasks": summary.total_tasks,
                    "total_passed": summary.total_passed,
                    "avg_latency_ms": round(summary.avg_latency_ms, 1),
                    "avg_cost_usd": round(summary.avg_cost_usd, 5),
                }
                for summary in snapshot.agent_summaries
            ],
            "drift_alerts": [
                {
                    "agent": alert.agent.value,
                    "metric_name": alert.metric_name,
                    "baseline_value": round(alert.baseline_value, 4),
                    "current_value": round(alert.current_value, 4),
                    "delta": round(alert.delta, 4),
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "detected_at": alert.detected_at.isoformat() + "Z",
                }
                for alert in snapshot.drift_alerts
            ],
        }
    )


@app.route("/api/v1/task-results")
def api_task_results() -> Response:
    return jsonify(generate_demo_task_results())


@app.route("/api/v1/history")
def api_history() -> Response:
    return jsonify(generate_history())


@app.route("/api/v1/agents")
def api_agents() -> Response:
    from src.junior_apogee.agents.profiles import ALL_AGENTS

    return jsonify(
        [
            {
                "name": agent.name.value,
                "description": agent.description,
                "model_backend": agent.model_backend,
                "temperature": agent.temperature,
                "tags": agent.tags,
                "capabilities": [
                    {"name": capability.name, "description": capability.description}
                    for capability in agent.capabilities
                ],
            }
            for agent in ALL_AGENTS.values()
        ]
    )


@app.route("/api/v1/compliance")
def api_compliance() -> Response:
    runs = [
        make_run(agent=AgentName.APOGEE, output="Safe compliant response."),
        make_run(
            agent=AgentName.PRODIGY,
            output="Research complete. Source: example.com",
        ),
        make_run(
            agent=AgentName.COLLEEN,
            output="OWASP scan complete. No violations.",
        ),
        make_run(
            agent=AgentName.DEMIJOULE,
            output="Monitoring drift. All within bounds.",
        ),
        make_run(
            agent=AgentName.RECIPROCITY,
            output="Workflow coordinated successfully.",
        ),
    ]
    report = gov.build_compliance_report(runs)
    return jsonify(
        {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat() + "Z",
            "total_checks": report.total_checks,
            "passed_checks": report.passed_checks,
            "compliance_score": round(report.compliance_score, 4),
            "critical_count": len(report.critical_flags),
            "agents_evaluated": [agent.value for agent in report.agents_evaluated],
            "flags": [
                {
                    "flag_id": flag.flag_id,
                    "category": flag.category.value,
                    "owasp_id": flag.owasp_id,
                    "severity": flag.severity.value,
                    "description": flag.description,
                    "agent": flag.agent.value if flag.agent else None,
                    "mitigated": flag.mitigated,
                }
                for flag in report.flags
            ],
        }
    )


@app.route("/api/v1/evaluate", methods=["POST"])
def api_evaluate() -> tuple[Response, int] | Response:
    data = request.get_json(silent=True) or {}
    agent_name = data.get("agent", "Apogee")
    output = data.get("output", "")
    tool_calls = data.get("tool_calls", [])

    try:
        agent = AgentName(agent_name)
    except ValueError:
        return jsonify({"error": f"Unknown agent: {agent_name}"}), 400

    run = make_run(agent=agent, output=output, tool_calls=tool_calls)
    task = make_task(name=data.get("task_name", "Ad-hoc task"))

    result = engine.evaluate_run(task, run)
    flags, stats = gov.run_all_checks(run)

    task_status = (
        result.task_results[0].status.value if result.task_results else "unknown"
    )

    return jsonify(
        {
            "eval_id": result.eval_id,
            "agent": agent.value,
            "overall_score": round(result.overall_score, 4),
            "pass_rate": round(result.pass_rate, 4),
            "task_status": task_status,
            "reasoning": result.reasoning.model_dump() if result.reasoning else {},
            "action": result.action.model_dump() if result.action else {},
            "outcome": result.outcome.model_dump() if result.outcome else {},
            "governance": {
                "total_checks": stats["total"],
                "passed_checks": stats["passed"],
                "failed_checks": stats["failed"],
                "flags": len(flags),
            },
        }
    )


@app.route("/api/v1/stream")
def api_stream() -> Response:
    def event_stream() -> Any:
        while True:
            snapshot = generate_demo_snapshot()
            payload = json.dumps(
                {
                    "timestamp": utcnow_iso(),
                    "total_evals": snapshot.total_evals_run,
                    "summaries": [
                        {
                            "agent": summary.agent.value,
                            "overall_score": round(summary.overall_score, 4),
                            "task_success": round(summary.task_success_rate, 4),
                        }
                        for summary in snapshot.agent_summaries
                    ],
                    "alerts": len(snapshot.drift_alerts),
                }
            )
            yield f"data: {payload}\n\n"
            time.sleep(5)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/health")
def health() -> Response:
    return jsonify(
        {"status": "ok", "version": APP_VERSION, "timestamp": utcnow_iso()}
    )


def main() -> None:
    logger.info(
        f"Starting Junior Apogee dashboard on {FLASK_HOST}:{FLASK_PORT}"
    )
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
