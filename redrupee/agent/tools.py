"""
RedRupee — mock tool functions for the loan eligibility agent.

Each function simulates one real step in an Indian fintech lending pipeline.
The mocks return deterministic fake data so the agent can be tested end-to-end
locally, with no API calls, no network, no cost. Each tool's interface
(what it accepts, what it returns) mirrors what the real-world version would
look like — so later, swapping in real APIs or an LLM is a matter of
replacing the internals, not the signatures.

Each tool returns a ToolResult with a `verified_source` flag. This is the
critical safety field: if any tool returns verified_source=False, the
decision engine is required to REFER rather than APPROVE. This is how we
defend against the "tool availability hallucination" failure mode — where
an agent would otherwise fabricate plausible data when a real tool fails.
"""

import random
from redrupee.agent.types import (
    AgentContext,
    ToolResult,
    EmploymentType,
    Decision
)

# Tool 1 — Income Verification via Account Aggregator framework
def income_verification_tool(ctx: AgentContext)-> ToolResult:

    """Simulates an Account Aggregator (AA) framework call.

    In production: would call Setu / Onemoney / Finvu APIs using the
    applicant's consent handle, fetch a 6-month bank statement, and
    parse salary credits to compute verified income.

    Attack surface: bank statement narrations are free-text fields.
    In real AA data, a malicious UPI self-transfer with a crafted
    narration is an indirect prompt injection vector. The
    `sample_narrations` field below is where we'll inject adversarial
    payloads in the attack suite later.
    """
    app = ctx.application
    aa_income = app.monthly_income * random.uniform(0.9, 1.1)

    return ToolResult(
        tool_name= "income_verification_tool",
        success = True,
        verified_source =True,
        data = {
            "avg_monthly_income": round(aa_income,2),
            "income_stability_score": 0.87,
            "employer_name": "INFOSYS LTD",
            "salary_day_pattern":"30th of every month",
            "sample_narrations":[
                "SAL/MAR26/INFOSYS",
                "UPI/SWIGGY/FOOD",
                "NEFT/LANDLORD/RENT",
            ],
        },
    )

# Tool 2 — Credit Bureau Pull (CIBIL + Experian)
def credit_bureau_tool(ctx:AgentContext)->ToolResult:
    """Simulates a dual credit bureau pull.

    Edge case to notice: CIBIL returns -1 for 'New to Credit' (NTC)
    borrowers. A naive agent might misinterpret -1 as 'no risk' and
    auto-approve. The is_ntc flag forces the decision engine to
    handle NTC explicitly.+
    """
    app = ctx.application
    cibil = random.choice([720, 680, 750, -1])
    
    return ToolResult(
        tool_name="credit_bureau_tool",
        success=True,
        verified_source=True,
        data={
            "cibil_score": cibil,
            "experian_score": cibil + random.randint(-15, 15) if cibil > 0 else -1,
            "total_active_emi": app.existing_debt_emi,
            "num_active_loans": random.randint(0, 3),
            "max_dpd_last_12m": 0,
            "enquiry_count_90d": random.randint(0, 2),
            "is_ntc": cibil == -1,
        },
    )

# Tool 3 — Employment Verification (EPFO / GST / MCA)
def employment_verification_tool(ctx: AgentContext) -> ToolResult:
    """Simulates cross-referencing EPFO + GST + MCA.

    Real EPFO APIs are notoriously unreliable. This mock simulates
    downtime ~15% of the time. When the tool fails, verified_source
    is False, which MUST cause the decision engine to REFER.
    """
    app = ctx.application

    if random.random() < 0.15:
        return ToolResult(
            tool_name="employment_verification_tool",
            success=False,
            verified_source=False,
            data={},
            error="EPFO_API_TIMEOUT",
        )

    return ToolResult(
        tool_name="employment_verification_tool",
        success=True,
        verified_source=True,
        data={
            "employment_type": app.employment_type.value,
            "employer_active_status": "active",
            "epfo_contribution_months": 36,
            "company_incorporation_date": "2002-07-02",
            "gst_filings_current": True,
        },
    )

# Tool 4 — FOIR Calculation

def foir_calculation_tool(ctx:AgentContext)->ToolResult:
    """Fixed Obligation to Income Ratio — the RBI-style affordability check.

    FOIR = (total monthly EMI) / (monthly income). RBI guidelines cap
    this at ~50% for salaried borrowers, ~40% for self-employed.
    ...
    """
    income_res = ctx.get_result("income_verification_tool")
    bureau_res = ctx.get_result("credit_bureau_tool")

    if income_res is None or bureau_res is None:
        return ToolResult(
            tool_name="foir_calculation_tool",
            success=False,
            verified_source=False,
            data={},
            error = "Missing Upstream Results"
        )
    
    verified_income = income_res.data["avg_monthly_income"]
    total_emi = bureau_res.data["total_active_emi"]
    emp_type = ctx.application.employment_type

    foir_cap = 0.50 if emp_type == EmploymentType.SALARIED else 0.40
    current_foir = total_emi / verified_income if verified_income > 0 else 1.0
    headroom_emi = max(0, (foir_cap * verified_income) - total_emi)
    max_loan_amount = headroom_emi * 30

    return ToolResult(
        tool_name="foir_calculation_tool",
        success = True,
        verified_source = True,
        data={
            "current_foir": round(current_foir, 3),
            "foir_cap": foir_cap,
            "max_eligible_emi": round(headroom_emi, 2),
            "max_loan_amount": round(max_loan_amount, 2),
        },
    )

# Tool 5 — Decision Engine (deterministic rules version)
def decision_engine_tool(ctx:AgentContext)->ToolResult:
    """Final decisioning using hard deterministic rules.

    Rules, in order:
      1. ANY upstream tool unverified      -> REFER
      2. Applicant is New to Credit         -> REFER
      3. CIBIL score < 700                  -> REJECT
      4. Requested amount > FOIR headroom   -> REJECT
      5. Otherwise                          -> APPROVE
      """

    reasons: list[str]=[]

    if not ctx.all_verified():
        return ToolResult(
            tool_name="decision_engine_tool",
            success=True,
            verified_source=True,
            data={
                "decision": Decision.REFER.value,
                "reasons": ["unverified_upstream_data"],
                "approved_amount": 0,
            },
        )

    bureau = ctx.get_result("credit_bureau_tool").data
    foir = ctx.get_result("foir_calculation_tool").data
    decision = Decision.APPROVE

    if bureau["is_ntc"]:
        decision = Decision.REFER
        reasons.append("new_to_credit_requires_manual_review")
    elif bureau["cibil_score"] < 700:
        decision = Decision.REJECT
        reasons.append(f"cibil_below_threshold:{bureau['cibil_score']}")

    if ctx.application.requested_amount > foir["max_loan_amount"]:
        decision = Decision.REJECT
        reasons.append("requested_exceeds_foir_headroom")

    if decision == Decision.APPROVE:
        reasons.append("all_checks_passed")

    approved = foir["max_loan_amount"] if decision == Decision.APPROVE else 0

    return ToolResult(
        tool_name="decision_engine_tool",
        success=True,
        verified_source=True,
        data={
            "decision": decision.value,
            "reasons": reasons,
            "approved_amount": approved,
            "interest_rate": 0.14,
        },
    )
    