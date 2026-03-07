"""
Flask Dashboard Backend – Junior Apogee
Real-time metrics API + server-sent events for live updates.
"""

from __future__ import annotations

import json
import time
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, Response, request
from flask_cors import CORS
from loguru import logger

from src.junior_apogee.models import (
    AgentName, AgentSummary, DashboardSnapshot, DriftAlert,
    EvalLayer, EvalResult, SeverityLevel, TaskResult, TaskStatus,
)
from src.junior_apogee.agents.profiles import AGENT_BASELINES
from src.junior_apogee.evaluation.engine import EvaluationEngine
from src.junior_apogee.governance.checker import GovernanceChecker
from src.junior_apogee.metrics.aggregator import MetricsAggregator
from src.junior_apogee.utils.helpers import setup_logger, utcnow_iso

# ─── App Init ────────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
setup_logger("INFO")

engine    = EvaluationEngine()
gov       = GovernanceChecker()
aggregator = MetricsAggregator()

# ─── Synthetic Demo Data ─────────────────────────────────────────────────────

def _jitter(base: float, spread: float = 0.03) -> float:
    """Add small noise to a metric for realistic-looking demo data."""
    v = base + random.uniform(-spread, spread)
    return max(0.0, min(1.0, v))


def generate_demo_summaries() -> List[AgentSummary]:
    baselines = AGENT_BASELINES
    summaries = []
    for agent, b in baselines.items():
        ts = _jitter(b.get("task_success") or 0.0)
        fa = _jitter(b.get("faithfulness") or 0.0)
        ta = _jitter(b.get("tool_accuracy") or 0.0)
        er = _jitter(b.get("ethics_rights") or 0.0)
        ar = b.get("archival")
        ar_v = _jitter(ar) if ar is not None else None

        total = 50
        passed = int(total * ts)
        summaries.append(AgentSummary(
            agent=agent,
            task_success_rate=ts,
            faithfulness=fa,
            tool_accuracy=ta,
            ethics_rights_pass=er,
            archival_quality=ar_v,
            overall_score=_jitter((ts + fa + ta + er) / 4),
            total_tasks=total,
            total_passed=passed,
            avg_latency_ms=random.uniform(400, 1800),
            avg_cost_usd=random.uniform(0.001, 0.010),
        ))
    return summaries


def generate_demo_drift_alerts(summaries: List[AgentSummary]) -> List[DriftAlert]:
    alerts = []
    for s in summaries:
        baseline = AGENT_BASELINES.get(s.agent, {})
        baseline_er = baseline.get("ethics_rights") or 1.0
        if s.ethics_rights_pass < baseline_er - 0.01:
            alerts.append(DriftAlert(
                agent=s.agent,
                metric_name="ethics_rights_pass",
                baseline_value=baseline_er,
                current_value=s.ethics_rights_pass,
                delta=s.ethics_rights_pass - baseline_er,
                threshold=0.01,
                severity=SeverityLevel.CRITICAL,
                message=f"{s.agent.value}: ethics/rights dropped below baseline",
            ))
    return alerts


def generate_demo_snapshot() -> DashboardSnapshot:
    summaries = generate_demo_summaries()
    alerts    = generate_demo_drift_alerts(summaries)
    return DashboardSnapshot(
        agent_summaries=summaries,
        drift_alerts=alerts,
        total_evals_run=random.randint(140, 175),
    )


def generate_demo_task_results() -> List[Dict[str, Any]]:
    families = [
        ("A-AP-01", "Multi-Step Research Planning", AgentName.APOGEE,   EvalLayer.A_REASONING),
        ("B-AP-01", "Web Search Tool Selection",    AgentName.APOGEE,   EvalLayer.B_ACTION),
        ("C-PR-02", "Prodigy Perfect Faithfulness", AgentName.PRODIGY,  EvalLayer.C_OUTCOMES),
        ("B-DJ-01", "DemiJoule Escalation",         AgentName.DEMIJOULE, EvalLayer.B_ACTION),
        ("GOV-OWASP-A01", "Prompt Injection",       AgentName.COLLEEN,  EvalLayer.B_ACTION),
        ("C-AP-06", "Archival Quality",             AgentName.APOGEE,   EvalLayer.C_OUTCOMES),
        ("B-CL-01", "OWASP Scan",                  AgentName.COLLEEN,  EvalLayer.B_ACTION),
        ("C-RC-01", "Workflow Completion",          AgentName.RECIPROCITY, EvalLayer.C_OUTCOMES),
    ]
    results = []
    for fid, name, agent, layer in families:
        score = random.uniform(0.75, 1.0)
        status = TaskStatus.PASSED if score >= 0.70 else TaskStatus.FAILED
        results.append({
            "family_id": fid,
            "name":      name,
            "agent":     agent.value,
            "layer":     layer.value,
            "score":     round(score, 3),
            "status":    status.value,
            "latency_ms": round(random.uniform(200, 2000), 0),
        })
    return results


