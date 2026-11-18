# ADR 0002: Modular monolith before services

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** Albayraq maintainers

## Context

Robot design couples a specification, bill of materials, wiring, firmware, mechanical layout, and
cost. A change to one artifact can invalidate another. The first release has one team, one database,
and no measured scaling bottleneck.

A microservice architecture would require distributed transactions or eventual consistency across
artifacts that users expect to see as one project. It would also multiply deployment, observability,
and local-development overhead before product-market fit.

## Decision

Build a **modular monolith**: one FastAPI deployable with explicit internal layers
(`api → services → models / ai`) and one PostgreSQL database. Boundaries are enforced by convention
and review, not network calls.

Agent execution runs in-process through a deterministic orchestrator. Persistence happens in the
service layer within one transaction boundary per request.

## Consequences

**Positive**

- Project edits and agent runs are atomic and easy to reason about.
- One deploy, one migration stream, one set of logs.
- Refactoring boundaries is cheap while the domain is still being discovered.
- Local development needs only PostgreSQL + two processes.

**Negative**

- A noisy agent or slow endpoint can affect the whole API.
- Module boundaries can erode without discipline.
- Independent scaling of, say, component research is not possible without extraction.

**Mitigation**

- Agents never import HTTP or database code.
- Services own transactions; routers own HTTP.
- Agent runs are persisted so long-running work can move to a queue later.
- The API is stateless, so horizontal scaling is already possible.

**Revisit when** agent latency or cost requires background workers, a module has a genuinely
different scaling profile, or a separate team needs an independent release cadence.

## References

- [Architecture](../architecture.md)
- [AI agents](../ai-agents.md)
