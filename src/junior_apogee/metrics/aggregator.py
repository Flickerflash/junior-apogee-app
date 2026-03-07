"""
Metrics aggregation – builds AgentSummary objects and detects drift.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from loguru import logger

from ..models import (
    AgentName,
    AgentSummary,
    DashboardSnapshot,
    DriftAlert,
    EvalResult,
    SeverityLevel,
    TaskStatus,
)
from ..agents.profiles import AGENT_BASELINES
from ..utils.helpers import clamp, pct, format_score, format_latency


# ─── Drift Thresholds ────────────────────────────────────────────────────────
DRIFT_THRESHOLDS: Dict[str, float] = {
    "task_success_rate":  0.05,  # 5% drop triggers WARNING
    "faithfulness":       0.03,  # 3% drop
    "tool_accuracy":      0.04,
    "ethics_rights_pass": 0.01,  # 1% drop is CRITICAL for ethics/rights
    "archival_quality":   0.05,
    "overall_score":      0.05,
}

CRITICAL_METRICS = {"ethics_rights_pass"}


class MetricsAggregator:
    """
    Converts raw EvalResult objects into AgentSummary + DriftAlert objects
    suitable for the dashboard.
    """

    def __init__(self, baseline: Optional[Dict[AgentName, Dict]] = None) -> None:
        self.baseline = baseline or AGENT_BASELINES
        self._history: Dict[AgentName, List[AgentSummary]] = {}

    # ─── Public API ──────────────────────────────────────────────────────────

    def summarise(self, result: EvalResult) -> AgentSummary:
        """Build an AgentSummary from a single EvalResult."""
        agent = result.agent
        tr = result.task_results

        total_tasks  = len(tr)
        total_passed = sum(1 for r in tr if r.passed)
        avg_latency  = (sum(r.latency_ms for r in tr) / total_tasks) if total_tasks else 0.0
        avg_cost     = (sum(r.token_cost_usd for r in tr) / total_tasks) if total_tasks else 0.0

        # Layer scores → agent summary fields
        faithfulness   = result.outcome.faithfulness  if result.outcome   else 0.0
        tool_accuracy  = result.action.tool_selection_accuracy if result.action else 0.0
        ethics_rights  = (
            (result.action.ethics_gate_pass + result.action.rights_gate_pass) / 2
            if result.action else 0.0
        )
        archival       = result.outcome.archival_quality if result.outcome else None

        summary = AgentSummary(
            agent=agent,
            task_success_rate=pct(total_passed, total_tasks),
            faithfulness=faithfulness,
            tool_accuracy=tool_accuracy,
            ethics_rights_pass=ethics_rights,
            archival_quality=archival,
            overall_score=result.overall_score,
            total_tasks=total_tasks,
            total_passed=total_passed,
            avg_latency_ms=avg_latency,
            avg_cost_usd=avg_cost,
        )

        # Store in history for drift detection
        self._history.setdefault(agent, []).append(summary)

        return summary

    def detect_drift(self, current: AgentSummary) -> List[DriftAlert]:
        """
        Compare current summary against baselines (or previous summaries)
        and return any DriftAlert objects.
        """
        alerts: List[DriftAlert] = []
        agent_baseline = self.baseline.get(current.agent, {})

        comparisons: List[Tuple[str, Optional[float], float]] = [
            ("task_success_rate",  agent_baseline.get("task_success"),  current.task_success_rate),
            ("faithfulness",       agent_baseline.get("faithfulness"),   current.faithfulness),
            ("tool_accuracy",      agent_baseline.get("tool_accuracy"),  current.tool_accuracy),
            ("ethics_rights_pass", agent_baseline.get("ethics_rights"),  current.ethics_rights_pass),
            ("archival_quality",   agent_baseline.get("archival"),       current.archival_quality or 0.0),
        ]

        for metric_name, baseline_val, current_val in comparisons:
            if baseline_val is None:
                continue
            delta     = current_val - baseline_val
            threshold = DRIFT_THRESHOLDS.get(metric_name, 0.05)

            if delta < -threshold:
                severity = SeverityLevel.CRITICAL if metric_name in CRITICAL_METRICS else SeverityLevel.WARNING
                alerts.append(DriftAlert(
                    agent=current.agent,
                    metric_name=metric_name,
                    baseline_value=baseline_val,
                    current_value=current_val,
                    delta=delta,
                    threshold=threshold,
                    severity=severity,
                    message=(
                        f"{current.agent.value} | {metric_name} dropped "
                        f"{abs(delta)*100:.1f}pp below baseline "
                        f"({format_score(current_val)} vs {format_score(baseline_val)})"
                    ),
                ))

        return alerts

    def build_snapshot(
        self,
        results: List[EvalResult],
        compliance_report=None,
        total_evals_run: int = 0,
    ) -> DashboardSnapshot:
        """Build a full dashboard snapshot from a list of eval results."""
        summaries: List[AgentSummary] = []
        all_alerts: List[DriftAlert] = []

        for result in results:
            summary = self.summarise(result)
            summaries.append(summary)
            drift_alerts = self.detect_drift(summary)
            all_alerts.extend(drift_alerts)
            for alert in drift_alerts:
                logger.warning(f"DRIFT ALERT: {alert.message}")

        return DashboardSnapshot(
            agent_summaries=summaries,
            drift_alerts=all_alerts,
            compliance_report=compliance_report,
            total_evals_run=total_evals_run or sum(
                s.total_tasks for s in summaries
            ),
        )

    def format_table(self, summaries: List[AgentSummary]) -> str:
        """Return a formatted ASCII table of agent summaries."""
        header = (
            f"{'Agent':<14} | {'Task Success':>12} | {'Faithfulness':>12} | "
            f"{'Tool Acc':>9} | {'Ethics/Rights':>13} | {'Archival':>9} | {'Overall':>8}"
        )
        sep = "-" * len(header)
        rows = [header, sep]
        for s in summaries:
            archival = format_score(s.archival_quality) if s.archival_quality is not None else "  N/A"
            rows.append(
                f"{s.agent.value:<14} | {format_score(s.task_success_rate):>12} | "
                f"{format_score(s.faithfulness):>12} | {format_score(s.tool_accuracy):>9} | "
                f"{format_score(s.ethics_rights_pass):>13} | {archival:>9} | "
                f"{format_score(s.overall_score):>8}"
            )
        return "\n".join(rows)
