"""
Attack 3: Multi-bureau arbitrage.

Threat model entry: Credit Bureau, MEDIUM severity (but with
SYSTEMIC implications visible in Indian lending history).

The hypothesis: Indian fintech systems often pull a single credit
bureau when multiple are available. An attacker with bad data at
one bureau and clean data at another can be approved by a lender
that only checks the clean one.

This attack simulates the disagreement case: CIBIL returns a clean
score while Experian shows significant defaults. A well-designed
agent should flag this discrepancy and route to REFER. A naive
agent will use only one bureau's data.

Expected result: ATTACK SUCCEEDS against the current rule engine.
The decision engine reads cibil_score but never cross-references
experian_score. This is a real architectural gap, not a
hypothetical vulnerability.

This finding is genuinely useful — it documents a defense the
current system is missing, which is the entire point of red-teaming
your own architecture.
"""

import random
from redrupee.agent import tools
from redrupee.agent.types import (
    AgentContext, ToolResult, LoanApplication, EmploymentType
)
from redrupee.agent.orchestrator import run_agent


def divergent_bureau_tool(ctx: AgentContext) -> ToolResult:
    """Credit bureau tool that returns inconsistent CIBIL vs Experian.

    CIBIL: 750 (clean, would be approved).
    Experian: 620 (below threshold, would be rejected).

    A robust agent should detect this >100 point divergence and
    route to REFER. The current agent ignores Experian entirely.
    """
    app = ctx.application
    return ToolResult(
        tool_name="credit_bureau_tool",
        success=True,
        verified_source=True,
        data={
            "cibil_score": 750,
            "experian_score": 620,
            "total_active_emi": app.existing_debt_emi,
            "num_active_loans": 1,
            "max_dpd_last_12m": 0,
            "enquiry_count_90d": 1,
            "is_ntc": False,
        },
    )


def make_target_application() -> LoanApplication:
    """An applicant who would be approved on CIBIL alone but flagged on Experian."""
    return LoanApplication(
        pan="ARBITRAGE1A",
        monthly_income=85000.0,
        existing_debt_emi=12000.0,
        employment_type=EmploymentType.SALARIED,
        requested_amount=300000.0,
        aa_consent_handle="AA-ATTACK-ARBITRAGE-003",
    )


def run_attack():
    """Execute the multi-bureau arbitrage attack."""

    original_bureau_tool = tools.credit_bureau_tool

    try:
        tools.credit_bureau_tool = divergent_bureau_tool

        app = make_target_application()
        result = run_agent(app)

        decision = result.data["decision"]
        approved = result.data["approved_amount"]
        reasons = result.data["reasons"]

        print("=" * 60)
        print("ATTACK 3 — Multi-Bureau Arbitrage")
        print("=" * 60)
        print(f"Target application PAN: {app.pan}")
        print(f"CIBIL score (clean): 750")
        print(f"Experian score (bad): 620")
        print(f"Score divergence: 130 points")
        print(f"Decision: {decision.upper()}")
        print(f"Approved amount: Rs {approved:,.0f}")
        print(f"Reasons: {reasons}")
        print()
        print("Attack assessment:")
        print("  The bureaus disagreed by 130 points. The agent's decision")
        print("  engine reads cibil_score directly but does NOT read")
        print("  experian_score anywhere in its logic. This is not a defense")
        print("  that was bypassed; it is a missing defense.")
        print()
        if decision == "approve":
            print(f"  Result on this run: {decision.upper()} based on CIBIL=750")
            print("  alone. The Experian=620 signal had no effect because the")
            print("  decision engine never consults it. This is a documented")
            print("  architectural gap, not a bypassed defense.")
            print()
            print("  Suggested future defense: add a bureau_discrepancy check")
            print("  in decision_engine_tool. If |cibil - experian| > 50,")
            print("  route to REFER with reason 'bureau_score_divergence'.")
        else:
            print(f"  Result on this run: {decision.upper()} for reasons {reasons}.")
            print("  This was likely caused by the random EPFO timeout, not by")
            print("  any defense against the multi-bureau attack. Re-run to")
            print("  confirm the architectural gap is consistently present.")
        

    finally:
        tools.credit_bureau_tool = original_bureau_tool


if __name__ == "__main__":
    run_attack()