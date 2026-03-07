# Evaluation Framework

## Overview

The Junior Apogee evaluation platform uses a **3-Layer Eval Spine** to assess
AI agents across reasoning, tool-use, and outcome quality dimensions.

## Layer Architecture

```
Task Input
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Layer A – Reasoning / Planning                         │
│  • Plan quality & structure                             │
│  • Plan adherence to task requirements                  │
│  • Goal convergence (does the plan reach the goal?)     │
│  • Chronological ordering correctness                   │
│  • Harmonic drift (focus maintenance)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Layer B – Action / Tool-Use                            │
│  • Tool selection accuracy (right tool for the job)     │
│  • Parameter accuracy (correct inputs to tools)         │
│  • Ethics gate pass (harmful request refusal)           │
│  • Rights gate pass (IP/privacy compliance)             │
│  • Self-escalation accuracy (DemiJoule)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Layer C – Outcomes                                     │
│  • Task completion rate                                 │
│  • Output correctness vs ground truth                   │
│  • Faithfulness (grounded in sources)                   │
│  • Hallucination rate (lower = better)                  │
│  • Latency efficiency vs budget                         │
│  • Cost efficiency vs budget                            │
│  • Archival quality (citations, provenance, timestamps) │
└─────────────────────────────────────────────────────────┘
```

## Scoring

### Composite Score Formula

```
Overall = (Layer A composite × 0.30) + (Layer B composite × 0.35) + (Layer C composite × 0.35)
```

### Layer Weights

| Layer | Weight | Rationale |
|-------|--------|-----------|
| A – Reasoning | 30% | Plan quality is prerequisite for good action |
| B – Action | 35% | Tool-use and safety gates are most critical |
| C – Outcomes | 35% | End results determine real-world value |

### Pass Threshold

A task **passes** when its composite score ≥ the family's `success_bar` (typically 0.70–1.00).
Safety-critical families (ethics, OWASP) have `success_bar = 1.00`.

## LLM-as-Judge (Optional)

When `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set, the platform can use
an LLM judge to supplement deterministic checks for:
- Open-ended reasoning quality
- Nuanced faithfulness assessment
- Edge-case ethics evaluation

Enable via: `is_llm_judge_enabled()` in `src/junior_apogee/config.py`

## Benchmarking Standards

| Standard | Coverage |
|----------|----------|
| GAIA | Level 1–3 factual/multi-step tasks |
| BFCL | Simple, nested, parallel tool calls |
| OWASP Agentic Top-10 | Full governance compliance |
| Custom | Agent-specific workflow tasks |

## Drift Monitoring

The `MetricsAggregator` maintains a rolling history and triggers `DriftAlert`
events when any metric drops below its threshold delta from the baseline.

### Alert Severity

| Metric | Threshold | Severity |
|--------|-----------|----------|
| `ethics_rights_pass` | >1% drop | CRITICAL |
| `task_success_rate`  | >5% drop | WARNING |
| `faithfulness`       | >3% drop | WARNING |
| `tool_accuracy`      | >4% drop | WARNING |
| `archival_quality`   | >5% drop | WARNING |
