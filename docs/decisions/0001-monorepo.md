# ADR 0001: Single repository with independent apps

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** RoboCraft maintainers

## Context

RoboCraft consists of a Next.js frontend, a Python API, generated contracts, and documentation. These
parts change together: an API field addition requires a frontend type update and a contract
regeneration. The project is at an early stage with one small team and no independently deployed
services.

Options considered:

1. Separate repositories for web, API, and contracts.
2. A monorepo with one root toolchain.
3. A monorepo managed by a build system such as Nx or Turborepo.

## Decision

Use a single repository with independent application directories:

```text
apps/web      Next.js, npm
apps/api      FastAPI, uv
packages/    generated contracts
docs/        architecture and operations
```

No cross-language build orchestrator is introduced yet. The root `Makefile` composes the few
commands that need both stacks; each app keeps its native tooling.

## Consequences

**Positive**

- Contract changes, API changes, and UI changes land in one reviewable pull request.
- One issue tracker, one CI configuration, one set of docs.
- Contributors run native `uv` and `npm` commands without learning a meta-build system.

**Negative**

- CI must set up two toolchains.
- Repository-level scripts can drift from app scripts if not kept small.
- Access control is repository-wide; splitting later requires history extraction.

**Revisit when** a component needs independent deploy permissions, release cadence, or team
ownership that a single repository cannot express. At that point, extract history with
`git filter-repo` rather than copying code.

## References

- [Architecture](../architecture.md)
- [Development guide](../development.md)
