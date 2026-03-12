# Anti-Scraper Proof-of-Work Demo

A demonstration service that adds adaptive proof-of-work friction to a protected endpoint.

This project is aimed at one specific abuse pattern:

- a scraper obtains a real browser-backed session or token,
- then pivots to a direct API client,
- and uses that stolen session state to hammer valuable endpoints cheaply.

The goal is **not** to make scraping impossible.
The goal is to make scraping **more expensive, lower-throughput, and more annoying to operationalize**.

## What this demo does

The demo exposes a protected endpoint that returns random numbers.
Before each successful call, the client must solve a server-issued proof-of-work challenge.

Difficulty increases based on recent successful requests within a sliding time window.
That means a session that keeps making successful requests must keep paying rising computational cost.

## What problem this is trying to solve

This design is intended to reduce the value of:
- one-time browser bootstrap followed by cheap API abuse,
- replaying a stolen WAF/browser token from a direct client,
- sustained use of a single valid session at high request rates,
- stockpiling easy challenges and spending them later.

In other words:

**without PoW**
- get a real session once,
- replay it from a script,
- scrape cheaply at scale.

**with PoW**
- get a real session once,
- still possible to use it,
- but every successful request requires fresh work,
- and the work gets more expensive as usage rises.

That shift is the core value of the design.

## Current implementation status

This repository contains a working demo implementation with:
- Python FastAPI backend
- browser-based JavaScript frontend
- adaptive sequential SHA-256 proof-of-work
- server-issued anonymous session cookie
- per-session difficulty tracking
- per-IP and per-session challenge issuance throttling
- outstanding challenge cap
- stale low-tier challenge rejection on submission
- replay protection for spent challenges
- in-memory telemetry counters for demo inspection

This is **demo-grade**, not production-grade distributed infrastructure.

## High-level design

### Protected resource
The protected endpoint is:

- `POST /v1/random-numbers`

It returns a JSON array of random numbers if proof validation succeeds.

### Challenge issuance
Challenges are issued via:

- `POST /v1/pow/challenges`

The server returns:
- a unique challenge ID,
- a seed,
- the current tier,
- stage definitions for the proof,
- expiry metadata.

### Browser/session identity
The browser does **not** choose its own identity.
The server issues an anonymous session cookie:

- `pow_session`

That session is the primary identity used for difficulty tracking.

### Proof algorithm
The proof is a sequential multi-stage SHA-256 puzzle.
For each stage, the client must find a nonce such that the resulting digest has at least a configured number of leading zero bits.

Each stage depends on the previous stage digest, so the work is not trivially parallelizable stage-to-stage.

### Adaptive difficulty
Difficulty is based on successful requests in a sliding 10-minute window.

Default rule:

```text
tier = floor(successful_requests_in_last_10_minutes / 10)
```

Implications:
- 0–9 recent successes => tier 0
- 10–19 => tier 1
- 20–29 => tier 2
- etc.

Each tier increases complexity by:
- adding another sequential stage,
- increasing stage target bits.

## Protections currently in place

## 1. Server-issued session identity

### What it does
The browser gets a server-issued opaque session cookie.
The client does not provide the primary identity key.

### Why it matters
This blocks the simplest bypass where a scraper just invents a new `clientId` every request to reset difficulty.

### What it mitigates
- naive client-ID rotation
- free reset of session-local difficulty by changing a request field

### What it does not solve
It does **not** stop a determined actor from obtaining many real sessions over time.
It only ensures identity is owned by the server, not claimed by the client.

## 2. Per-session adaptive proof-of-work

### What it does
Each successful request requires a fresh proof tied to a specific challenge and request body.
Difficulty rises with successful request volume for the same session.

### Why it matters
A stolen real session is no longer enough by itself.
Continued scraping requires continued computation.

### What it mitigates
- cheap repeated use of one valid session
- low-cost direct API replay after browser bootstrap
- high-volume hammering through a single active session

### What it does not solve
It does not prevent a scraper from:
- writing a faster solver,
- distributing solve work across machines,
- running many sessions in parallel,
- paying the cost if the scraped data is valuable enough.

## 3. Request binding

### What it does
Challenges are bound to the request shape through a canonical request hash.
In this demo, that means a challenge for one `count` value is not valid for a different `count` value.

### Why it matters
It prevents solving a proof once and reusing it across multiple request variants.

### What it mitigates
- replay of proofs across different request parameters
- some forms of challenge reuse

### What it does not solve
If the request shape is too simple, the protection surface is correspondingly narrow.
A real system should bind whatever parameters make the protected resource valuable.

## 4. Single-use challenges

### What it does
Each challenge can only be spent once.
After successful submission, it is marked consumed.

