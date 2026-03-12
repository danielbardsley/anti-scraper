# Adversarial Evaluation Harness — Design

## 1. Overview

This tool is a controlled defensive evaluation harness for testing the economics and robustness of the anti-scraping proof-of-work design.

It is not intended to “break in” to third-party services. It is intended to answer questions like:
- How much throughput can a direct API client achieve after session bootstrap?
- How much does throughput fall as tier rises?
- How much value does a stolen or reused session still have under PoW?
- Do rate limits and outstanding-challenge controls work under concurrency?
- What does an attacker gain by replacing the browser solver with a local Python solver?

## 2. Proposed Architecture

## 2.1 Top-Level Components

Recommended components:
- `HarnessApp`
- `RunController`
- `TargetPolicy`
- `ScenarioDefinition`
- `SessionProvider`
- `ChallengeClient`
- `ProtectedEndpointClient`
- `PowSolver`
- `WorkerPoolCoordinator`
- `MetricsCollector`
- `ReportWriter`

## 2.2 Responsibility Split

### HarnessApp
- entry point
- loads config
- validates target allowlist
- dispatches scenario execution

### RunController
- creates one run context
- coordinates sessions, workers, metrics, and stop conditions

### TargetPolicy
- enforces allowlist and run guardrails
- blocks execution against non-approved targets

### SessionProvider
- loads or refreshes operator-approved session material
- provides session jars to workers

### ChallengeClient
- fetches challenges from the target API
- records issuance outcomes and errors

### ProtectedEndpointClient
- submits proofs to the target protected endpoint
- classifies responses

### PowSolver
- solves the current target’s challenge format
- exposes timing metrics
- supports multiple execution strategies

### WorkerPoolCoordinator
- manages local worker threads
- coordinates challenge->solve->submit pipelines

### MetricsCollector
- captures challenge counts, solve times, success rates, error reasons, throughput, tier progression

### ReportWriter
- emits JSON/Markdown summaries

## 3. Data Flow

### 3.1 Basic direct-client scenario
1. Load target config.
2. Validate target against allowlist.
3. Load one authorized session.
4. Request challenge directly from target.
5. Solve challenge locally.
6. Submit proof directly to protected endpoint.
7. Record outcome and timings.
8. Repeat until duration or iteration cap is reached.

### 3.2 Session fan-out scenario
1. Load one authorized session jar.
2. Share it across multiple local workers.
3. Run parallel challenge/solve/submit loops.
4. Measure:
   - challenge issuance rejections,
   - stale challenges,
   - outstanding challenge rejections,
   - throughput decay as tier rises.

### 3.3 Multi-session pool scenario
1. Load multiple operator-approved session jars.
2. Assign workers to session pool entries.
3. Compare throughput and effective cost when abuse is spread across sessions.

## 4. Target Configuration Model

Suggested target config:

```json
{
  "name": "anti-scraper-demo",
  "baseUrl": "https://example.ts.net",
  "allowed": true,
  "challengeEndpoint": "/v1/pow/challenges",
  "protectedEndpoint": "/v1/random-numbers",
  "challengeRequestTemplate": {
    "resource": "random-numbers",
    "count": 10
  },
  "protectedRequestTemplate": {
    "count": 10
  },
  "sessionCookieName": "pow_session"
}
```

TargetPolicy must refuse execution unless the target is explicitly listed.

## 5. Session Input Model

Supported session sources should include:
- cookie jar JSON file,
- raw cookie header provided via environment variable or secure input,
- pluggable bootstrap adapter.

The tool must not automatically steal or scrape browser credentials.

Recommended session file example:

```json
{
  "cookieName": "pow_session",
  "cookieValue": "opaque-session-token",
  "baseUrl": "https://example.ts.net"
}
```

## 6. Solver Design

## 6.1 Common interface
Expose a common solver interface such as:

```text
solve(challenge) -> proof, metrics
```

Where metrics include:
- total solve duration,
- per-stage durations,
- hashes attempted (if measured),
- worker count.

## 6.2 Strategies

### Baseline strategy
- pure Python
- single thread
- used as the baseline measurement

### Threaded strategy
- single host
- local worker threads
- useful for measuring whether extra local parallelism materially improves solve throughput

### Optional optimized strategy
If added later, still keep it local and authorized. Examples could include multiprocessing or native extensions, but that is outside the initial phase.

## 7. Scenario Types

Recommended initial scenarios:

### Scenario A — single-session baseline
- one session
- one worker
- fixed request shape
- measure baseline throughput and cost

### Scenario B — single-session multithreaded fan-out
- one session
- N workers
- measure how well protections degrade parallel direct API abuse

### Scenario C — outstanding-challenge cap pressure
- one session
- request challenges faster than they can be solved/submitted
- verify cap behavior and rejection patterns

### Scenario D — stale challenge spend attempt
- intentionally hold older low-tier challenges
- continue successful requests to raise tier
- attempt later submission
- verify rejection of stale lower-tier work

### Scenario E — expiry-edge timing
- intentionally submit near challenge expiry
- measure stability and error classification

### Scenario F — multi-session pool comparison
- multiple operator-provided sessions
- compare cost/throughput versus one-session fan-out

## 8. Metrics Model

The collector should record at least:
- run metadata
- target metadata
- scenario name
- solver strategy
- worker count
- total challenges requested
- total proofs submitted
- total successes
- successes per minute
- median/95th solve time
- median/95th request latency
- tier distribution of successful submissions
- server error counts by code
- transport failure count
- effective success-per-CPU-time ratio if measurable

## 9. Reporting

### 9.1 JSON output
Recommended path:
- `artifacts/reports/<timestamp>-<scenario>.json`

### 9.2 Markdown summary
Recommended path:
- `artifacts/reports/<timestamp>-<scenario>.md`

Suggested summary sections:
- Scenario
- Target
- Session source
- Worker configuration
- Success/failure counts
- Throughput trend
- Tier escalation observations
- Top failure reasons
- Interpretation

## 10. Guardrails

The tool should refuse or require explicit override when:
- the host is not on an allowlist,
- the run exceeds configured request caps,
- concurrency exceeds configured local limits,
- no authorized session source is configured,
- the operator has not acknowledged authorized testing mode.

Recommended flags:
- `--target <name>`
- `--scenario <name>`
- `--session-file <path>`
- `--max-requests <n>`
- `--duration-seconds <n>`
- `--workers <n>`
- `--ack-authorized-test`

## 11. Code Organization

To match workspace preferences, a possible Python layout is:

```text
src/adversarial_harness/
  app/
  config/
  models/
  clients/
  solvers/
  scenarios/
  metrics/
  reports/
```

Prefer one class per file where practical.

## 12. Testing Strategy

The harness itself should include tests for:
- target allowlist enforcement,
- session-file parsing,
- solver correctness against known challenge vectors,
- response classification,
- metrics aggregation,
- scenario stop conditions,
- refusal to run without explicit authorization flags.

## 13. Deliverable Value

A good outcome from this harness is not “we bypassed everything.”
A good outcome is:
- we measured abuse cost realistically,
- we found where protections bend or break,
- we identified the throughput ceiling under direct API use,
- we learned which controls matter most before production investment.
