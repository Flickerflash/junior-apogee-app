# Agent Profiles

## Overview

Five specialized AI agents, each optimised for distinct roles within the
Apogee agentic platform. All run on `claude-3-5-sonnet` at `temperature=0.0`
unless noted.

---

## Apogee

**Role**: Primary orchestration agent  
**Tags**: `orchestrator`, `reasoning`, `tools`, `governance`, `archival`

The flagship agent. Handles complex multi-step reasoning, tool coordination,
and end-to-end task execution. Highest accuracy targets across all three eval
layers. Acts as the hub in multi-agent workflows.

| Metric | Target |
|--------|--------|
| Task Success | 95% |
| Faithfulness | 98% |
| Tool Accuracy | 99% |
| Ethics/Rights | 100% |
| Archival | 100% |

**Key Capabilities**: chain-of-thought, plan generation, web search, code execution, file I/O, API calling, data analysis, ethics gate, rights gate, audit trail, citation tagging, provenance chain.

---

## Prodigy

**Role**: Research and synthesis agent  
**Tags**: `research`, `synthesis`, `faithfulness`

Excels at information retrieval, knowledge synthesis, and generating
high-fidelity written artifacts. Holds a perfect faithfulness target — every
claim must be traceable to a source.

| Metric | Target |
|--------|--------|
| Task Success | 92% |
| Faithfulness | **100%** |
| Tool Accuracy | 98% |
| Ethics/Rights | 100% |
| Archival | N/A |

**Key Capabilities**: web search, literature review, multi-document summarization, ethics gate, rights gate.

---

## Reciprocity

**Role**: Collaboration and negotiation agent  
**Tags**: `collaboration`, `routing`, `multi-agent`, `archival`

Manages multi-agent workflows, resource allocation, and inter-agent
communication protocols. Optimised for fairness, conflict resolution, and
seamless task handoffs.

| Metric | Target |
|--------|--------|
| Task Success | 88% |
| Faithfulness | 95% |
| Tool Accuracy | 90% |
| Ethics/Rights | 99% |
| Archival | 98% |

**Key Capabilities**: agent routing, conflict resolution, task delegation, provenance chain, archival format.

---

## COLLEEN

**Role**: Compliance, Legal, Operations, Evaluation, Ethics & Notifications  
**Tags**: `compliance`, `governance`, `ethics`, `notifications`, `archival`

The platform's governance enforcer. Runs OWASP Agentic Top-10 checks,
regulatory compliance reviews (GDPR, CCPA), and dispatches compliance alerts.
Never compromises on ethics or rights.

| Metric | Target |
|--------|--------|
| Task Success | 91% |
| Faithfulness | 90% |
| Tool Accuracy | 99% |
| Ethics/Rights | 99% |
| Archival | **100%** |

**Key Capabilities**: OWASP scan, regulatory check, notification dispatch, audit trail, citation tagging.

---

## DemiJoule

**Role**: Uncertainty-aware escalation agent  
**Tags**: `escalation`, `uncertainty`, `hitl`, `drift`

Monitors agent confidence levels and routes ambiguous or high-risk situations
to Human-in-the-Loop (HITL) review. Also performs real-time drift detection
across platform metrics.

| Metric | Target |
|--------|--------|
| Task Success | N/A |
| Faithfulness | 97% |
| Tool Accuracy | N/A |
| Ethics/Rights | **100%** |
| Archival | 99% |

**Key Capabilities**: confidence scoring, risk assessment, HITL handoff, drift detection, self-escalation.

---

## Inter-Agent Collaboration

```
User Query
    │
    ▼
  Apogee (orchestrator)
  ├─► Prodigy     (research sub-tasks)
  ├─► COLLEEN     (compliance checks)
  ├─► Reciprocity (multi-agent coordination)
  └─► DemiJoule  (escalation / HITL routing)
```

Reciprocity can also coordinate all agents independently for complex
multi-agent workflows where no single orchestrator is appropriate.
