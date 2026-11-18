# ADR 0005: Provider-independent LLM boundary

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** Albayraq maintainers

## Context

The AI model landscape changes quickly. Different deployments may require OpenAI, Anthropic, Azure,
a local Ollama model, or an offline mock for tests. Domain code must not depend on a vendor SDK, and
the application must be testable without credentials or network access.

## Decision

Define a narrow async `LLMProvider` port:

- `default_model` — model identifier used when a request does not override it;
- `generate(LLMRequest) -> LLMResponse` — single completion with usage metadata;
- `health()` — optional readiness probe.

`LLMRequest` is provider-neutral: messages, model, temperature, token limit, optional response
schema, and metadata. `LLMResponse` includes content, provider, model, usage, and raw payload.

Provider selection is configuration (`AI_PROVIDER`), resolved through a factory registry. The
`mock` provider is the only implementation in the foundation release; it returns deterministic,
explicitly labelled placeholder content. Real adapters are added in M3, with vendor imports confined
to the provider module.

Agents depend on the port, not the provider. Model output is validated against typed contracts
before it enters shared context or the database.

## Consequences

**Positive**

- Tests run offline and deterministically.
- Switching providers is configuration, not a refactor.
- Token usage and latency can be normalized across providers.
- Vendor-specific retry/streaming behavior stays at the edge.

**Negative**

- The lowest-common-denominator request shape may hide provider-specific features.
- Structured output support varies; adapters must repair/retry consistently.
- An abstraction layer needs its own tests and documentation.

**Rules**

- No vendor SDK import outside a provider adapter.
- No secrets in prompts, logs, or committed files.
- Contract validation is mandatory even when a provider claims structured output.
- Provider/model identifiers are recorded on every agent run.

## References

- [AI agents](../ai-agents.md)
- [`app/ai/provider.py`](../../apps/api/app/ai/provider.py)
