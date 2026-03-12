# Proof-of-Work API — Implementation Tasks

## Phase 0 — Spec Review

- [ ] Review `REQUIREMENTS.md` for agreement on caller identity, challenge TTL, and count limits.
- [ ] Review `DESIGN.md` for agreement on the sequential multi-stage hash puzzle.
- [ ] Resolve open questions before implementation starts.

## Phase 1 — Repository Setup

- [ ] Add project README summarizing scope after the spec is approved.
- [ ] Choose implementation language and runtime.
- [ ] Set up project structure under `/srv/projects/proof-of-work`.
- [ ] Initialize dependency management and test harness.
- [ ] Create checkpoint commit after scaffolding.

## Phase 2 — API Contract Implementation

- [ ] Implement `POST /v1/pow/challenges` contract.
- [ ] Implement `POST /v1/random-numbers` contract.
- [ ] Implement request canonicalization for proof binding.
- [ ] Define structured error payloads and status mapping.
- [ ] Create checkpoint commit after API contract layer is stable.

## Phase 3 — Difficulty and State Tracking

- [ ] Implement sliding 10-minute success window per `clientId`.
- [ ] Implement tier calculation: `floor(recentSuccesses / 10)`.
- [ ] Implement challenge persistence with expiration metadata.
- [ ] Implement atomic challenge consumption.
- [ ] Add tests for window-boundary edge cases.
- [ ] Create checkpoint commit after state tracking is verified.

## Phase 4 — PoW Engine

- [ ] Implement challenge seed generation with server randomness.
- [ ] Implement sequential stage definition from tier.
- [ ] Implement leading-zero-bit verification.
- [ ] Implement server-side proof validator.
- [ ] Add tests for malformed, invalid, expired, and replayed proofs.
- [ ] Create checkpoint commit after validator correctness is established.

## Phase 5 — Random Number Service

- [ ] Implement cryptographically secure random number generation.
- [ ] Enforce request count limits.
- [ ] Return response metadata (`tier`, `stages`, `challengeId`).
- [ ] Add tests confirming output shape and bounds.
- [ ] Create checkpoint commit after endpoint success path works end-to-end.

## Phase 6 — Reference Client

- [ ] Implement challenge retrieval client.
- [ ] Implement local PoW solver.
- [ ] Implement proof submission client.
- [ ] Implement one-shot retry on challenge expiration.
- [ ] Expose solve metrics (attempts, per-stage duration, total duration).
- [ ] Add integration tests against the API.
- [ ] Create checkpoint commit after client/server flow is working.

## Phase 7 — Observability and Hardening

- [ ] Add logging for challenge issuance and proof validation outcomes.
- [ ] Add metrics for per-tier solve and verification times.
- [ ] Load-test solve cost growth across tiers.
- [ ] Review abuse cases and replay resistance.
- [ ] Document operational configuration knobs.
- [ ] Create checkpoint commit after hardening.

## Phase 8 — Documentation and Demo

- [ ] Write README with usage flow and examples.
- [ ] Document the challenge/proof lifecycle.
- [ ] Document tuning guidance for base difficulty and tier increments.
- [ ] Prepare a simple demo script showing tier escalation over repeated calls.
- [ ] Tag the first implementation milestone.
