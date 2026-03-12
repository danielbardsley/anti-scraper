# Proof-of-Work Anti-Scraping Hardening — Requirements

## 1. Objective

Define a hardened proof-of-work design for anti-scraping use cases where:
- the server issues the caller identity,
- challenge issuance is rate-limited by IP address,
- proof difficulty is tracked against a server-issued session rather than a caller-supplied identifier,
- previously issued low-difficulty challenges cannot be stockpiled and spent later when the caller should face a higher tier.

This specification supersedes the trust model of the original proof-of-concept for anti-scraping deployments.

## 2. Scope

In scope:
- server-issued anonymous session identity,
- IP-based challenge issuance limits,
- per-session difficulty tracking,
- outstanding challenge limits,
- challenge submission-time tier re-evaluation,
- challenge/proof binding to the session and request,
- requirements, design constraints, and implementation tasks.

Out of scope:
- full account/login systems,
- device fingerprinting beyond optional supporting signals,
- CAPTCHA vendor integration,
- WAF vendor-specific configuration.

## 3. Definitions

- **Session**: a server-issued anonymous identity represented by an opaque cookie-backed token.
- **Primary identity key**: the server-issued session identifier used for PoW difficulty tracking.
- **IP rate key**: the client IP address or trusted proxy-derived client IP used for challenge issuance throttling.
- **Outstanding challenge**: an issued challenge that has not yet expired and has not yet been consumed.
- **Stale challenge**: a challenge whose recorded difficulty tier is lower than the caller's currently required tier at submission time.

## 4. Functional Requirements

### FR-1. Server-Issued Session Identity
The system must not rely on a caller-supplied `clientId` as the primary identity for difficulty tracking.

Instead:
- the server must issue an opaque session token,
- the token must be returned as an HTTP cookie,
- the protected workflow must use that session token as the primary identity anchor,
- the client must not be allowed to choose or override the session identifier.

### FR-2. Session Cookie Requirements
The session cookie must:
- be `HttpOnly`,
- be `SameSite=Lax` by default,
- be `Secure` when served over HTTPS,
- have configurable idle and absolute expiration,
- be rotated or replaced only by server policy.

### FR-3. Session Bootstrap
The system must support first-contact bootstrap for anonymous browser clients.

At minimum, one of these must be supported:
- issue the session cookie on the first challenge request if absent, or
- expose a dedicated session-bootstrap endpoint.

The browser demo should not require manual client identity entry.

### FR-4. Challenge Issuance Rate Limits by IP
Challenge issuance must be rate-limited by IP address.

The implementation must support configurable limits for:
- challenges per IP per sliding window,
- challenges per session per sliding window,
- optional bursts via token bucket or similar mechanism.

Rate limits must be enforced before challenge creation.

### FR-5. Trusted Client IP Resolution
If the service runs behind a proxy/load balancer, the implementation must resolve client IPs only from trusted proxy headers.

The system must:
- define a trusted proxy policy,
- ignore untrusted forwarded IP headers,
- document how client IP is derived.

### FR-6. Difficulty Tracking by Session
PoW difficulty must be tracked primarily by server-issued session identity.

The tier must be based on successful protected-endpoint requests within the configured sliding success window for that session.

### FR-7. Optional Secondary Abuse Signals
The design must allow optional secondary abuse inputs, such as:
- IP address,
- IP prefix,
- user-agent hash,
- ASN/datacenter classification.

These signals may influence challenge issuance limits or risk scoring, but the core PoW difficulty key remains the session.

### FR-8. Outstanding Challenge Limits
The server must cap the number of outstanding challenges per session.

The cap must be configurable and enforced during challenge issuance.

If the cap is exceeded, the server must reject new challenge issuance until one of the following happens:
- a challenge is consumed,
- a challenge expires,
- the server explicitly revokes or clears stale outstanding challenges.

### FR-9. Submission-Time Tier Re-Evaluation
The system must recompute the caller's currently required difficulty tier when a proof is submitted.

The server must reject the submission if:
- the current required tier is higher than the challenge's issued tier, or
- the challenge's stage targets are weaker than the currently required policy.

This is required to prevent stockpiling low-tier challenges for later use.

### FR-10. Challenge Binding
A challenge must be bound to:
- the server-issued session,
- the protected resource,
- the canonical request body,
- the challenge identifier,
- the challenge seed,
- the issue time and expiration time.

A proof must not validate outside that exact binding.

### FR-11. Single-Use and Expiration
Each challenge must remain single-use and short-lived.

The system must:
- reject expired challenges,
- reject consumed challenges,
- consume challenges atomically,
- ensure only one successful submission can spend a given challenge.

### FR-12. Protected Endpoint Limits
The protected endpoint must continue to enforce PoW validation before returning random numbers.

The hardened version must additionally support:
- per-session success counting,
- optional per-IP endpoint-level throttling,
- structured rejection of stale-low-tier challenges.

### FR-13. Browser Compatibility
The browser-facing design must work for normal users without requiring manual identity management.

The session and challenge flow must work in browsers that support cookies and JavaScript.

### FR-14. Error Handling
The spec must define structured errors for at least:
- missing or invalid session,
- challenge issuance rate-limited by IP,
- challenge issuance rate-limited by session,
- too many outstanding challenges,
- stale challenge difficulty,
- expired challenge,
- consumed challenge,
- proof/session mismatch,
- request-binding mismatch.

### FR-15. Observability
The implementation must be able to record:
- session issuance count,
- challenge issuance count by IP and session,
- challenge rejections by reason,
- stale-challenge rejection count,
- proof verification failures,
- per-tier success counts,
- per-IP challenge pressure.

## 5. Non-Functional Requirements

### NFR-1. Anti-Abuse Posture
The design should materially raise the cost of scraping for:
- single-IP bots,
- low-effort browser automation,
- simple identity rotation attacks.

It is not required to fully defeat distributed proxy-based scraping by itself.

### NFR-2. Fairness
The design should reduce false positives for legitimate users behind shared IPs by:
- using session as the primary PoW identity,
- using IP mainly for issuance throttling,
- keeping all IP-based thresholds configurable.

### NFR-3. Configurability
At minimum, the following must be configurable:
- session idle TTL,
- session absolute TTL,
- challenge TTL,
- per-IP issuance limits,
- per-session issuance limits,
- max outstanding challenges per session,
- success-window duration,
- per-tier PoW policy.

### NFR-4. Production Compatibility
The design must be compatible with distributed state backends such as Redis for:
- session lookup,
- rate limiting,
- outstanding challenge tracking,
- challenge consumption.

## 6. Acceptance Criteria

The spec is acceptable when it clearly defines:
1. how the server issues and owns the primary identity,
2. how IP-based challenge throttling works,
3. how per-session difficulty is tracked,
4. how outstanding challenge stockpiling is prevented,
5. how stale low-tier challenges are rejected at submission time,
6. how the browser flow works without user-entered client IDs.