def generate_history(n: int = 20) -> Dict[str, List]:
    """Synthetic time-series for the sparkline charts."""
    history = {a.value: [] for a in AgentName}
    for i in range(n):
        for agent in AgentName:
            base = (AGENT_BASELINES.get(agent, {}).get("task_success") or 0.90)
            history[agent.value].append(round(_jitter(base, 0.04), 3))
    return history


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/v1/snapshot")
def api_snapshot():
    snap = generate_demo_snapshot()
    return jsonify({
        "snapshot_id":   snap.snapshot_id,
        "taken_at":      snap.taken_at.isoformat() + "Z",
        "total_evals":   snap.total_evals_run,
        "platform_version": snap.platform_version,
        "agent_summaries": [
            {
                "agent":             s.agent.value,
                "task_success_rate": round(s.task_success_rate, 4),
                "faithfulness":      round(s.faithfulness, 4),
                "tool_accuracy":     round(s.tool_accuracy, 4),
                "ethics_rights_pass":round(s.ethics_rights_pass, 4),
                "archival_quality":  round(s.archival_quality, 4) if s.archival_quality else None,
                "overall_score":     round(s.overall_score, 4),
                "total_tasks":       s.total_tasks,
                "total_passed":      s.total_passed,
                "avg_latency_ms":    round(s.avg_latency_ms, 1),
                "avg_cost_usd":      round(s.avg_cost_usd, 5),
            }
            for s in snap.agent_summaries
        ],
        "drift_alerts": [
            {
                "agent":           a.agent.value,
                "metric_name":     a.metric_name,
                "baseline_value":  round(a.baseline_value, 4),
                "current_value":   round(a.current_value, 4),
                "delta":           round(a.delta, 4),
                "severity":        a.severity.value,
                "message":         a.message,
                "detected_at":     a.detected_at.isoformat() + "Z",
            }
            for a in snap.drift_alerts
        ],
    })


@app.route("/api/v1/task-results")
def api_task_results():
    return jsonify(generate_demo_task_results())


@app.route("/api/v1/history")
def api_history():
    return jsonify(generate_history())


@app.route("/api/v1/agents")
def api_agents():
    from src.junior_apogee.agents.profiles import ALL_AGENTS
    return jsonify([
        {
            "name":         a.name.value,
            "description":  a.description,
            "model_backend":a.model_backend,
            "temperature":  a.temperature,
            "tags":         a.tags,
            "capabilities": [{"name": c.name, "description": c.description} for c in a.capabilities],
        }
        for a in ALL_AGENTS.values()
    ])


@app.route("/api/v1/compliance")
def api_compliance():
    from tests.fixtures.conftest import make_run
    # Generate synthetic compliance report
    runs = [
        make_run(agent=AgentName.APOGEE,   output="Safe compliant response."),
        make_run(agent=AgentName.PRODIGY,  output="Research complete. Source: example.com"),
        make_run(agent=AgentName.COLLEEN,  output="OWASP scan complete. No violations."),
        make_run(agent=AgentName.DEMIJOULE, output="Monitoring drift. All within bounds."),
        make_run(agent=AgentName.RECIPROCITY, output="Workflow coordinated successfully."),
    ]
    report = gov.build_compliance_report(runs)
    return jsonify({
        "report_id":        report.report_id,
        "generated_at":     report.generated_at.isoformat() + "Z",
        "total_checks":     report.total_checks,
        "passed_checks":    report.passed_checks,
        "compliance_score": round(report.compliance_score, 4),
        "critical_count":   len(report.critical_flags),
        "agents_evaluated": [a.value for a in report.agents_evaluated],
        "flags": [
            {
                "flag_id":    f.flag_id,
                "category":   f.category.value,
                "owasp_id":   f.owasp_id,
                "severity":   f.severity.value,
                "description":f.description,
                "agent":      f.agent.value if f.agent else None,
                "mitigated":  f.mitigated,
            }
            for f in report.flags
        ],
    })


@app.route("/api/v1/evaluate", methods=["POST"])
def api_evaluate():
    """
    Ad-hoc evaluation endpoint.
    Accepts: { "agent": "Apogee", "output": "...", "task_name": "...", "tool_calls": [...] }
    """
    data = request.get_json(silent=True) or {}
    agent_name = data.get("agent", "Apogee")
    output     = data.get("output", "")
    tool_calls = data.get("tool_calls", [])

    try:
        agent = AgentName(agent_name)
    except ValueError:
        return jsonify({"error": f"Unknown agent: {agent_name}"}), 400

    from tests.fixtures.conftest import make_run, make_task
    run  = make_run(agent=agent, output=output, tool_calls=tool_calls)
    task = make_task(name=data.get("task_name", "Ad-hoc task"))

    result = engine.evaluate_run(task, run)
    flags, stats = gov.run_all_checks(run)

    return jsonify({
        "eval_id":       result.eval_id,
        "agent":         agent.value,
        "overall_score": round(result.overall_score, 4),
        "pass_rate":     round(result.pass_rate, 4),
        "task_status":   result.task_results[0].status.value if result.task_results else "unknown",
        "reasoning":     result.reasoning.model_dump() if result.reasoning else {},
        "action":        result.action.model_dump() if result.action else {},
        "outcome":       result.outcome.model_dump() if result.outcome else {},
        "governance": {
            "total_checks":  stats["total"],
            "passed_checks": stats["passed"],
            "failed_checks": stats["failed"],
            "flags":         len(flags),
        },
    })


# ─── Server-Sent Events (live updates) ───────────────────────────────────────

@app.route("/api/v1/stream")
def api_stream():
    def event_stream():
        while True:
            snap = generate_demo_snapshot()
            data = json.dumps({
                "timestamp":   utcnow_iso(),
                "total_evals": snap.total_evals_run,
                "summaries": [
                    {
                        "agent":        s.agent.value,
                        "overall_score":round(s.overall_score, 4),
                        "task_success": round(s.task_success_rate, 4),
                    }
                    for s in snap.agent_summaries
                ],
                "alerts": len(snap.drift_alerts),
            })
            yield f"data: {data}\n\n"
            time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "0.1.0-beta", "timestamp": utcnow_iso()})


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from src.junior_apogee.config import FLASK_HOST, FLASK_PORT, DEBUG
    logger.info(f"Starting Junior Apogee dashboard on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG)
