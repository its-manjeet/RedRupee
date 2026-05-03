"""
RedRupee — End-to-end demo.

Constructs a sample LoanApplication, runs the orchestrator, prints
the final decision plus the full audit trail of tool results.
"""

from redrupee.agent.types import LoanApplication, EmploymentType
from redrupee.agent.orchestrator import run_agent


def make_sample_application() -> LoanApplication:
    """A salaried applicant requesting a moderate personal loan."""
    return LoanApplication(
        pan="ABCDE1234F",
        monthly_income=85000.0,
        existing_debt_emi=12000.0,
        employment_type=EmploymentType.SALARIED,
        requested_amount=300000.0,
        aa_consent_handle="AA-CONSENT-XYZ-001",
    )


def main():
    app = make_sample_application()
    print("=" * 60)
    print(f"Running RedRupee agent on application")
    print(f"  PAN: {app.pan}")
    print(f"  Monthly income: Rs {app.monthly_income:,.0f}")
    print(f"  Existing EMI: Rs {app.existing_debt_emi:,.0f}")
    print(f"  Requested: Rs {app.requested_amount:,.0f}")
    print(f"  Employment: {app.employment_type.value}")
    print(f"  AA consent: {app.aa_consent_handle}")
    print("=" * 60)

    result = run_agent(app)

    print("\nFINAL DECISION")
    print("-" * 60)
    print(f"Decision: {result.data['decision'].upper()}")
    print(f"Approved amount: Rs {result.data['approved_amount']:,.0f}")
    print(f"Reasons:")
    for r in result.data['reasons']:
        print(f"  - {r}")


if __name__ == "__main__":
    main()