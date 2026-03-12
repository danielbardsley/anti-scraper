# Proof-of-Work Anti-Scraping Hardening — Design

## 1. Overview

This design hardens the original proof-of-work prototype for anti-scraping by replacing caller-chosen identity with a server-issued anonymous session and by adding IP-based challenge throttling.

The core model is:
- **session** is the primary identity key for PoW difficulty,
- **IP** is a secondary anti-abuse key for challenge issuance throttling,
- **submission-time tier validation** prevents spending old easy challenges after the session should face higher work.

## 2. Recommended Architecture

### 2.1 Identity Model
Use a server-issued opaque token stored in an HTTP cookie:

```text
Cookie: pow_session=<opaque-random-token>
```

Recommended properties:
- opaque random 128-bit or 256-bit token,
- server-side lookup rather than self-contained JWT for easier revocation and rate checks,
- `HttpOnly`,
- `SameSite=Lax`,
- `Secure` under HTTPS.

### 2.2 State Stores
Use a shared state backend such as Redis in production.

Recommended keys:
- `pow:session:<sessionId>` -> session metadata
- `pow:successes:<sessionId>` -> sorted timestamps of successful protected requests
- `pow:challenges:<challengeId>` -> challenge record
- `pow:outstanding:<sessionId>` -> set/count of outstanding challenge IDs
- `pow:rate:ip:<ip>` -> challenge issuance rate limiter state
- `pow:rate:session:<sessionId>` -> challenge issuance rate limiter state

## 3. Session Bootstrap Flow

### Option A — bootstrap during challenge issuance
1. Browser calls `POST /v1/pow/challenges` with no session cookie.
2. Server creates a session.
3. Server sets `pow_session` cookie.
4. Server continues to process the challenge request.

This is the simplest browser flow and is recommended for the demo.

### Option B — dedicated bootstrap endpoint
1. Browser calls `POST /v1/pow/session`.
2. Server sets cookie.
3. Browser calls `POST /v1/pow/challenges`.

This gives cleaner separation but adds an extra round trip.

## 4. Endpoint Surface

### 4.1 Issue Challenge

```text
POST /v1/pow/challenges
```

**Request**

```json
{
  "resource": "random-numbers",
  "count": 32
}
```

**Behavior**
1. Resolve client IP from trusted proxy context.
2. Create session cookie if absent.
3. Enforce per-IP challenge issuance rate limit.
4. Enforce per-session challenge issuance rate limit.
5. Enforce outstanding-challenge cap for the session.
6. Compute current session tier from successful requests in the sliding window.
7. Build and persist the challenge.
8. Return the challenge.

### 4.2 Submit Proof

```text
POST /v1/random-numbers
```

**Request**

```json
{
  "count": 32,
  "challengeId": "01JQ...",
  "proof": {
    "nonces": ["184920", "882113"]
  }
}
```

**Behavior**
1. Read session cookie.
2. Load challenge.
3. Verify challenge/session binding.
4. Recompute canonical request hash.
5. Recompute the currently required tier for the session.
6. Reject if the current tier exceeds the challenge tier.
7. Verify the proof.
8. Atomically consume the challenge.
9. Record the successful protected request for the session.
10. Return random numbers.

## 5. Identity and Abuse Keys

### 5.1 Primary key
The primary PoW identity is:

```text
sessionId
```

### 5.2 Secondary keys
The system may additionally track:

```text
ipAddress
ipPrefix
userAgentHash
```

These are supporting signals only. They must not replace the session as the main PoW difficulty key for browser fairness.

## 6. Session Model

Recommended session metadata:

```json
{
  "sessionId": "opaque-token",
  "createdAt": "2026-03-12T00:00:00Z",
  "lastSeenAt": "2026-03-12T00:05:00Z",
  "issuedByIp": "203.0.113.10",
  "userAgentHash": "optional-hash",
  "idleExpiresAt": "2026-03-13T00:05:00Z",
  "absoluteExpiresAt": "2026-03-19T00:00:00Z"
}
```

Recommended defaults:
- idle TTL: 24 hours,
- absolute TTL: 7 days.

