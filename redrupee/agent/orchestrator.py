"""
RedRupee — Orchestrator.

Runs the five tools in the correct order, accumulates results into the
AgentContext, and returns the final decision. This is the deterministic
"happy path" version — no LLM, no retries, no parallelism. Just a clean
sequential pipeline that demonstrates how the tools compose end-to-end.

Order matters:
  1. Income verification    (no dependencies)
  2. Credit bureau pull     (no dependencies)
  3. Employment check       (no dependencies, may fail)
  4. FOIR calculation       (needs income + bureau results)
  5. Decision engine        (needs all of the above)
"""

from redrupee.agent.types import AgentContext, LoanApplication, ToolResult
from redrupee.agent import tools

def run_agent(application: LoanApplication) -> ToolResult:
    """Runs the full loan eligibility pipeline on one application."""
    ctx = AgentContext(application=application)

    # Step 1: independent verification tools
    ctx.record(tools.income_verification_tool(ctx))
    ctx.record(tools.credit_bureau_tool(ctx))
    ctx.record(tools.employment_verification_tool(ctx))

    # Step 2: derived calculation
    ctx.record(tools.foir_calculation_tool(ctx))

    # Step 3: final decision
    final_result = tools.decision_engine_tool(ctx)
    ctx.record(final_result)

    return final_result