# Proof-of-Work Anti-Scraping Hardening — Tasks

## Phase 0 — Review and Decisions

- [x] Approve the move from caller-supplied `clientId` to a server-issued session cookie.
- [x] Approve the use of IP throttling for challenge issuance.
- [x] Confirm trusted proxy / client-IP derivation rules.
- [x] Confirm default limits for IP, session, and outstanding challenges.

## Phase 1 — Session Identity

- [x] Add server-issued anonymous session model.
- [x] Add session persistence store.
- [x] Add cookie issuance and session lookup middleware/helpers.
- [x] Remove manual `clientId` entry from the browser UI.
- [x] Add session expiry handling.
- [x] Add tests for first-contact session bootstrap.
- [x] Create checkpoint commit after session flow is stable.

## Phase 2 — Challenge Issuance Hardening

- [x] Add trusted client-IP resolution.
- [x] Add per-IP challenge issuance limiter.
- [x] Add per-session challenge issuance limiter.
- [x] Add outstanding-challenge counter and cap.
- [x] Add structured `429` responses for issuance rejections.
- [x] Add tests for IP/session issuance throttling.
- [x] Create checkpoint commit after issuance hardening.

## Phase 3 — Submission-Time Difficulty Enforcement

- [x] Recompute current required tier on proof submission.
- [x] Reject stale low-tier challenges with `STALE_CHALLENGE_DIFFICULTY`.
- [x] Ensure challenge consumption remains atomic.
- [x] Add tests proving stockpiled easy challenges are rejected once the tier rises.
- [x] Create checkpoint commit after stale-challenge protection is verified.

## Phase 4 — Browser and API Contract Updates

- [x] Update challenge endpoint contract to rely on cookie session identity.
- [x] Update protected endpoint contract to rely on cookie session identity.
- [x] Remove `clientId` from the browser request flow.
- [x] Update browser status messaging for rate-limit and stale-challenge errors.
- [x] Create checkpoint commit after browser flow is aligned.

## Phase 5 — Observability and Abuse Telemetry

- [x] Record session issuance counts.
- [x] Record challenge issuance counts per IP and per session.
- [x] Record stale-challenge rejection counts.
- [x] Record outstanding-challenge rejection counts.
- [x] Add dashboards or logs for challenge pressure by IP and session.
- [x] Create checkpoint commit after telemetry is available.

## Phase 6 — Documentation

- [x] Update README with the hardened session/IP model.
- [x] Document deployment assumptions around HTTPS and trusted proxies.
- [x] Document default rate limits and tuning guidance.
- [x] Document fairness trade-offs for NAT/shared-IP users.

## Phase 7 — Optional Extensions

- [ ] Add IP-prefix or ASN-based secondary throttles.
- [ ] Add user-agent consistency checks.
- [ ] Add CAPTCHA or interactive escalation for suspicious sessions.
- [ ] Add per-resource risk policy tuning.
