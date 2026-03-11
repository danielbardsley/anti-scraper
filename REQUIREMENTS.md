# Proof-of-Work API — Requirements

## 1. Objective

Design a small service and companion client that protect an API endpoint with an adaptive proof-of-work (PoW) scheme.

The protected endpoint must:
- require the caller to solve a PoW challenge before each successful request,
- increase challenge complexity every time the same caller crosses another block of 10 successful requests inside a sliding 10-minute window,
- validate proofs quickly on the server, and
- return a list of random numbers when the proof is valid.

This project is specification-only at this stage. No implementation code is in scope yet.

## 2. Scope

In scope:
- one protected API endpoint that returns random numbers,
- one challenge-issuance endpoint used by the client before calling the protected endpoint,
- one reference client workflow that requests challenges, solves them, and submits proofs,
- adaptive difficulty based on a per-caller sliding 10-minute window,
- request/response contracts, validation rules, and implementation tasks.

Out of scope for this phase:
- production deployment manifests,
- UI/dashboard work,
- authentication productization beyond a stable caller identifier,
- distributed quota billing,
- non-HTTP transports.

## 3. Definitions

- **Caller**: the identity used to track request frequency and assign difficulty. For the proof-of-concept, this is a required `clientId`.
- **Protected endpoint**: the API route that returns random numbers only after successful PoW validation.
- **Challenge**: a short-lived, server-issued description of the work the caller must solve.
- **Proof**: the caller-computed response containing one or more nonces that satisfy the challenge.
- **Tier**: the difficulty level derived from the caller's recent request count.
- **Sliding window**: the rolling 10-minute interval used to count successful requests per caller.

## 4. Functional Requirements

### FR-1. Protected Random Number Endpoint
The system must expose a protected HTTP endpoint that returns a list of random numbers after successful proof validation.

The endpoint must:
- accept a caller identifier,
- accept a PoW proof bound to the request,
- accept a requested result size within configured limits,
- return HTTP 200 on success, and
- return a JSON payload containing a `numbers` array.

### FR-2. Challenge Issuance Endpoint
The system must expose a challenge endpoint that issues a fresh PoW challenge for the protected endpoint.

The challenge must include at minimum:
- a unique challenge identifier,
- the caller identity the challenge is bound to,
- the target protected resource,
- the computed difficulty tier,
- the algorithm description for the current tier,
- the challenge seed/input,
- an issuance timestamp, and
- an expiration timestamp.

### FR-3. Stable Caller Identity
Difficulty must be computed per caller, not globally.

For this phase:
- the client must send a stable `clientId`,
- the server must treat `clientId` as required input,
- challenges must be bound to that exact `clientId`, and
- proofs submitted under a different `clientId` must be rejected.

### FR-4. Sliding 10-Minute Difficulty Rule
The server must compute difficulty using a sliding 10-minute window of successful requests for the same caller.

The tier must be calculated as:

```text
tier = floor(successfulRequestsInPrevious10Minutes / 10)
```

Implications:
- requests 1-10 in the rolling window use tier 0,
- requests 11-20 use tier 1,
- requests 21-30 use tier 2,
- and so on.

For clarity, `successfulRequestsInPrevious10Minutes` means successful protected-endpoint calls completed before the current challenge is issued.

Challenge fetches do not count toward the tier.

### FR-5. Increasingly Complicated PoW Algorithm
The proof-of-work algorithm must become more complicated as the tier increases.

The required behavior is:
- tier 0 uses one proof stage,
- each additional tier adds at least one additional sequential proof stage,
- each stage must require brute-force search over a nonce space,
- each stage must be easy for the server to verify with a small, deterministic amount of work,
- each stage must depend on the previous stage output so the overall proof cannot be fully parallelized,
- the algorithm must use cryptographic hash functions, and
- the difficulty schedule must be configurable without changing the API contract.

