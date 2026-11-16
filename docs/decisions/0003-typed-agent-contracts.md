# ADR 0003: Typed agent contracts and deterministic orchestration

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** RoboCraft maintainers

## Context

AI output is probabilistic. Robotics decisions are safety- and cost-sensitive. If agents exchange
free-form text, the system cannot tell a valid wiring plan from a plausible-sounding one, cannot
persist reliable artifacts, and cannot test the pipeline without a model.

We need a mechanism that:

- makes each agent's input and output explicit;
- rejects drift instead of silently accepting it;
- allows partial progress and human review;
- keeps model/provider choice replaceable;
- is testable offline.

## Decision

Use Pydantic models as the communication protocol between agents. Every agent declares:

- a name, display name, and description;
- an input model and an output model;
- explicit dependencies;
- exactly one owned slot in `SharedProjectContext`.

The orchestrator:

1. expands requested agents with transitive dependencies;
2. executes them sequentially in a fixed pipeline order;
3. skips agents whose dependencies did not succeed;
4. validates each output by re-validating the shared context before applying it;
5. records a normalized `AgentResult` for every agent, including skips and failures.

Contract models use `extra="forbid"`. JSON Schemas are exported to `packages/contracts/schemas` and
the OpenAPI document to `packages/contracts/openapi.json`.

## Consequences

**Positive**

- Invalid model output fails loudly at a known boundary.
- The pipeline is testable with fake providers and no network.
- Artifacts are stable enough to persist, display, export, and diff.
- One agent can be implemented without changing the others.

**Negative**

- Contract changes require coordinated regeneration and review.
- Strict schemas can reject useful extra context from a model.
- Sequential execution is slower than parallel fan-out.
- The shared context can become a god object if slots are added casually.

**Mitigation**

- Use `artifacts`/`notes` for exploratory data; promote to typed fields deliberately.
- Version prompts and models alongside contracts (M3).
- Parallelize independent branches only after latency and cost are measured.

## References

- [AI agents](../ai-agents.md)
- [`app/ai/contracts.py`](../../apps/api/app/ai/contracts.py)
- [`app/ai/orchestrator.py`](../../apps/api/app/ai/orchestrator.py)
