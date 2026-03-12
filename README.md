# Proof-of-Work Demo

Adaptive proof-of-work protected random-number API.

## Stack

- Backend: Python + FastAPI
- Frontend: Vanilla JavaScript + HTML/CSS
- PoW algorithm: sequential SHA-256 leading-zero-bit puzzle
- Identity model: server-issued anonymous session cookie
- Anti-abuse model: per-session difficulty + per-IP/per-session challenge throttling

## Endpoints

- `GET /` — web UI
- `GET /healthz` — health check
- `GET /v1/config` — demo config for the UI
- `GET /v1/telemetry` — in-memory telemetry counters for the demo
- `POST /v1/pow/challenges` — issue a challenge and bootstrap session cookie if needed
- `POST /v1/random-numbers` — submit proof and receive random numbers

## Hardening behavior

- The browser does **not** provide its own identity.
- The server issues a `pow_session` cookie and tracks PoW difficulty by that session.
- Challenge issuance is rate-limited by IP and by session.
- A session can hold only a limited number of outstanding challenges.
- On proof submission, the server recomputes the current required tier and rejects stale lower-tier challenges.
- IP is treated as a secondary anti-abuse signal rather than the main identity anchor.

## Deployment notes

- In production, run behind HTTPS so the session cookie can be marked `Secure`.
- If deployed behind a reverse proxy, configure trusted proxy IPs before honoring forwarded client-IP headers.
- Shared/NAT'd users may hit IP issuance limits sooner than single-user IPs, so keep those thresholds configurable.

## Local run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
uvicorn proof_of_work_api.main:create_app --factory --host 0.0.0.0 --port 8017
```

## Notes

- The browser demo uses a configurable base difficulty that is intentionally moderate by default so the UI remains responsive.
- Difficulty still increases every 10 successful requests within the rolling 10-minute window.