### FR-6. Proof Hardness vs Validation Cost
The proof must be substantially more expensive to compute than to validate.

Therefore:
- the client should perform repeated hashing and nonce search,
- the server should validate by recomputing a bounded number of hashes,
- validation must not require brute-force search,
- validation must be deterministic, and
- the server must reject proofs that are malformed, incomplete, expired, or replayed.

### FR-7. Replay Resistance and Expiration
Challenges must be short-lived and single-use.

The system must:
- expire challenges after a configurable TTL,
- reject expired challenges,
- reject already-consumed challenges,
- bind the challenge to the protected resource and request parameters, and
- prevent precomputation by including server-generated unpredictable input in the challenge.

### FR-8. Request Binding
A proof must only be valid for the exact intended request.

At minimum, the challenge/proof pair must be bound to:
- `clientId`,
- the protected endpoint identity,
- the requested random number count, and
- the unique challenge identifier.

A proof generated for one request shape must not be reusable for another request shape.

### FR-9. Random Number Output
On success, the protected endpoint must return random numbers generated by a cryptographically secure random source.

The response must:
- include a `numbers` array,
- allow the caller to request a count within configured bounds,
- document the numeric type and range, and
- include response metadata describing the tier or proof details used for that request.

### FR-10. Reference Client Behavior
A reference client must be specified.

The client must:
- request a challenge,
- solve the challenge locally,
- submit the proof to the protected endpoint,
- handle challenge expiration by refreshing the challenge and retrying once,
- surface timing/attempt metrics useful for testing, and
- support configurable concurrency while preserving per-request correctness.

### FR-11. Error Handling
The specification must define structured error responses.

At minimum, the system must distinguish:
- missing proof/challenge,
- malformed proof,
- invalid proof,
- expired challenge,
- replayed challenge,
- caller mismatch,
- request-binding mismatch, and
- invalid random-number count.

### FR-12. Observability
The system must expose enough information to evaluate the behavior of the adaptive PoW mechanism.

At minimum, the implementation must be able to record:
- challenge issuance count,
- protected-endpoint success/failure count,
- proof verification failures by reason,
- per-tier solve time observed by clients,
- per-tier verification time observed by server, and
- sliding-window counts per caller for debugging.

## 5. Non-Functional Requirements

### NFR-1. Performance
- Server-side proof verification should remain cheap relative to client solve cost.
- Verification cost should grow linearly with tier, not exponentially.
- Challenge issuance should be lightweight and not require solving work on the server.

### NFR-2. Security
- The challenge seed must contain high-entropy server-generated randomness.
- Challenge identifiers must be unique.
- Proofs must be single-use.
- The algorithm must avoid trivial shortcuts and obvious replay paths.

### NFR-3. Configurability
The following must be configurable:
- challenge TTL,
- random number count limits,
- base difficulty,
- per-tier difficulty increments,
- hash algorithm selection if future variants are added, and
- storage strategy for sliding-window accounting and challenge tracking.

### NFR-4. Deterministic Validation
Given a challenge, request, and proof, all compliant servers must produce the same validation result.

### NFR-5. Testability
The design must support:
- unit tests for tier calculation,
- unit tests for proof validation,
- replay/expiration tests,
- sliding-window edge-case tests, and
- load tests showing rising client solve cost as request rate increases.

## 6. Assumptions

- The proof-of-concept may use `clientId` instead of full authentication.
- The same caller may make concurrent requests, so challenge consumption must be atomic.
- Time comparisons use server time only.
- Only successful protected-endpoint calls increase the sliding-window count.

## 7. Acceptance Criteria

The specification is acceptable when it clearly defines:
1. the endpoints and their contracts,
2. how tiering works in a sliding 10-minute window,
3. how the proof gets more complicated every additional 10 successful requests,
4. how the proof remains easy to validate,
5. how replay and expiration are handled,
6. what the client must do, and
7. what tasks are required for implementation.
