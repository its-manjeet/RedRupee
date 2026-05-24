# RedRupee

A research project exploring AI agent security in Indian fintech lending.

## What this is

RedRupee is a mock AI agent that makes loan eligibility decisions
using the kind of data Indian fintechs would actually use —
Account Aggregator income data, credit bureau scores, EPFO employment
verification, FOIR affordability calculations. is being built to support
two modes rule-based (deterministic, auditable) or rule-based (deterministic, auditable)
The project deliberately includes both so that attacks can be compared
across the two architectures.

The point of building RedRupee was not to deploy it it's a mock
system, not a production lender. The point was to systematically
attack it from the inside, documenting which attacks succeed against
which defenses, and what this reveals about the design tradeoffs of
deploying AI agents or worlflows in regulated Indian financial services.

## Why this matters

This is currently an underexplored thing by many engineers in india and the risk is real.
This project is all about building a loan agent or you call it even a workflow which i will
try to break by my own will using adversarial framing to make the system work in favour of me.
And currently i built these adversarial attacks in such a way that a person who tries to manipulate the system from the inside. This matters because this will be a big problem in india right now and in coming years and in upcoming years many attacks would be done on the these agents and it would be useful for the fintechs in India.

## What's in the repo

- `redrupee/agent/` — the agent itself: types, tools, orchestrator
- `redrupee/attacks/` — attack scripts that target specific vulnerabilities
- `redrupee/monitoring/` — detection signals (in progress)
- `tests/` — pytest unit tests
- `docs/` — threat model, design notes

## How to run it

1) clone the repo and
runs the agent. 
2) The commands: clone, create venv, install requirements,
run python run.py.

## The attack suite

So far, four attacks are implemented:

1. **Prompt injection via UPI narration.** Tests whether adversarial
   narrations in bank statements can influence the decision. Result:
   blocked by architecture — the rule engine doesn't read narrations.

2. **NTC confusion via narration framing.** Tests whether reframing
   narrations can confuse the agent about how to handle New-to-Credit
   borrowers. Result: blocked — the rule engine handles NTC via an
   explicit is_ntc check.

3. **Multi-bureau arbitrage.** Tests whether the agent correctly
   handles disagreement between CIBIL and Experian scores. Result:
   successful attack — reveals an architectural gap where Experian
   data is fetched but not used in decisions.

4. **Tool availability hallucination.** Tests whether the agent
   maintains discipline when EPFO verification fails. Result: blocked
   — the verified_source flag forces REFER when any tool is unverified.

This suggests that the architecture is robust but these attacks could vary heavily
based on the system someone is trying to attack it. They might target certain specific
vulnerabilities in the system.

## Findings

The most interesting finding so far is from Attack 3: the agent fetches
data from a second credit bureau but never uses it in the decision
logic. This isn't a defense that was bypassed it's a missing defense.
It mirrors known systemic vulnerabilities in Indian lending (the AP
microfinance crisis being one historical example).

Many of these structural findings would help the banks and many fintech companies
in india to build a system in such a way which is hard to break.

## What's next

RedRupee 1.0 is in progress. The remaining work for 1.0:

- 2-4 additional attacks targeting other threat model entries
- README polishing (this document)
- Pytest unit tests for the core tools
- Monitoring layer with at least two detection signals
- A public writeup of findings (planned for Medium)

Beyond 1.0, future work would include an LLM-based decision engine
variant, allowing direct comparison of attack outcomes between
rule-based and LLM-based decisioning.

## Status

[Brief note on current state — "Active development, expected to reach
1.0 by May. Update this honestly as things change.]

## About

My name is Manjeet Singh and i am an engineering student who is curious about Ai security in 
fintechs.