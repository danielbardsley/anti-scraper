# Adversarial Evaluation Harness — Requirements

## 1. Objective

Design a Python-based internal evaluation harness that simulates the target abuse pattern against systems you control in order to measure how effective the anti-scraping protections are.

The harness must evaluate this threat model:
- a scraper obtains a real browser-backed session or token,
- then pivots to a direct API client,
- and uses that stolen session state to hammer valuable endpoints cheaply.

The harness is intended to test whether the current protections:
- raise per-request cost,
- reduce throughput,
- degrade sustained abuse within one session,
- remain effective under direct API use and multithreaded pressure,
- fail safely and observably under adversarial-but-authorized testing.

This specification is for defensive evaluation only. It must not be designed as a general-purpose bypass tool for third-party systems.

## 2. Scope

In scope:
- single-host Python harness,
- optional multithreaded execution,
- authenticated/authorized testing only against explicitly allowed targets,
- session reuse tests,
- direct API challenge/solve/submit workflows,
- configurable solver strategies,
- concurrency and throughput experiments,
- metrics, reports, and failure analysis.

Out of scope:
- credential theft,
- browser token theft tooling,
- target discovery,
- third-party exploitation features,
- stealth/obfuscation designed to evade unrelated monitoring,
- distributed botnet or proxy-network orchestration.

## 3. Definitions

- **Harness**: the Python tool that performs controlled adversarial testing.
- **Target**: the system under test, which must be explicitly authorized and configured by the operator.
- **Session seed**: a real, already-authorized session/cookie/token provided by the operator or obtained through an approved bootstrap flow.
- **Scenario**: a repeatable abuse simulation such as direct API replay pressure, session fan-out, or challenge concurrency tests.
- **Run**: one execution of a scenario with a concrete configuration.
- **Solver strategy**: the implementation used to compute proof-of-work, such as single-threaded Python or worker-thread pools.

## 4. Functional Requirements

### FR-1. Explicit Authorized Target Configuration
The harness must require explicit operator configuration of the target.

At minimum:
- the operator must provide the base URL,
- the operator must provide or approve the protected endpoint definitions,
- the harness must refuse to run without a target allowlist match,
- the harness must make it difficult to accidentally point at arbitrary hosts.

### FR-2. Single-Host Operation
The harness must run on a single host.

It may use:
- one process,
- multiple local threads,
- optional local worker pools.

It must not require distributed infrastructure.

### FR-3. Direct API Client Workflow
The harness must simulate a direct API client that:
- reuses an authorized session,
- requests PoW challenges directly,
- solves challenges outside the browser,
- submits proofs directly to the protected endpoint.

### FR-4. Session Reuse Scenarios
The harness must support testing one or more real session states provided by the operator.

It must support:
- a single reused session,
- multiple independent session jars,
- optional session refresh/bootstrap hooks if explicitly configured.

### FR-5. Solver Strategy Abstraction
The harness must support multiple solver strategies behind a common interface.

At minimum:
- a baseline single-threaded Python solver,
- an optional multithreaded local solver strategy,
- configurable worker count,
- metrics per solver strategy.

### FR-6. Concurrency Scenarios
The harness must support scenarios that test:
- parallel challenge fetching,
- parallel proof submission,
- session fan-out across local workers,
- tier-boundary pressure,
- expiry-edge timing,
- outstanding-challenge cap behavior.

### FR-7. Throughput Measurement
The harness must measure:
- challenge acquisition rate,
- solve time per stage and per request,
- success rate,
- rejection rate by error code,
- sustained throughput over time,
- throughput degradation as tier rises.

### FR-8. Failure Classification
The harness must classify server responses into meaningful buckets.

At minimum:
- success,
- session required/invalid,
- challenge rate limited by IP,
- challenge rate limited by session,
- too many outstanding challenges,
- stale challenge difficulty,
- challenge expired,
- challenge already consumed,
- request binding mismatch,
- invalid proof,
- transport/network failure.

### FR-9. Repeatable Scenario Definitions
The harness must allow scenarios to be expressed declaratively or via structured configuration.

At minimum, a scenario must define:
- target base URL,
- session source,
- request count/shape,
- duration or iteration count,
- concurrency level,
- solver strategy,
- pacing strategy.

### FR-10. Safety Guardrails
The harness must include explicit safety controls.

At minimum:
- target allowlist enforcement,
- max request cap per run,
- max duration cap per run,
- explicit acknowledgment or flag for “high-pressure” modes,
- clear labeling that the tool is for authorized defensive evaluation only.

### FR-11. Reporting
The harness must produce machine-readable and human-readable results.

At minimum:
- structured JSON run output,
- summary table or markdown report,
- top error reasons,
- observed throughput,
- observed solve-cost trends,
- notes on whether protections raised cost as expected.

### FR-12. Session Input Model
The harness must support operator-provided session material in a safe, explicit way.

Examples:
- cookie jar file,
- raw cookie header input,
- exported browser session file,
- bootstrap callback that acquires an authorized session through an approved path.

### FR-13. No Credential Acquisition Features
The harness must not implement credential theft or unauthorized session extraction logic.

If session material is required, it must be provided by the operator or obtained through an explicitly approved bootstrap path against an allowed target.

### FR-14. Extensibility
The harness design must allow future scenarios for:
- multiple session pools,
- variable value-per-request modeling,
- different PoW endpoint contracts,
- alternate protected resources.

## 5. Non-Functional Requirements

### NFR-1. Clarity
The harness should be understandable and auditable by engineers reviewing defensive test tooling.

### NFR-2. Containment
The tool should make misuse harder by default through clear guardrails and configuration friction.

### NFR-3. Deterministic Reporting
Given the same scenario inputs and enough environmental stability, the harness should produce comparable metrics across runs.

### NFR-4. Maintainability
The codebase should follow the workspace preferences:
- Python,
- maintainable OOP-oriented structure,
- one class per file where practical.

## 6. Acceptance Criteria

The spec is acceptable when it clearly defines:
1. how the harness tests direct API abuse against authorized targets,
2. how session reuse is supplied and controlled,
3. how concurrency and solver strategies are modeled,
4. what guardrails prevent accidental misuse,
5. what metrics/reports determine whether the protections are working.
