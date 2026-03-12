# Proof-of-Work Anti-Scraping Hardening — Tasks

## Phase 0 — Review and Decisions

- [ ] Approve the move from caller-supplied `clientId` to a server-issued session cookie.
- [ ] Approve the use of IP throttling for challenge issuance.
- [ ] Confirm trusted proxy / client-IP derivation rules.
- [ ] Confirm default limits for IP, session, and outstanding challenges.

## Phase 1 — Session Identity

- [ ] Add server-issued anonymous session model.
- [ ] Add session persistence store.
- [ ] Add cookie issuance and session lookup middleware/helpers.
- [ ] Remove manual `clientId` entry from the browser UI.
- [ ] Add session expiry handling.
- [ ] Add tests for first-contact session bootstrap.
- [ ] Create checkpoint commit after session flow is stable.

## Phase 2 — Challenge Issuance Hardening

- [ ] Add trusted client-IP resolution.
- [ ] Add per-IP challenge issuance limiter.
- [ ] Add per-session challenge issuance limiter.
- [ ] Add outstanding-challenge counter and cap.
- [ ] Add structured `429` responses for issuance rejections.
- [ ] Add tests for IP/session issuance throttling.
- [ ] Create checkpoint commit after issuance hardening.

## Phase 3 — Submission-Time Difficulty Enforcement

- [ ] Recompute current required tier on proof submission.
- [ ] Reject stale low-tier challenges with `STALE_CHALLENGE_DIFFICULTY`.
- [ ] Ensure challenge consumption remains atomic.
- [ ] Add tests proving stockpiled easy challenges are rejected once the tier rises.
- [ ] Create checkpoint commit after stale-challenge protection is verified.

## Phase 4 — Browser and API Contract Updates

- [ ] Update challenge endpoint contract to rely on cookie session identity.
- [ ] Update protected endpoint contract to rely on cookie session identity.
- [ ] Remove `clientId` from the browser request flow.
- [ ] Update browser status messaging for rate-limit and stale-challenge errors.
- [ ] Create checkpoint commit after browser flow is aligned.

## Phase 5 — Observability and Abuse Telemetry

- [ ] Record session issuance counts.
- [ ] Record challenge issuance counts per IP and per session.
- [ ] Record stale-challenge rejection counts.
- [ ] Record outstanding-challenge rejection counts.
- [ ] Add dashboards or logs for challenge pressure by IP and session.
- [ ] Create checkpoint commit after telemetry is available.

## Phase 6 — Documentation

- [ ] Update README with the hardened session/IP model.
- [ ] Document deployment assumptions around HTTPS and trusted proxies.
- [ ] Document default rate limits and tuning guidance.
- [ ] Document fairness trade-offs for NAT/shared-IP users.

## Phase 7 — Optional Extensions

- [ ] Add IP-prefix or ASN-based secondary throttles.
- [ ] Add user-agent consistency checks.
- [ ] Add CAPTCHA or interactive escalation for suspicious sessions.
- [ ] Add per-resource risk policy tuning.
