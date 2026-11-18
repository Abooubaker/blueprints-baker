# ADR 0004: PostgreSQL, SQLAlchemy async, and Alembic

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** Blueprints Baker maintainers

## Context

Blueprints Baker stores a project aggregate with strict relationships, commercial snapshots, evolving
engineering JSON, and an append-only agent audit log. The API is async because model and supplier
calls will be I/O-bound.

Candidate approaches:

1. PostgreSQL + SQLAlchemy 2 async + Alembic.
2. PostgreSQL + an async query builder (e.g. SQLModel, databases, Piccolo).
3. A document database (e.g. MongoDB) because artifacts are JSON-like.
4. SQLite for production simplicity.

## Decision

Use **PostgreSQL 16** as the runtime database, **SQLAlchemy 2.0 async ORM** for persistence, and
**Alembic** for versioned migrations.

- UUID primary keys generated in Python.
- Timezone-aware timestamps with server defaults.
- String-backed enums (`native_enum=False`) for portable, readable rows.
- `NUMERIC(10,2)` for money and `Decimal` in Python.
- JSON columns for evolving payloads; relational columns for anything queried or constrained.
- SQLite (`aiosqlite`) only for hermetic unit tests.
- Migrations are reviewed, reversible, and run as a separate deployment step.

## Consequences

**Positive**

- Foreign keys, unique constraints, and check constraints protect the project aggregate.
- One transaction can cover project + specification + audit rows.
- JSON gives flexibility without abandoning relational integrity.
- Alembic provides an auditable schema history and CI drift detection.

**Negative**

- SQLite tests cannot catch every PostgreSQL behavior.
- Async SQLAlchemy adds ceremony and lazy-loading pitfalls.
- Native PostgreSQL enums were rejected, so enum validation lives in Python/check constraints.
- JSON fields can hide schema drift if overused.

**Mitigation**

- CI runs migrations up/down/up against PostgreSQL 16 and `alembic check`.
- Relationships needed by responses use `selectin` loading; sessions are request-scoped.
- Promote JSON fields to columns when query patterns stabilize.

## References

- [Database](../database.md)
- [CI workflow](../../.github/workflows/ci.yml)
