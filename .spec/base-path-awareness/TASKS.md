# TASKS.md — Base-Path Awareness

## Phase 1 — Configuration
- [ ] Add `POW_BASE_PATH` setting
- [ ] Normalize and validate base-path input
- [ ] Expose effective base path to app components

## Phase 2 — Backend mounting
- [ ] Refactor app creation to support root mode and mounted subpath mode
- [ ] Ensure static files are reachable under the base path
- [ ] Ensure `GET /`, `GET /healthz`, `GET /v1/config`, and protected endpoints work under the base path

## Phase 3 — Frontend path handling
- [ ] Remove hardcoded root-relative asset assumptions
- [ ] Add frontend URL builder/helper for base-path-prefixed API calls
- [ ] Inject base path into the UI safely

## Phase 4 — Session/cookie review
- [ ] Decide and document cookie path behavior
- [ ] Verify session flow still works under subpath deployment

## Phase 5 — Tests
- [ ] Add root-mode regression coverage
- [ ] Add subpath-mode route coverage
- [ ] Add static asset coverage under subpath
- [ ] Add browser/API path correctness checks

## Phase 6 — Docs
- [ ] Update README with base-path deployment instructions
- [ ] Document example `/proof-of-work` hosting
- [ ] Document relevant Tailscale Serve/Funnel commands
