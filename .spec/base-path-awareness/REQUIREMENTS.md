# REQUIREMENTS.md — Base-Path Awareness

## Summary
The `proof-of-work` demo must support being served from a non-root URL path, such as:

- `/proof-of-work`

Today the app assumes it is mounted at `/`, which breaks UI asset loading and API calls when reverse-proxied under a subpath.

This feature adds configurable base-path awareness across:
- backend route mounting
- static asset URLs
- frontend API calls
- generated links and config values

## Functional requirements

### FR1 — Configurable base path
The application must support a configurable base path, for example:
- empty / root path: `""`
- subpath: `"/proof-of-work"`

The base path should be controlled by configuration, preferably environment-driven.

### FR2 — Root and subpath compatibility
The app must still work when served at root (`/`) and when served under a subpath.

Examples:
- local development root mode should continue working
- deployed subpath mode should work when proxied at `/proof-of-work`

### FR3 — Static asset correctness
All browser-loaded assets must resolve correctly under the configured base path.

Examples:
- stylesheet URL
- JavaScript URL
- any future favicon or static asset references

### FR4 — API call correctness
All frontend API calls must target base-path-prefixed endpoints when a base path is configured.

Examples under `/proof-of-work`:
- `/proof-of-work/v1/config`
- `/proof-of-work/v1/pow/challenges`
- `/proof-of-work/v1/random-numbers`

### FR5 — Mounted backend routes
Backend endpoints must be reachable under the configured base path.

If base path is `/proof-of-work`, these should work:
- `GET /proof-of-work/`
- `GET /proof-of-work/healthz`
- `GET /proof-of-work/v1/config`
- `POST /proof-of-work/v1/pow/challenges`
- `POST /proof-of-work/v1/random-numbers`
- `GET /proof-of-work/static/...`

### FR6 — Config visibility
The frontend should be able to discover or receive the effective base path so it can compose URLs safely.

This can be done by:
- embedding it in the HTML,
- exposing it in `/v1/config`,
- or both.

### FR7 — No behavior regression
Existing proof-of-work behavior must remain unchanged apart from path handling.

Specifically:
- challenge issuance still works
- proof submission still works
- session cookie flow still works
- UI still displays and solves challenges correctly

## Non-functional requirements

### NFR1 — Backward compatibility
Existing root-path local development should remain simple and unchanged by default.

### NFR2 — Minimal proxy assumptions
The app should not rely on brittle HTML rewriting by the proxy.
Path correctness should be handled by the app itself.

### NFR3 — Testability
Automated tests should verify both:
- root-path behavior
- subpath behavior

### NFR4 — Clear deployment instructions
README should document how to run the app with a base path and how to publish it behind Tailscale Serve/Funnel.

## Out of scope
- multi-tenant path routing inside one app
- arbitrary runtime path discovery without configuration
- path-based auth or routing logic beyond correct mounting

## Acceptance criteria
- app works under `/`
- app works under `/proof-of-work`
- UI assets load correctly in both modes
- frontend calls the correct base-path-prefixed API routes
- tests cover subpath behavior
- docs explain base-path deployment
