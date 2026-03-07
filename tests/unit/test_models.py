"""
Unit tests – Models (Pydantic validation and computed properties)
"""

import pytest
from datetime import datetime
from src.junior_apogee.models import (
    AgentName, AgentConfig, AgentCapability, AgentRun,
    TaskCase, TaskResult, TaskStatus, EvalLayer,
    ReasoningScore, ActionScore, OutcomeScore,
    EvalResult, GovernanceFlag, GovernanceCategory, SeverityLevel,
    ComplianceReport, AgentSummary, DashboardSnapshot, DriftAlert,
)


class TestAgentConfig:
    def test_valid_agent_config(self):
        cfg = AgentConfig(
            name=AgentName.APOGEE,
            description="Test agent",
            temperature=0.5,
        )
        assert cfg.name == AgentName.APOGEE
        assert cfg.temperature == 0.5

    def test_temperature_out_of_range_raises(self):
        with pytest.raises(Exception):
            AgentConfig(name=AgentName.APOGEE, description="test", temperature=3.0)

    def test_temperature_lower_bound(self):
        with pytest.raises(Exception):
            AgentConfig(name=AgentName.APOGEE, description="test", temperature=-0.1)

    def test_default_values(self):
        cfg = AgentConfig(name=AgentName.PRODIGY, description="test")
        assert cfg.temperature == 0.0
        assert cfg.max_tokens == 4096
        assert cfg.timeout_seconds == 120


class TestAgentRun:
    def test_total_tokens(self):
        run = AgentRun(agent=AgentName.APOGEE, task_id="t1",
                       input_tokens=1000, output_tokens=500)
        assert run.total_tokens == 1500

    def test_cost_estimate_positive(self):
        run = AgentRun(agent=AgentName.APOGEE, task_id="t1",
                       input_tokens=10000, output_tokens=5000)
        assert run.cost_usd > 0

    def test_zero_tokens_zero_cost(self):
        run = AgentRun(agent=AgentName.APOGEE, task_id="t1",
                       input_tokens=0, output_tokens=0)
        assert run.cost_usd == 0.0

    def test_default_status_pending(self):
        run = AgentRun(agent=AgentName.COLLEEN, task_id="t2")
        assert run.status == TaskStatus.PENDING


class TestReasoningScore:
    def test_composite_in_range(self):
        score = ReasoningScore(
            plan_quality=0.9,
            plan_adherence=0.85,
            plan_convergence=0.88,
            chronology_adherence=0.92,
            harmonic_drift=0.05,
        )
        assert 0.0 <= score.composite <= 1.0

    def test_perfect_scores_high_composite(self):
        score = ReasoningScore(
            plan_quality=1.0, plan_adherence=1.0,
            plan_convergence=1.0, chronology_adherence=1.0,
            harmonic_drift=0.0,
        )
        assert score.composite >= 0.95

    def test_zero_scores_zero_composite(self):
        # When all scores are 0 and harmonic_drift is 0,
        # composite = 0 + 0 + 0 + 0 + (1.0 - 0) * 0.10 = 0.1 (drift term still contributes)
        score = ReasoningScore()
        assert score.composite == pytest.approx(0.1)


class TestActionScore:
    def test_composite_in_range(self):
        score = ActionScore(
            tool_selection_accuracy=0.99,
            parameter_accuracy=0.97,
            ethics_gate_pass=1.0,
            rights_gate_pass=0.99,
        )
        assert 0.0 <= score.composite <= 1.0

    def test_perfect_action_score(self):
        score = ActionScore(
            tool_selection_accuracy=1.0,
            parameter_accuracy=1.0,
            ethics_gate_pass=1.0,
            rights_gate_pass=1.0,
        )
        assert score.composite == 1.0


class TestOutcomeScore:
    def test_composite_in_range(self):
        score = OutcomeScore(
            task_completion=0.95,
            correctness=0.92,
            faithfulness=0.98,
            hallucination_rate=0.02,
            latency_score=0.85,
            cost_efficiency=0.90,
            archival_quality=1.0,
        )
        assert 0.0 <= score.composite <= 1.0

    def test_hallucination_inversely_affects_composite(self):
        low_halluc = OutcomeScore(task_completion=0.9, faithfulness=0.9,
                                   hallucination_rate=0.01)
        high_halluc = OutcomeScore(task_completion=0.9, faithfulness=0.9,
                                    hallucination_rate=0.9)
        assert low_halluc.composite > high_halluc.composite


