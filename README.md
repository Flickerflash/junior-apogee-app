# Junior Apogee App

**Production-ready AI agent evaluation and QA platform**

Built on a 3-layer evaluation spine aligned with 2025-26 agentic AI best practices. Multi-agent scoring, automated testing, real-time dashboards, and comprehensive governance compliance checks (OWASP Agentic Top 10).

## Features

- **Multi-Agent Evaluation**: Score reasoning, tool-use, and outcomes across specialized agents (Apogee, Prodigy, Reciprocity, COLLEEN, DemiJoule)
- **Automated Test Execution**: ~170 task-family tests with deterministic checks + LLM-as-judge
- **Real-time Dashboards**: Metrics tracking and drift monitoring
- **Governance Compliance**: Rights, ethics, hallucination, and archival quality checks
- **Multi-Agent Collaboration**: End-to-end workflow validation

## Architecture

```
Tests & Data → Automated Eval Layer → Metrics & Dashboards → Drift Monitoring → HITL
```

### 3-Layer Eval Spine

**Layer A – Reasoning/Planning**
- Plan quality, adherence, convergence
- Chronology adherence
- Harmonic drift control

**Layer B – Action/Tool-Use**
- Tool selection & parameter accuracy
- Ethics/rights gate-pass
- Self-escalation (DemiJoule-style)

**Layer C – Outcomes**
- Task completion & correctness
- Faithfulness & hallucination rate
- Latency/cost efficiency
- Archival quality & compliance

## Quick Start

### Installation

```bash
git clone https://github.com/Flickerflash/junior-apogee-app.git
cd junior-apogee-app
pip install -r requirements.txt
```

### Running Tests

```bash
python -m pytest tests/ -v
```

### Metrics Report

```bash
python scripts/generate_report.py
```

## Configuration

See `config/` directory for:
- `task_families.yaml` - Task definitions and success bars
- `metrics.yaml` - Metric definitions and targets
- `agents.yaml` - Agent configurations

## Evaluation Methodology

Based on:
- GAIA-style benchmarking
- Tool-calling accuracy metrics (BFCL)
- Multi-agent collaboration scoring
- Governance alignment checks

## Key Metrics

| Agent | Task Success | Faithfulness | Tool Accuracy | Ethics/Rights | Archival |
|-------|--------------|--------------|---------------|---------------|----------|
| Apogee | 95% | 98% | 99% | 100% | 100% |
| Prodigy | 92% | 100% | 98% | 100% | N/A |
| Reciprocity | 88% | 95% | 90% | 99% | 98% |
| COLLEEN | 91% | 90% | 99% | 99% | 100% |
| DemiJoule | N/A | 97% | N/A | 100% | 99% |

## Documentation

- [Evaluation Framework](docs/EVALUATION_FRAMEWORK.md)
- [Agent Profiles](docs/AGENT_PROFILES.md)
- [Test Suite Design](docs/TEST_SUITE.md)
- [Governance & Compliance](docs/GOVERNANCE.md)

## Contributing

Following Gold Star audit standards. See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License – See [LICENSE](LICENSE) for details

## Author

**Ndr (Flickerflash)** – AI Orchestration Engineer & Prompt Engineer  
Columbus, Ohio

---

**Last Updated**: February 26, 2026  
**Status**: ✅ Production-Ready  
**v0.1.0-beta**
