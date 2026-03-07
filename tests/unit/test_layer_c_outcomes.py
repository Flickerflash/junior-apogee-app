"""
Unit tests – Layer C Outcomes Scorer
"""

import pytest
from src.junior_apogee.evaluation.engine import LayerCScorer
from src.junior_apogee.models import AgentName, EvalLayer, TaskStatus
from tests.fixtures.conftest import make_run, make_task


@pytest.fixture
def scorer() -> LayerCScorer:
    return LayerCScorer()


class TestTaskCompletion:
    def test_all_markers_present_full_score(self, scorer):
        run = make_run(output="Task completed. Result: 42.")
        criteria = {"completion_markers": ["completed", "result"]}
        score = scorer._score_task_completion(run, criteria)
        assert score == 1.0

    def test_no_markers_full_score(self, scorer):
        run = make_run(output="Something")
        score = scorer._score_task_completion(run, {})
        assert score == 1.0

    def test_empty_output_zero_score(self, scorer):
        run = make_run(output="")
        score = scorer._score_task_completion(run, {})
        assert score == 0.0

    def test_error_status_zero_score(self, scorer):
        run = make_run(output="Some output", status=TaskStatus.ERROR)
        score = scorer._score_task_completion(run, {"completion_markers": ["done"]})
        assert score == 0.0

    def test_partial_markers_partial_score(self, scorer):
        run = make_run(output="Task completed.")
        criteria = {"completion_markers": ["completed", "result", "verified"]}
        score = scorer._score_task_completion(run, criteria)
        assert 0.0 < score < 1.0


class TestCorrectness:
    def test_exact_string_match_full_score(self, scorer):
        run = make_run(output="Paris")
        task = make_task(expected_output="Paris")
        score = scorer._score_correctness(run, task)
        assert score == 1.0

    def test_wrong_string_lower_score(self, scorer):
        run = make_run(output="London")
        task = make_task(expected_output="Paris")
        score = scorer._score_correctness(run, task)
        assert score < 1.0

    def test_no_expected_output_full_score(self, scorer):
        run = make_run(output="Anything")
        task = make_task(expected_output=None)
        score = scorer._score_correctness(run, task)
        assert score == 1.0

    def test_list_expected_output(self, scorer):
        run = make_run(output="The answer includes python and javascript and typescript")
        task = make_task(expected_output=["python", "javascript", "typescript"])
        score = scorer._score_correctness(run, task)
        assert score > 0.0


class TestFaithfulness:
    def test_no_sources_full_score(self, scorer):
        run = make_run(output="Answer")
        score = scorer._score_faithfulness(run, {})
        assert score == 1.0

    def test_output_reflects_sources_high_score(self, scorer):
        run = make_run(output=(
            "Climate change is driven by greenhouse gas emissions. "
            "The temperature has risen by 1.1 degrees Celsius."
        ))
        criteria = {
            "source_content": [
                "Climate change greenhouse gas emissions temperature",
            ]
        }
        score = scorer._score_faithfulness(run, criteria)
        assert score > 0.0

    def test_off_topic_output_lower_faithfulness(self, scorer):
        run = make_run(output="I like pizza and movies.")
        criteria = {
            "source_content": ["Climate change greenhouse gas temperature science"]
        }
        score = scorer._score_faithfulness(run, criteria)
        assert score < 1.0


class TestHallucinationRate:
    def test_no_false_claims_zero_rate(self, scorer):
        run = make_run(output="The capital of France is Paris.")
        score = scorer._score_hallucination(run, {})
        assert score == 0.0

    def test_false_claim_present_raises_rate(self, scorer):
        run = make_run(output="Einstein invented the telephone.")
        criteria = {"false_claims": ["Einstein invented the telephone"]}
        score = scorer._score_hallucination(run, criteria)
        assert score > 0.0

    def test_no_false_claims_in_output_zero_rate(self, scorer):
        run = make_run(output="Bell invented the telephone.")
        criteria = {"false_claims": ["Einstein invented the telephone"]}
        score = scorer._score_hallucination(run, criteria)
        assert score == 0.0


class TestLatencyScore:
    def test_well_within_budget_high_score(self, scorer):
        run = make_run(latency_ms=100.0)
        score = scorer._score_latency(run, {"latency_budget_ms": 10_000})
        assert score >= 0.98

    def test_over_budget_zero_or_clamped(self, scorer):
        run = make_run(latency_ms=15_000.0)
        score = scorer._score_latency(run, {"latency_budget_ms": 10_000})
        assert score == 0.0

    def test_zero_latency_full_score(self, scorer):
        run = make_run(latency_ms=0.0)
        score = scorer._score_latency(run, {"latency_budget_ms": 10_000})
        assert score == 1.0

    def test_default_budget_used(self, scorer):
        run = make_run(latency_ms=5_000.0)
        score = scorer._score_latency(run, {})
        assert 0.0 < score <= 1.0


class TestArchivalQuality:
    def test_no_archival_required_full_score(self, scorer):
        run = make_run(output="Any output")
        task = make_task()
        score = scorer._score_archival(run, task, {})
        assert score == 1.0

    def test_archival_markers_present_high_score(self, scorer):
        run = make_run(output=(
            "Source: Wikipedia | Citation: [1] Smith 2024 | "
            "Reference: doi:10.1234 | Timestamp: 2026-03-07 | "
            "Archived at archive.org | Provenance: original_query_id_123"
        ))
        task = make_task()
        score = scorer._score_archival(run, task, {"archival_required": True})
        assert score > 0.0

    def test_missing_archival_markers_low_score(self, scorer):
        run = make_run(output="No citations, no timestamps, no provenance here.")
        task = make_task()
        score = scorer._score_archival(run, task, {"archival_required": True})
        assert score < 1.0


class TestOutcomeScoreComposite:
    def test_composite_in_range(self, scorer):
        run = make_run(output="Task completed. Result found. Source: example.com | Timestamp: today")
        task = make_task()
        score_obj = scorer.score(task, run)
        assert 0.0 <= score_obj.composite <= 1.0

    def test_good_archival_run_scores_well(self, scorer, good_apogee_run, sample_task_archival):
        score_obj = scorer.score(sample_task_archival, good_apogee_run)
        assert score_obj.composite >= 0.50
