# Proof-of-Work API — Design

## 1. Overview

This design uses a two-step challenge/response flow:

1. The client requests a fresh PoW challenge.
2. The client solves the challenge locally.
3. The client submits the solved proof to the protected random-number endpoint.
4. The server verifies the proof cheaply and returns random numbers.

The key design choice is a **sequential multi-stage hash puzzle**:
- the number of stages grows with the caller's request tier,
- each stage requires brute-force nonce search,
- each stage depends on the digest from the previous stage,
- verification is cheap because the server only recomputes the declared stage digests once.

## 2. API Surface

### 2.1 Issue Challenge

**Endpoint**

```text
POST /v1/pow/challenges
```

**Request**

```json
{
  "clientId": "client-123",
  "resource": "random-numbers",
  "count": 32
}
```

**Response**

```json
{
  "challengeId": "01JQ...",
  "clientId": "client-123",
  "resource": "random-numbers",
  "requestHash": "9b7c...",
  "issuedAt": "2026-03-11T22:00:00Z",
  "expiresAt": "2026-03-11T22:01:30Z",
  "tier": 2,
  "algorithm": {
    "name": "sequential-leading-zero-hash",
    "hashFunction": "SHA-256",
    "stages": [
      { "index": 0, "targetBits": 22 },
      { "index": 1, "targetBits": 23 },
      { "index": 2, "targetBits": 24 }
    ]
  },
  "seed": "base64-encoded-random-seed"
}
```

### 2.2 Protected Random Number Endpoint

**Endpoint**

```text
POST /v1/random-numbers
```

**Request**

```json
{
  "clientId": "client-123",
  "count": 32,
  "challengeId": "01JQ...",
  "proof": {
    "nonces": ["184920", "882113", "17500112"],
    "solverStartedAt": "2026-03-11T22:00:02Z",
    "solverFinishedAt": "2026-03-11T22:00:06Z"
  }
}
```

**Successful Response**

```json
{
  "numbers": [372814, 99102, 441209, 708811],
  "meta": {
    "clientId": "client-123",
    "count": 4,
    "tier": 2,
    "stages": 3,
    "challengeId": "01JQ..."
  }
}
```

## 3. Tiering Rule

Let:

```text
recentSuccesses = number of successful /v1/random-numbers calls
                  for the same clientId
                  where completedAt > now - 10 minutes
```

Then:

```text
tier = floor(recentSuccesses / 10)
stageCount = tier + 1
baseTargetBits = 20 + tier
stageTargetBits[i] = baseTargetBits + i
```

Examples:
- 0-9 recent successes -> tier 0 -> 1 stage -> targets [20]
- 10-19 recent successes -> tier 1 -> 2 stages -> targets [21, 22]
- 20-29 recent successes -> tier 2 -> 3 stages -> targets [22, 23, 24]

This meets the requirement that the algorithm becomes more complicated every additional 10 successful requests in a rolling 10-minute window.

## 4. Puzzle Construction

### 4.1 Challenge Seed

The server constructs a challenge seed from:
- `challengeId`,
- `clientId`,
- `resource`,
- canonical hash of the intended request body,
- issuance timestamp,
- server-generated random bytes.

This prevents:
- offline precomputation,
- reuse across callers,
- reuse across endpoints,
- reuse across different `count` values.

### 4.2 Stage Computation

Define:

```text
seed0 = SHA-256(challengeId || clientId || resource || requestHash || issuedAt || serverNonce)
```

For each stage `i` from `0` to `stageCount - 1`:

```text
input_i  = (i == 0 ? seed0 : digest_(i-1)) || ":" || i || ":" || nonce_i
digest_i = SHA-256(input_i)
```

Stage `i` is valid if:

```text
leadingZeroBits(digest_i) >= stageTargetBits[i]
```

The proof is the ordered list of nonces:

```json
{
  "nonces": ["nonce0", "nonce1", "nonce2"]
}
```

## 5. Why This PoW Fits the Goal

