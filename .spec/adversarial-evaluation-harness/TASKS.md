# Adversarial Evaluation Harness — Tasks

## Phase 0 — Spec Review

- [ ] Review and approve the defensive scope: authorized evaluation only.
- [ ] Confirm allowed target configuration model.
- [ ] Confirm acceptable session input formats.
- [ ] Confirm initial scenarios to implement first.

## Phase 1 — Project Scaffolding

- [ ] Create a new Python project under `/srv/projects` if implemented separately.
- [ ] Set up virtual environment and dependency management.
- [ ] Create class-based project structure.
- [ ] Add checkpoint commit after scaffolding.

## Phase 2 — Core Config and Guardrails

- [ ] Implement target allowlist model.
- [ ] Implement operator acknowledgment flag for authorized testing.
- [ ] Implement max-request and max-duration safeguards.
- [ ] Add refusal behavior for non-approved targets.
- [ ] Add tests for guardrail enforcement.
- [ ] Add checkpoint commit after guardrails.

## Phase 3 — Session and Client Layer

- [ ] Implement session-file loader.
- [ ] Implement challenge API client.
- [ ] Implement protected endpoint client.
- [ ] Implement response/error classifier.
- [ ] Add tests for request/response classification.
- [ ] Add checkpoint commit after client layer.

## Phase 4 — Solver Layer

- [ ] Implement baseline single-threaded Python solver.
- [ ] Implement solver interface abstraction.
- [ ] Add optional multithreaded local solver strategy.
- [ ] Add tests against known challenge vectors.
- [ ] Add checkpoint commit after solver layer.

## Phase 5 — Scenario Engine

- [ ] Implement single-session baseline scenario.
- [ ] Implement single-session multithreaded fan-out scenario.
- [ ] Implement outstanding-challenge pressure scenario.
- [ ] Implement stale-challenge spend scenario.
- [ ] Implement expiry-edge scenario.
- [ ] Add tests for scenario stop conditions and metrics capture.
- [ ] Add checkpoint commit after scenario engine.

## Phase 6 — Metrics and Reporting

- [ ] Implement structured metrics collector.
- [ ] Implement JSON run report output.
- [ ] Implement markdown summary output.
- [ ] Add success/failure and throughput summaries.
- [ ] Add checkpoint commit after reporting.

## Phase 7 — Documentation

- [ ] Write README describing authorized use and guardrails.
- [ ] Document session input format.
- [ ] Document scenario definitions.
- [ ] Document how to interpret results.
- [ ] Document explicit non-goals: no credential theft, no unauthorized targeting.

## Phase 8 — Optional Extensions

- [ ] Add multi-session pool scenario.
- [ ] Add pacing strategies.
- [ ] Add richer value-per-request modeling.
- [ ] Add comparison mode between solver strategies.
- [ ] Add summary charts or lightweight visualization output.
