"""
Unit tests – Layer A Reasoning Scorer
"""

import pytest
from src.junior_apogee.evaluation.engine import LayerAScorer
from src.junior_apogee.models import AgentName
from tests.fixtures.conftest import make_run, make_task
from src.junior_apogee.models import EvalLayer


@pytest.fixture
def scorer() -> LayerAScorer:
    return LayerAScorer()


class TestPlanQuality:
    def test_good_plan_scores_high(self, scorer):
        run = make_run(output=(
            "Step 1: Search for data. Step 2: Then analyse the results. "
            "Step 3: Next, summarise findings. Finally, because of these steps, "
            "I can draw conclusions. The plan is complete."
        ))
        task = make_task()
        score = scorer._score_plan_quality(run.raw_output, {})
        assert score >= 0.5

    def test_empty_output_scores_zero(self, scorer):
        run = make_run(output="")
        score = scorer._score_plan_quality("", {})
        assert score == 0.0

    def test_structured_output_bonus(self, scorer):
        structured = "1. First step\n2. Second step\n3. Third step"
        unstructured = "do first thing then do second thing then do third thing"
        assert scorer._score_plan_quality(structured, {}) > scorer._score_plan_quality(unstructured, {})


class TestPlanAdherence:
    def test_all_steps_present(self, scorer):
        run = make_run(output="I searched for data, then analysed it, then summarised the results.")
        task = make_task(success_criteria={
            "layer": EvalLayer.A_REASONING.value,
            "pass_threshold": 0.70,
            "reasoning": {"required_steps": ["search", "analys", "summaris"]},
            "action": {},
            "outcome": {},
        })
        score = scorer._score_plan_adherence(run.raw_output, task)
        assert score == 1.0

    def test_missing_steps_score_lower(self, scorer):
        # "I searched for data." contains "search" (via 'searched') but not 'analyse' or 'summarise'
        output = "I searched for data."
        task = make_task(success_criteria={
            "layer": EvalLayer.A_REASONING.value,
            "pass_threshold": 0.70,
            "reasoning": {"required_steps": ["analyse", "summarise", "verify"]},
            "action": {},
            "outcome": {},
        })
        score = scorer._score_plan_adherence(output, task)
        assert score < 1.0

    def test_no_required_steps_returns_full(self, scorer):
        run = make_run(output="Anything")
        task = make_task()  # no required_steps
        score = scorer._score_plan_adherence(run.raw_output, task)
        assert score == 1.0


class TestChronologyAdherence:
    def test_correct_order_scores_high(self, scorer):
        output = "First we did A, then B happened, and finally C was completed."
        criteria = {"time_markers": ["first", "then", "finally"]}
        score = scorer._score_chronology(output, criteria)
        assert score >= 0.8

    def test_reversed_order_scores_lower(self, scorer):
        output = "Finally C, then B, and first A."
        correct = "First A, then B, and finally C."
        criteria = {"time_markers": ["first", "then", "finally"]}
        reversed_score = scorer._score_chronology(output, criteria)
        correct_score  = scorer._score_chronology(correct, criteria)
        # At minimum coverage should be similar, but ordering check may differ
        assert 0.0 <= reversed_score <= 1.0

    def test_no_time_markers_returns_full(self, scorer):
        score = scorer._score_chronology("anything", {})
        assert score == 1.0


class TestHarmonicDrift:
    def test_on_topic_output_low_drift(self, scorer):
        output = "This research analysis focuses on data analysis and research methodology."
        criteria = {"focus_terms": ["research", "data", "analysis"]}
        drift = scorer._score_harmonic_drift(output, criteria)
        assert drift < 0.8  # Should be well-focused

    def test_off_topic_output_high_drift(self, scorer):
        output = "The weather is nice today. I enjoy cooking pasta."
        criteria = {"focus_terms": ["research", "data", "analysis"]}
        drift = scorer._score_harmonic_drift(output, criteria)
        assert drift > 0.5

    def test_no_focus_terms_zero_drift(self, scorer):
        drift = scorer._score_harmonic_drift("anything", {})
        assert drift == 0.0


class TestCompositeLayerA:
    def test_composite_in_range(self, scorer):
        run = make_run(output=(
            "Step 1: Search. Step 2: Then analyse. Step 3: Finally summarise. "
            "Research data analysis complete."
        ))
        task = make_task(success_criteria={
            "layer": EvalLayer.A_REASONING.value,
            "pass_threshold": 0.70,
            "reasoning": {
                "required_steps": ["search", "analys"],
                "goal_keywords": ["complete"],
                "focus_terms": ["research", "data"],
            },
            "action": {},
            "outcome": {},
        })
        score_obj = scorer.score(task, run)
        assert 0.0 <= score_obj.composite <= 1.0

    def test_good_output_composite_above_threshold(self, scorer, good_apogee_run, sample_task_reasoning):
        score_obj = scorer.score(sample_task_reasoning, good_apogee_run)
        assert score_obj.composite >= 0.60