## 7. Challenge Record Model

Each challenge record should store:
- `challengeId`
- `sessionId`
- `resource`
- `requestHash`
- `tier`
- `stageTargetBits`
- `seed`
- `issuedAt`
- `expiresAt`
- `issuedIp`
- `consumedAt`

`issuedIp` is mainly useful for telemetry and abuse analysis; hard IP binding at submission is optional and should be treated carefully because client IPs can change.

## 8. IP-Based Challenge Issuance Limits

Recommended default controls:
- challenges per IP per 10 minutes: **60**
- challenges per session per 10 minutes: **30**
- max outstanding challenges per session: **2**

These values are only defaults and must remain configurable.

The rate-limiting algorithm may be:
- sliding window,
- token bucket,
- leaky bucket.

For anti-scraping, a token bucket is usually a good operational choice, but a sliding window is easier to reason about in the spec.

## 9. Difficulty Calculation

Difficulty remains adaptive and based on successful protected requests in a sliding window.

```text
recentSuccesses = successful protected-endpoint calls for this session
                  where completedAt > now - successWindow

tier = floor(recentSuccesses / 10)
stageCount = tier + 1
```

The challenge stores the issued tier, but the submission path must also compute:

```text
currentRequiredTier = floor(currentRecentSuccesses / 10)
```

Validation rule:

```text
if challenge.tier < currentRequiredTier:
    reject as STALE_CHALLENGE_DIFFICULTY
```

This closes the easy-challenge stockpiling loophole.

## 10. Outstanding Challenge Control

When issuing a challenge, the server must count currently outstanding challenges for the session.

Outstanding means:
- issued,
- not expired,
- not consumed.

If the outstanding count is already at the configured cap, issuance is rejected with a structured error.

This reduces the ability to prefetch a large bank of future challenges.

## 11. Proof Validation Rules

A proof submission is valid only if:
- a valid session cookie is present,
- the challenge exists,
- the challenge belongs to that session,
- the challenge has not expired,
- the challenge has not been consumed,
- the request hash matches,
- the current required tier is not higher than the challenge tier,
- the proof nonces satisfy the challenge's stage requirements.

## 12. Browser Flow

Recommended browser flow:
1. Browser loads the page.
2. Browser calls `POST /v1/pow/challenges`.
3. Server sets `pow_session` cookie if missing.
4. Browser solves the challenge.
5. Browser submits proof to `POST /v1/random-numbers`.
6. Server validates using session cookie and returns data.

The browser should never ask the user to type a client ID.

## 13. Error Model

Suggested status codes and error codes:

- `401 SESSION_REQUIRED` — missing/invalid session
- `429 IP_CHALLENGE_RATE_LIMITED` — IP-based challenge issuance limit exceeded
- `429 SESSION_CHALLENGE_RATE_LIMITED` — session-based challenge issuance limit exceeded
- `429 TOO_MANY_OUTSTANDING_CHALLENGES` — session has too many unspent challenges
- `409 STALE_CHALLENGE_DIFFICULTY` — challenge tier is now too low
- `410 CHALLENGE_EXPIRED` — challenge expired
- `409 CHALLENGE_ALREADY_CONSUMED` — challenge already spent
- `401 SESSION_MISMATCH` — challenge/session mismatch
- `401 REQUEST_BINDING_MISMATCH` — proof is for a different request

## 14. Operational Notes

### 14.1 Reverse proxies
Only trust `X-Forwarded-For` or similar headers from known proxy hops.

### 14.2 HTTPS
Use HTTPS in production so the session cookie can be marked `Secure` and so browser security features behave normally.

### 14.3 False positives
Do not hard-bind successful proof submission to a single IP unless you have strong reasons; session continuity plus issuance throttling is usually safer for real users.

## 15. Recommended Next-Step Implementation Order

1. Add server-issued session cookie.
2. Remove user-entered `clientId` from the browser UI.
3. Add IP and session issuance rate limiters.
4. Add outstanding challenge cap.
5. Add submit-time stale-tier rejection.
6. Add tests for stockpiling and session rotation attacks.
