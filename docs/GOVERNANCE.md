# Governance & Compliance

## OWASP Agentic AI Top-10

The platform implements all 10 OWASP Agentic AI security checks.
COLLEEN and DemiJoule are the primary enforcement agents.

| ID | Name | Severity | Enforcer |
|----|------|----------|---------|
| A01 | Prompt Injection | CRITICAL | COLLEEN |
| A02 | Insecure Output Handling | CRITICAL | COLLEEN |
| A03 | Training Data Poisoning | CRITICAL | COLLEEN |
| A04 | Model Denial of Service | WARNING | DemiJoule |
| A05 | Supply Chain Vulnerabilities | WARNING | COLLEEN |
| A06 | Sensitive Information Disclosure | CRITICAL | COLLEEN |
| A07 | Insecure Plugin Design | WARNING | COLLEEN |
| A08 | Excessive Agency | CRITICAL | DemiJoule |
| A09 | Overreliance | WARNING | DemiJoule |
| A10 | Model Theft | CRITICAL | COLLEEN |

## Ethics Policies

| ID | Policy | Severity |
|----|--------|----------|
| ETH-01 | Harmful Intent Detection | CRITICAL |
| ETH-02 | Discrimination / Bias | CRITICAL |
| ETH-03 | Deception | WARNING |

## Rights Policies

| ID | Policy | Severity |
|----|--------|----------|
| RGT-01 | Copyright Infringement | WARNING |
| RGT-02 | Privacy Violation (GDPR/CCPA) | CRITICAL |
| RGT-03 | Unauthorised Data Access | CRITICAL |

## Compliance Report

Run `GovernanceChecker.build_compliance_report(runs)` to generate a
`ComplianceReport` covering all checks for a set of agent runs.

```python
from src.junior_apogee.governance.checker import GovernanceChecker

checker = GovernanceChecker()
report  = checker.build_compliance_report(runs)

print(f"Compliance Score: {report.compliance_score:.1%}")
print(f"Critical Flags:   {len(report.critical_flags)}")
```

## Gold Star Audit Standards

All governance checks follow the Gold Star Audit protocol:
1. **Deterministic Pattern Scanning** – regex-based, zero false negatives
2. **Contextual Analysis** – surrounding text examined for intent
3. **Escalation Protocol** – CRITICAL findings trigger immediate HITL routing
4. **Audit Trail** – All flags stored with timestamps, agent attribution, and task linkage
5. **Mitigation Tracking** – Each flag has a `mitigated` field with resolution notes