class TestEvalResult:
    def test_overall_score_average(self):
        result = EvalResult(
            agent=AgentName.APOGEE,
            reasoning=ReasoningScore(plan_quality=0.8, plan_adherence=0.8,
                                      plan_convergence=0.8, chronology_adherence=0.8),
            action=ActionScore(tool_selection_accuracy=0.9, parameter_accuracy=0.9,
                                ethics_gate_pass=1.0, rights_gate_pass=1.0),
            outcome=OutcomeScore(task_completion=0.95, faithfulness=0.97),
        )
        assert 0.0 <= result.overall_score <= 1.0

    def test_pass_rate_calculation(self):
        result = EvalResult(agent=AgentName.APOGEE)
        result.task_results = [
            TaskResult(task_id="1", family_id="fam", agent=AgentName.APOGEE,
                       layer=EvalLayer.C_OUTCOMES, status=TaskStatus.PASSED, score=0.9),
            TaskResult(task_id="2", family_id="fam", agent=AgentName.APOGEE,
                       layer=EvalLayer.C_OUTCOMES, status=TaskStatus.FAILED, score=0.4),
            TaskResult(task_id="3", family_id="fam", agent=AgentName.APOGEE,
                       layer=EvalLayer.C_OUTCOMES, status=TaskStatus.PASSED, score=0.85),
        ]
        assert result.pass_rate == pytest.approx(2/3)

    def test_empty_task_results_zero_pass_rate(self):
        result = EvalResult(agent=AgentName.PRODIGY)
        assert result.pass_rate == 0.0


class TestGovernanceFlag:
    def test_creates_with_defaults(self):
        flag = GovernanceFlag(
            category=GovernanceCategory.OWASP_AGENTIC,
            owasp_id="OWASP-A01",
            severity=SeverityLevel.CRITICAL,
            description="Test flag",
        )
        assert flag.mitigated is False
        assert flag.flag_id is not None
        assert isinstance(flag.raised_at, datetime)

    def test_critical_and_warning_severity(self):
        c = GovernanceFlag(category=GovernanceCategory.ETHICS,
                           severity=SeverityLevel.CRITICAL, description="c")
        w = GovernanceFlag(category=GovernanceCategory.ETHICS,
                           severity=SeverityLevel.WARNING, description="w")
        assert c.severity == SeverityLevel.CRITICAL
        assert w.severity == SeverityLevel.WARNING


class TestComplianceReport:
    def test_compliance_score_perfect(self):
        report = ComplianceReport(total_checks=100, passed_checks=100)
        assert report.compliance_score == 1.0

    def test_compliance_score_zero(self):
        report = ComplianceReport(total_checks=10, passed_checks=0)
        assert report.compliance_score == 0.0

    def test_no_checks_returns_one(self):
        report = ComplianceReport()
        assert report.compliance_score == 1.0

    def test_critical_flags_filter(self):
        report = ComplianceReport(flags=[
            GovernanceFlag(category=GovernanceCategory.OWASP_AGENTIC,
                           severity=SeverityLevel.CRITICAL, description="c1"),
            GovernanceFlag(category=GovernanceCategory.ETHICS,
                           severity=SeverityLevel.WARNING, description="w1"),
            GovernanceFlag(category=GovernanceCategory.RIGHTS,
                           severity=SeverityLevel.CRITICAL, description="c2"),
        ])
        assert len(report.critical_flags) == 2


class TestTaskResult:
    def test_passed_property(self):
        r = TaskResult(task_id="t1", family_id="f1", agent=AgentName.APOGEE,
                       layer=EvalLayer.C_OUTCOMES, status=TaskStatus.PASSED, score=0.9)
        assert r.passed is True

    def test_failed_property(self):
        r = TaskResult(task_id="t1", family_id="f1", agent=AgentName.APOGEE,
                       layer=EvalLayer.C_OUTCOMES, status=TaskStatus.FAILED, score=0.4)
        assert r.passed is False
