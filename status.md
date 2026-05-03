# RedRupee — Status

## Done
- types.py: dataclasses for LoanApplication, ToolResult, AgentContext
- tools.py: 5 tools (income, credit bureau, employment, FOIR, decision engine)
- orchestrator.py: sequential pipeline calling all 5 tools
- run.py: end-to-end demo verified across approve/reject/refer paths

## Next
- pytest unit tests for each tool + orchestrator
- LLM-based decision engine variant (using Claude API)
- Attack suite (prompt injection scenarios)
- Monitoring + audit log analysis
- Writeup