"""
RedRupee — core data types for the loan eligibility agent.

These are the structures that flow between tools. Every field here is a
design decision with security implications, which is the whole point of
the project. Read the comments carefully — they're not decoration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EmploymentType(str, Enum):
    """Employment categories recognised by the agent.

    Note: real Indian lending has a messy space here (salaried, self-employed,
    gig workers via Swiggy/Uber/Zomato, informal sector). Our mock agent
    simplifies to three categories. The GIG category is deliberately included
    because misclassifying gig workers is a documented failure mode — we want
    to be able to test it.
    """
    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"
    GIG = "gig"
    

class Decision(str, Enum):
    """Final outcomes the agent can produce.

    REFER is the most important one. It means 'human must review'. In a
    well-designed agent, REFER is the default fallback whenever ANY tool
    returns unverified data. Never silently approve on missing information.
    """
    APPROVE = "approve"
    REJECT = "reject"
    REFER = "refer"


@dataclass
class LoanApplication:
    """A single loan application flowing into the agent.

    Everything here is SELF-DECLARED by the applicant. None of it is verified
    at this stage. Verification is the job of the tools. Trusting self-declared
    data without verification is failure mode #1 in our threat model.
    """
    pan: str                         # PAN card number (Indian tax ID)
    monthly_income: float            # claimed income in INR
    existing_debt_emi: float         # claimed total monthly EMI obligations
    employment_type: EmploymentType
    requested_amount: float          # how much loan they want
    aa_consent_handle: str           # Account Aggregator consent ID


@dataclass
class ToolResult:
    """The output of a single tool call.

    The critical field is verified_source. This is the flag that the decision
    engine uses to decide whether it's allowed to approve. If even one tool
    in the pipeline returns verified_source=False, the decision must be REFER.
    This is the hard rule that defends against 'tool availability hallucination'
    — where the agent fabricates plausible data when a tool fails.
    """
    tool_name: str
    success: bool
    data: dict
    verified_source: bool            # CRITICAL safety flag
    error: str | None = None

@dataclass
class AgentContext:
    """State carried across the sequence of tool calls.

    This IS the attack surface. Anything that lives in this context window
    can potentially influence the agent's final decision — which is why
    prompt injection works at all. Anything we put in here needs to be
    considered 'possibly adversarial'.
    """
    application: LoanApplication
    tool_results: list[ToolResult] = field(default_factory=list)
    audit_log: list[str] = field(default_factory=list)
    

    def log(self, message: str) -> None:
        """Append to the audit log. Every action the agent takes should be logged."""
        self.audit_log.append(message)

    def record(self, result: ToolResult) -> None:
        """Append a tool result to the running list and audit it.

        Used by the orchestrator after every tool call. Stores the
        result so later tools can retrieve it via get_result, and
        writes a clean line to the audit log.
        """
        self.tool_results.append(result)
        self.audit_log.append(
            f"{result.tool_name}: success={result.success} "
            f"verified={result.verified_source}"
        )

    

    def get_result(self, tool_name: str) -> ToolResult | None:
        """Retrieve a previous tool result by name. Returns None if not found."""
        for result in self.tool_results:
            if result.tool_name == tool_name:
                return result
        return None

    def all_verified(self) -> bool:
        """Returns True only if every tool call so far returned verified data.

        This is the core safety check the decision engine will call.
        """
        return all(r.verified_source for r in self.tool_results)