### Why it matters
This prevents straightforward replay of a solved challenge.

### What it mitigates
- double-spend of the same solved proof
- naive replay after success

### What it does not solve
It does not prevent scrapers from solving fresh challenges repeatedly.

## 5. Challenge expiry

### What it does
Challenges expire quickly.

### Why it matters
This limits the usable lifetime of issued work and reduces the value of hoarding large challenge inventories.

### What it mitigates
- long-lived reuse of solved or unsolved challenges
- some forms of delayed replay

### What it does not solve
It does not stop a scraper from solving and submitting within the validity window.

## 6. Outstanding challenge cap

### What it does
Each session can only hold a limited number of live, unspent challenges at once.

Default:
- max outstanding challenges per session = 2

### Why it matters
This reduces the ability to prefetch a large bank of challenge material for later use.

### What it mitigates
- challenge stockpiling
- challenge prefetch pipelines inside one session

### What it does not solve
A determined actor can still run many sessions in parallel.

## 7. Stale low-tier challenge rejection

### What it does
The server recomputes the currently required tier when a proof is submitted.
If the challenge was issued at a lower tier than is currently required, the proof is rejected.

### Why it matters
This closes the important loophole where a scraper collects easy challenges early and spends them later after the session has become “hot”.

### What it mitigates
- low-tier challenge stockpiling
- delayed spend of older cheaper work

### What it does not solve
It does not stop a scraper from continuously solving at the current tier.

## 8. Per-IP challenge issuance throttling

### What it does
Challenge issuance is limited per source IP over a sliding window.

### Why it matters
This makes rapid creation of lots of challenge requests from one IP more expensive and more visible.

### What it mitigates
- single-IP challenge flooding
- some session-churn attacks from one network origin

### What it does not solve
It does not stop:
- proxy rotation,
- botnets,
- distributed issuance from many IPs,
- abuse hidden behind large residential proxy pools.

## 9. Per-session challenge issuance throttling

### What it does
Challenge issuance is also limited per session.

### Why it matters
This stops one session from minting challenges too quickly even if IP limits are permissive.

### What it mitigates
- per-session over-issuance
- tight challenge-fetch loops

### What it does not solve
It does not stop actors from spreading abuse over many sessions.

## 10. Trusted proxy-aware IP resolution

### What it does
The application only trusts forwarded client-IP headers from configured trusted proxies.
If the immediate peer is not trusted, the forwarded header is ignored.

### Why it matters
Without this, a direct client could spoof `X-Forwarded-For` and defeat IP-based controls.

### What it mitigates
- header spoofing for IP-based issuance controls

### What it does not solve
If reverse proxy trust is misconfigured in deployment, IP controls may still be ineffective or too aggressive.

## 11. Telemetry counters

### What it does
The demo exposes in-memory counters at:

- `GET /v1/telemetry`

These track basic issuance, error, and success counts.

### Why it matters
This helps evaluate whether the protections are activating and whether the system behaves as expected under test.

### What it does not solve
This is observability for a demo, not production monitoring.
It is not durable, not access-controlled, and not suitable as-is for real environments.

## Threat model fit

This design is a good fit for:
- direct API abuse after real browser bootstrap
- scraping where the attacker currently gets cheap value from a stolen session or token
- attackers who care about cost and throughput
- situations where adding friction is good enough

This design is a poor fit if you expect it to:
- completely stop scraping,
- survive high-scale distributed abuse without additional layers,
- replace account-based abuse controls,
- replace WAFs, behavioral detection, or rate limiting.

## What determined engineers or scrapers will try

Expect them to try at least the following:

### Direct API use
They will skip the UI and call the challenge and submit endpoints directly.
That is expected.
This design still helps because the cost is enforced server-side, not UI-side.

### Faster solvers
They will replace the browser solver with:
- native code,
- multithreaded workers,
- optimized hash implementations,
- distributed solve pools.

This does not defeat the design; it changes the cost curve.

### Session fan-out
They will attempt to reuse a single valid session across many workers.
The per-session rising difficulty still helps, but throughput may remain useful depending on hardware and economics.

### Session churn
They will try to acquire many sessions and rotate between them.
This is a real limitation of any per-session design.

### Proxy rotation
They will rotate IPs to reduce issuance throttling pain.
This is expected.

### Race conditions
They will attempt:
- double-spend races,
- challenge fetch bursts,
- tier-boundary timing games,
- expiry-edge submissions.

### Automation with real browsers
They may use Playwright/Puppeteer or real browser pools to maintain more legitimate-looking behavior.

## Known limitations

## 1. This is not a complete anti-scraping solution
It is one layer of friction.
A motivated, well-funded scraper can still succeed.