### Hard to compute
The client must brute-force each stage until the hash output meets the target. As stages and target bits increase, expected work rises quickly.

### Easy to validate
The server only:
- rebuilds the challenge seed,
- recomputes one hash per submitted stage,
- checks each target threshold,
- checks expiration and single-use semantics.

This makes validation bounded and deterministic.

### Increasingly complicated
Higher tiers increase complexity in two ways:
- more sequential stages,
- stricter target bits per stage.

That is more than just "turning one knob"; it makes the proof structurally more involved.

## 6. Sliding Window Accounting

## 6.1 Logical Model
For each `clientId`, keep timestamps of successful protected-endpoint requests.

On challenge issuance:
1. trim entries older than 10 minutes,
2. count remaining entries,
3. compute `tier = floor(count / 10)`.

On successful proof validation and response generation:
1. atomically mark the challenge consumed,
2. append the success timestamp for that `clientId`.

## 6.2 Storage Options

### Proof-of-concept
- in-memory ordered deque per caller,
- in-memory challenge store keyed by `challengeId`.

### Production-friendly option
- Redis sorted set for request timestamps,
- Redis key/value or hash for challenge metadata,
- atomic consume/update via Lua script or transaction.

## 7. Challenge Lifecycle

Each challenge record should store:
- `challengeId`,
- `clientId`,
- `resource`,
- `requestHash`,
- `tier`,
- `stage targets`,
- `seed/serverNonce`,
- `issuedAt`,
- `expiresAt`,
- `consumedAt` (nullable).

Rules:
- a challenge may be used once,
- an expired challenge is invalid even if the proof is correct,
- a consumed challenge is invalid even if resubmitted identically,
- proof validation and consumption must happen atomically.

## 8. Request Canonicalization

To bind the proof to the actual request, the server must canonicalize the request body before hashing.

For this API, canonicalization can be simple because the body is small and fixed-shape:

```json
{
  "clientId": "client-123",
  "count": 32
}
```

Canonicalization rule for phase 1:
- include only fields that affect the protected operation,
- serialize them in deterministic key order,
- hash the canonical JSON string with SHA-256,
- include that `requestHash` in the challenge.

## 9. Error Model

Suggested status codes:
- `200 OK` — proof valid, numbers returned
- `400 Bad Request` — malformed proof or invalid count
- `401 Unauthorized` — caller mismatch or invalid proof identity binding
- `409 Conflict` — challenge already consumed
- `410 Gone` — challenge expired
- `428 Precondition Required` — challenge/proof missing

Suggested error payload:

```json
{
  "error": {
    "code": "CHALLENGE_EXPIRED",
    "message": "Challenge expired before proof submission.",
    "challengeId": "01JQ..."
  }
}
```

## 10. Reference Client Design

The reference client should have these responsibilities:
- build the canonical request body,
- request a challenge,
- solve stages in order,
- submit the proof,
- retry once on expiration by fetching a new challenge,
- surface metrics such as stage attempts and solve duration.

Recommended client modules:
- `ChallengeApiClient`
- `PowSolver`
- `PowSubmissionClient`
- `RequestCanonicalizer`
- `RetryPolicy`

## 11. Concurrency Considerations

- Multiple outstanding challenges for the same caller are allowed.
- Only successful protected-endpoint calls increase the tier.
- Since tier is calculated at challenge issuance time, two challenges issued close together may have the same tier.
- Challenge consumption must be atomic to prevent replay through racing submissions.

## 12. Random Number Generation

The protected endpoint returns integers generated from a cryptographically secure random source.

Phase-1 recommendation:
- 32-bit unsigned integers,
- configurable minimum/maximum count,
- default count = 10,
- maximum count kept intentionally modest for the PoC.

## 13. Open Questions

These should be settled before implementation starts:
- exact default `count` limit,
- exact challenge TTL,
- whether `clientId` is enough for phase 1 or should be combined with IP,
- whether to support a maximum tier safeguard,
- whether client solve telemetry is returned by the API or only logged locally.
