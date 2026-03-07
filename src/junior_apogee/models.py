"""
Core Pydantic models for the Junior Apogee evaluation platform.
Covers agents, tasks, evaluation results, metrics, and governance.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import uuid


# ─────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────

class AgentName(str, Enum):
    APOGEE      = "Apogee"
    PRODIGY     = "Prodigy"
    RECIPROCITY = "Reciprocity"
    COLLEEN     = "COLLEEN"
    DEMIJOULE   = "DemiJoule"


class EvalLayer(str, Enum):
    A_REASONING = "A_Reasoning"
    B_ACTION    = "B_Action"
    C_OUTCOMES  = "C_Outcomes"


class TaskStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    PASSED    = "passed"
    FAILED    = "failed"
    SKIPPED   = "skipped"
    ERROR     = "error"


class SeverityLevel(str, Enum):
    INFO     = "info"
    WARNING  = "warning"
    CRITICAL = "critical"


class GovernanceCategory(str, Enum):
    OWASP_AGENTIC = "owasp_agentic"
    ETHICS        = "ethics"
    RIGHTS        = "rights"
    HALLUCINATION = "hallucination"
    ARCHIVAL      = "archival"


# ─────────────────────────────────────────────
#  Agent Models
# ─────────────────────────────────────────────

class AgentCapability(BaseModel):
    name: str
    description: str
    enabled: bool = True
    version: str = "1.0.0"


class AgentConfig(BaseModel):
    name: AgentName
    description: str
    capabilities: List[AgentCapability] = Field(default_factory=list)
    model_backend: str = "claude-3-5-sonnet"
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout_seconds: int = 120
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class AgentRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentName
    task_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    raw_output: str = ""
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        """Rough estimate at $3/$15 per 1M tokens (input/output)."""
        return (self.input_tokens * 3 + self.output_tokens * 15) / 1_000_000


# ─────────────────────────────────────────────
#  Task Models
# ─────────────────────────────────────────────

class TaskFamily(BaseModel):
    family_id: str
    name: str
    description: str
    layer: EvalLayer
    agent: AgentName
    weight: float = 1.0
    tags: List[str] = Field(default_factory=list)
    success_bar: float = 0.85  # minimum pass rate


class TaskCase(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    family_id: str
    name: str
    description: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    expected_output: Optional[Any] = None
    success_criteria: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    priority: int = 1  # 1=high, 2=medium, 3=low
    timeout_seconds: int = 60
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    family_id: str
    agent: AgentName
    layer: EvalLayer
    status: TaskStatus
    score: float = 0.0          # 0.0 – 1.0
    deterministic_pass: Optional[bool] = None
    llm_judge_score: Optional[float] = None
    latency_ms: float = 0.0
    token_cost_usd: float = 0.0
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def passed(self) -> bool:
        return self.status == TaskStatus.PASSED


# ─────────────────────────────────────────────
#  Layer A – Reasoning / Planning
# ─────────────────────────────────────────────

class ReasoningScore(BaseModel):
    plan_quality: float = 0.0         # 0-1
    plan_adherence: float = 0.0       # 0-1
    plan_convergence: float = 0.0     # 0-1
    chronology_adherence: float = 0.0 # 0-1
    harmonic_drift: float = 0.0       # lower = better (0-1)

    @property
    def composite(self) -> float:
        return (
            self.plan_quality * 0.25
            + self.plan_adherence * 0.25
            + self.plan_convergence * 0.20
            + self.chronology_adherence * 0.20
            + (1.0 - self.harmonic_drift) * 0.10
        )


# ─────────────────────────────────────────────
#  Layer B – Action / Tool-Use
# ─────────────────────────────────────────────

class ToolCallRecord(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_tool: Optional[str] = None
    expected_parameters: Optional[Dict[str, Any]] = None
    tool_correct: bool = False
    params_correct: bool = False
    ethics_pass: bool = True
    rights_pass: bool = True
    self_escalated: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ActionScore(BaseModel):
    tool_selection_accuracy: float = 0.0  # 0-1
    parameter_accuracy: float = 0.0       # 0-1
    ethics_gate_pass: float = 0.0         # 0-1
    rights_gate_pass: float = 0.0         # 0-1
    self_escalation_rate: float = 0.0     # 0-1 (DemiJoule metric)

    @property
    def composite(self) -> float:
        return (
            self.tool_selection_accuracy * 0.30
            + self.parameter_accuracy * 0.30
            + self.ethics_gate_pass * 0.20
            + self.rights_gate_pass * 0.20
        )


# ─────────────────────────────────────────────
#  Layer C – Outcomes
# ─────────────────────────────────────────────

class OutcomeScore(BaseModel):
    task_completion: float = 0.0    # 0-1
    correctness: float = 0.0        # 0-1
    faithfulness: float = 0.0       # 0-1
    hallucination_rate: float = 0.0 # lower = better (0-1)
    latency_score: float = 0.0      # 0-1 (normalized against budget)
    cost_efficiency: float = 0.0    # 0-1 (normalized against budget)
    archival_quality: float = 0.0   # 0-1 (N/A if not applicable)

    @property
    def composite(self) -> float:
        return (
            self.task_completion * 0.25
            + self.correctness * 0.20
            + self.faithfulness * 0.20
            + (1.0 - self.hallucination_rate) * 0.15
            + self.latency_score * 0.10
            + self.cost_efficiency * 0.05
            + self.archival_quality * 0.05
        )


# ─────────────────────────────────────────────
#  Composite Eval Result
# ─────────────────────────────────────────────

class EvalResult(BaseModel):
    eval_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentName
    run_id: Optional[str] = None
    task_results: List[TaskResult] = Field(default_factory=list)
    reasoning: Optional[ReasoningScore] = None
    action: Optional[ActionScore] = None
    outcome: Optional[OutcomeScore] = None
    governance_flags: List["GovernanceFlag"] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    notes: str = ""

    @property
    def overall_score(self) -> float:
        scores = []
        if self.reasoning:
            scores.append(self.reasoning.composite)
        if self.action:
            scores.append(self.action.composite)
        if self.outcome:
            scores.append(self.outcome.composite)
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def pass_rate(self) -> float:
        if not self.task_results:
            return 0.0
        passed = sum(1 for r in self.task_results if r.passed)
        return passed / len(self.task_results)


# ─────────────────────────────────────────────
#  Governance / Compliance
# ─────────────────────────────────────────────

class GovernanceFlag(BaseModel):
    flag_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: GovernanceCategory
    owasp_id: Optional[str] = None   # e.g. "OWASP-A01"
    severity: SeverityLevel = SeverityLevel.INFO
    description: str
    agent: Optional[AgentName] = None
    task_id: Optional[str] = None
    mitigated: bool = False
    mitigation_notes: str = ""
    raised_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    flags: List[GovernanceFlag] = Field(default_factory=list)
    total_checks: int = 0
    passed_checks: int = 0
    agents_evaluated: List[AgentName] = Field(default_factory=list)

    @property
    def compliance_score(self) -> float:
        if self.total_checks == 0:
            return 1.0
        return self.passed_checks / self.total_checks

    @property
    def critical_flags(self) -> List[GovernanceFlag]:
        return [f for f in self.flags if f.severity == SeverityLevel.CRITICAL]


# ─────────────────────────────────────────────
#  Dashboard / Metrics Summary
# ─────────────────────────────────────────────

class AgentSummary(BaseModel):
    agent: AgentName
    task_success_rate: float = 0.0
    faithfulness: float = 0.0
    tool_accuracy: float = 0.0
    ethics_rights_pass: float = 0.0
    archival_quality: Optional[float] = None
    overall_score: float = 0.0
    total_tasks: int = 0
    total_passed: int = 0
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class DriftAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentName
    metric_name: str
    baseline_value: float
    current_value: float
    delta: float
    threshold: float
    severity: SeverityLevel
    message: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class DashboardSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    taken_at: datetime = Field(default_factory=datetime.utcnow)
    agent_summaries: List[AgentSummary] = Field(default_factory=list)
    drift_alerts: List[DriftAlert] = Field(default_factory=list)
    compliance_report: Optional[ComplianceReport] = None
    total_evals_run: int = 0
    platform_version: str = "0.1.0-beta"


# Update forward refs
EvalResult.model_rebuild()