## 2. In-memory state only
Current state is local-process memory only.
That means:
- no cross-process coordination,
- no cross-instance consistency,
- restart resets state,
- horizontally scaled deployments would not behave correctly without shared storage.

## 3. No production-grade distributed locking/state
For production, sessions, challenge issuance state, rate limits, outstanding counts, and challenge consumption would need a shared backend such as Redis.

## 4. No authentication/account binding
This demo uses anonymous server-issued sessions.
That is useful for browser workflows but weaker than authenticated user or API-key identity when you have one.

## 5. IP controls can block legitimate users
IP-based controls are noisy.
They can unfairly affect:
- mobile carriers,
- office NATs,
- schools,
- VPN exit nodes,
- CGNAT users.

## 6. Browser fairness vs attacker efficiency gap
The browser demo intentionally uses a moderate difficulty so normal users can still complete work.
A custom native client may solve faster than the browser.
That is a real asymmetry.

## 7. Telemetry endpoint is open in the demo
That is convenient for testing but would likely need restriction, removal, or aggregation in production.

## 8. Cookie/session resets remain possible
A session cookie is better than caller-supplied identity, but still not the same thing as a durable account identity.

## Potential false positives / legitimate traffic risks

These are the most important ways this design could block traffic you actually want to allow.

### Shared IP pressure
Multiple real users behind one IP may hit issuance throttles faster than expected.

### Long-running legitimate automation
If you have legitimate integrations or internal tooling behaving like a scraper, they may be slowed or blocked.

### Accessibility/performance issues
Users on low-power devices may struggle more with PoW than users on fast machines.
That can create an unfair UX penalty.

### Mobile/browser instability
Session resets, cookie clearing, browser privacy modes, or aggressive tab lifecycle changes may create extra friction for real users.

### Human users making many legitimate requests
If the protected action is normal user behavior, adaptive difficulty may become a UX tax.
That means the protected endpoint must be chosen carefully.

## Potential operational issues

### Proxy trust mistakes
If trusted proxy configuration is wrong, IP controls may be bypassed or may misclassify real clients.

### State reset on deploy/restart
In-memory state means active difficulty and rate-limiter state disappear on restart.

### Multi-instance inconsistency
Two app instances would not agree on sessions/challenges/rate limits unless moved to shared storage.

### Cost tuning mistakes
If difficulty is too low, scrapers ignore it.
If difficulty is too high, you punish legitimate traffic.
Tuning matters.

## Why this may still be worth implementing in production

Because it directly attacks the economics of one common abuse pattern:

- real browser session obtained once,
- direct API client does the rest cheaply.

This design makes “the rest cheaply” much less true.
That alone may be enough to:
- reduce scraping throughput,
- reduce ROI for attackers,
- force scrapers into more expensive infrastructure,
- make abuse easier to detect because it becomes more structured and costly.

For many businesses, that is already a meaningful win.

## What a production version would likely add

A more serious implementation would typically include:
- Redis-backed session/challenge/rate-limit state
- stronger telemetry and dashboards
- protected/internal observability endpoints
- account or API-key binding where possible
- risk-based tuning by endpoint value
- better behavioral detection around browser-to-API pivots
- optional escalation to CAPTCHA or stronger checks
- better concurrency testing and adversarial load testing

## API summary

### `GET /`
Browser demo UI.

### `GET /healthz`
Basic liveness/status.

### `GET /v1/config`
Frontend/demo config.

### `GET /v1/telemetry`
Demo in-memory counters.

### `POST /v1/pow/challenges`
Issue a challenge and bootstrap a session cookie if needed.

Request:

```json
{
  "resource": "random-numbers",
  "count": 10
}
```

### `POST /v1/random-numbers`
Submit a proof for the current session and receive random numbers.

Request:

```json
{
  "count": 10,
  "challengeId": "...",
  "proof": {
    "nonces": ["123", "456"]
  }
}
```

## Local development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
uvicorn proof_of_work_api.main:create_app --factory --host 0.0.0.0 --port 8017
```

## Testing

```bash
. .venv/bin/activate
pytest -q
```

## Current test coverage themes

The test suite currently covers:
- session bootstrap
- request success flow
- replay rejection
- request-binding mismatch
- session-required handling
- session challenge rate limiting
- IP challenge rate limiting
- outstanding challenge cap
- stale low-tier challenge rejection
- expiry rejection
- trusted-proxy handling
- telemetry visibility
- expired challenge cleanup behavior

## Bottom line

This repo should be understood as a **friction layer demo**.
It is useful if your goal is to make scraping harder, slower, and more expensive.
It is not a silver bullet, and it should not be presented as one.

That said, for the specific pattern of **real session acquired once, then abused by direct API clients**, it is a reasonable and testable direction.
