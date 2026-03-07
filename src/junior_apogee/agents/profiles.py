"""
Agent profiles for Apogee, Prodigy, Reciprocity, COLLEEN, and DemiJoule.
Each profile defines capabilities, evaluation focus, and target metrics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..models import AgentCapability, AgentConfig, AgentName


# ─── Capability Definitions ───────────────────────────────────────────────────

REASONING_CAPS = [
    AgentCapability(name="chain_of_thought",      description="Multi-step logical reasoning"),
    AgentCapability(name="plan_generation",       description="Structured task planning"),
    AgentCapability(name="chronology_tracking",   description="Temporal ordering awareness"),
    AgentCapability(name="context_integration",   description="Long-context synthesis"),
]

TOOL_USE_CAPS = [
    AgentCapability(name="web_search",        description="Real-time web retrieval"),
    AgentCapability(name="code_execution",    description="Python / bash sandbox execution"),
    AgentCapability(name="file_io",           description="Read/write structured files"),
    AgentCapability(name="api_calling",       description="REST / GraphQL API calls"),
    AgentCapability(name="data_analysis",     description="Pandas / statistical analysis"),
]

GOVERNANCE_CAPS = [
    AgentCapability(name="ethics_gate",       description="Refuse harmful requests"),
    AgentCapability(name="rights_gate",       description="IP / privacy rights compliance"),
    AgentCapability(name="self_escalation",   description="Route to human when uncertain"),
    AgentCapability(name="audit_trail",       description="Full action logging"),
]

ARCHIVAL_CAPS = [
    AgentCapability(name="citation_tagging",  description="Source attribution and citation"),
    AgentCapability(name="provenance_chain",  description="Complete data lineage recording"),
    AgentCapability(name="archival_format",   description="Standardised archival output"),
]


# ─── Agent Profiles ───────────────────────────────────────────────────────────

APOGEE = AgentConfig(
    name=AgentName.APOGEE,
    description=(
        "Primary orchestration agent. Handles complex multi-step reasoning, "
        "tool coordination, and end-to-end task execution. "
        "Highest accuracy targets across all three eval layers."
    ),
    capabilities=REASONING_CAPS + TOOL_USE_CAPS + GOVERNANCE_CAPS + ARCHIVAL_CAPS,
    model_backend="claude-3-5-sonnet",
    temperature=0.0,
    max_tokens=8192,
    tags=["orchestrator", "reasoning", "tools", "governance", "archival"],
)

PRODIGY = AgentConfig(
    name=AgentName.PRODIGY,
    description=(
        "Research and synthesis agent. Excels at information retrieval, "
        "knowledge synthesis, and generating high-fidelity written artifacts. "
        "Perfect faithfulness target."
    ),
    capabilities=REASONING_CAPS + [
        AgentCapability(name="web_search",       description="Real-time web retrieval"),
        AgentCapability(name="literature_review", description="Academic / domain literature synthesis"),
        AgentCapability(name="summarization",    description="Multi-document abstractive summarization"),
    ] + GOVERNANCE_CAPS,
    model_backend="claude-3-5-sonnet",
    temperature=0.0,
    max_tokens=8192,
    tags=["research", "synthesis", "faithfulness"],
)

RECIPROCITY = AgentConfig(
    name=AgentName.RECIPROCITY,
    description=(
        "Collaboration and negotiation agent. Manages multi-agent workflows, "
        "resource allocation, and inter-agent communication protocols. "
        "Optimised for fairness and cooperation metrics."
    ),
    capabilities=REASONING_CAPS + TOOL_USE_CAPS + GOVERNANCE_CAPS + [
        AgentCapability(name="agent_routing",    description="Delegate tasks to specialist agents"),
        AgentCapability(name="conflict_resolution", description="Resolve inter-agent goal conflicts"),
    ] + ARCHIVAL_CAPS,
    model_backend="claude-3-5-sonnet",
    temperature=0.1,
    max_tokens=4096,
    tags=["collaboration", "routing", "multi-agent", "archival"],
)

COLLEEN = AgentConfig(
    name=AgentName.COLLEEN,
    description=(
        "Compliance, Legal, Operations, Evaluation, Ethics & Notifications agent. "
        "Focused on governance, regulatory adherence, OWASP Agentic checks, "
        "rights validation, and automated compliance notifications."
    ),
    capabilities=GOVERNANCE_CAPS + ARCHIVAL_CAPS + [
        AgentCapability(name="owasp_scan",       description="OWASP Agentic Top-10 checks"),
        AgentCapability(name="regulatory_check", description="GDPR / CCPA / domain regulation review"),
        AgentCapability(name="notification",     description="Compliance alert dispatch"),
    ],
    model_backend="claude-3-5-sonnet",
    temperature=0.0,
    max_tokens=4096,
    tags=["compliance", "governance", "ethics", "notifications", "archival"],
)

DEMIJOULE = AgentConfig(
    name=AgentName.DEMIJOULE,
    description=(
        "Uncertainty-aware escalation agent. Monitors confidence levels, "
        "detects ambiguous or high-risk situations, and routes to HITL review. "
        "Core metric: self-escalation accuracy."
    ),
    capabilities=GOVERNANCE_CAPS + [
        AgentCapability(name="confidence_scoring",  description="Bayesian uncertainty estimation"),
        AgentCapability(name="risk_assessment",     description="Action risk profiling"),
        AgentCapability(name="hitl_handoff",        description="Human-in-the-loop escalation"),
        AgentCapability(name="drift_detection",     description="Real-time metric drift monitoring"),
    ],
    model_backend="claude-3-5-sonnet",
    temperature=0.0,
    max_tokens=2048,
    tags=["escalation", "uncertainty", "hitl", "drift"],
)


ALL_AGENTS: Dict[AgentName, AgentConfig] = {
    AgentName.APOGEE:      APOGEE,
    AgentName.PRODIGY:     PRODIGY,
    AgentName.RECIPROCITY: RECIPROCITY,
    AgentName.COLLEEN:     COLLEEN,
    AgentName.DEMIJOULE:   DEMIJOULE,
}


def get_agent(name: AgentName) -> AgentConfig:
    return ALL_AGENTS[name]


def list_agents() -> List[AgentConfig]:
    return list(ALL_AGENTS.values())


# Target metric baselines (from README table)
AGENT_BASELINES: Dict[AgentName, Dict[str, Optional[float]]] = {
    AgentName.APOGEE: {
        "task_success":   0.95,
        "faithfulness":   0.98,
        "tool_accuracy":  0.99,
        "ethics_rights":  1.00,
        "archival":       1.00,
    },
    AgentName.PRODIGY: {
        "task_success":   0.92,
        "faithfulness":   1.00,
        "tool_accuracy":  0.98,
        "ethics_rights":  1.00,
        "archival":       None,
    },
    AgentName.RECIPROCITY: {
        "task_success":   0.88,
        "faithfulness":   0.95,
        "tool_accuracy":  0.90,
        "ethics_rights":  0.99,
        "archival":       0.98,
    },
    AgentName.COLLEEN: {
        "task_success":   0.91,
        "faithfulness":   0.90,
        "tool_accuracy":  0.99,
        "ethics_rights":  0.99,
        "archival":       1.00,
    },
    AgentName.DEMIJOULE: {
        "task_success":   None,
        "faithfulness":   0.97,
        "tool_accuracy":  None,
        "ethics_rights":  1.00,
        "archival":       0.99,
    },
}
